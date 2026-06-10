import csv
import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Q, Sum
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from accounts.mixins import AdminRequiredMixin, CaixaOrAdminRequiredMixin
from cashier.models import CashRegister
from core.date_filters import (
    filter_by_local_date_range,
    local_day_bounds,
    parse_filter_date,
)
from core.pdf_reports import build_cash_closing_pdf
from products.models import Category, Product
from sales.models import Sale, SaleItem

User = get_user_model()


def finalized_sales_between(start_date, end_date):
    start, _ = local_day_bounds(start_date)
    _, end = local_day_bounds(end_date)
    return Sale.objects.filter(status='FINALIZADA').filter(
        Q(data_finalizacao__gte=start, data_finalizacao__lt=end)
        | Q(
            data_finalizacao__isnull=True,
            data_venda__gte=start,
            data_venda__lt=end,
        )
    )


def month_bounds(year, month):
    start = date(year, month, 1)
    if month == 12:
        return start, date(year + 1, 1, 1) - timedelta(days=1)
    return start, date(year, month + 1, 1) - timedelta(days=1)


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localtime(timezone.now()).date()

        active_products = Product.objects.filter(ativo=True).select_related('categoria')
        month_start, month_end = month_bounds(today.year, today.month)
        vendas_hoje = finalized_sales_between(today, today)
        vendas_mes = finalized_sales_between(month_start, month_end)
        itens_mes = SaleItem.objects.filter(
            venda__in=vendas_mes,
        ).select_related('produto', 'produto__categoria')

        context['total_produtos'] = active_products.count()
        context['estoque_critico'] = active_products.filter(estoque_atual__lte=F('estoque_minimo')).count()
        context['estoque_zerado'] = active_products.filter(estoque_atual=0).count()
        context['vendas_hoje_qtd'] = vendas_hoje.count()
        context['faturamento_hoje'] = vendas_hoje.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        context['vendas_mes_qtd'] = vendas_mes.count()
        context['faturamento_mes'] = vendas_mes.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        context['ticket_medio_mes'] = context['faturamento_mes'] / context['vendas_mes_qtd'] if context['vendas_mes_qtd'] else Decimal('0.00')

        lucro_mes = sum((item.subtotal - (item.produto.preco_custo * item.quantidade)) for item in itens_mes)
        context['margem_lucro_mes'] = (lucro_mes / context['faturamento_mes'] * 100) if context['faturamento_mes'] else Decimal('0.00')
        context['valor_estoque'] = sum((produto.preco_custo * max(produto.estoque_atual, 0)) for produto in active_products)

        estoque_critico_real = max(context['estoque_critico'] - context['estoque_zerado'], 0)
        estoque_normal = max(context['total_produtos'] - context['estoque_critico'], 0)
        context['chart_estoque'] = json.dumps([estoque_normal, estoque_critico_real, context['estoque_zerado']])

        pay_totals = vendas_mes.values('forma_pagamento').annotate(total=Sum('valor_total'))
        pay_dict = {item['forma_pagamento']: float(item['total'] or 0) for item in pay_totals}
        pay_keys = ['PIX', 'CARTAO', 'DINHEIRO', 'OUTROS']
        context['chart_pagamentos_labels'] = json.dumps(
            ['Pix', 'Cartão', 'Dinheiro', 'Outros']
        )
        context['chart_pagamentos_data'] = json.dumps([pay_dict.get(key, 0.0) for key in pay_keys])

        top_produtos = itens_mes.values('produto__nome').annotate(qtd=Sum('quantidade')).order_by('-qtd')[:5]
        context['chart_top_produtos_labels'] = json.dumps([p['produto__nome'] for p in top_produtos])
        context['chart_top_produtos_data'] = json.dumps([p['qtd'] for p in top_produtos])

        dias_labels = []
        dias_data = []
        for i in range(6, -1, -1):
            dia = today - timedelta(days=i)
            dias_labels.append(dia.strftime('%d/%m'))
            total_dia = finalized_sales_between(dia, dia).aggregate(
                total=Sum('valor_total')
            )['total'] or Decimal('0.00')
            dias_data.append(float(total_dia))
        context['chart_7d_labels'] = json.dumps(dias_labels)
        context['chart_7d_data'] = json.dumps(dias_data)

        categorias_estoque = Category.objects.filter(ativo=True).annotate(
            total=Count('produtos', filter=Q(produtos__ativo=True))
        ).order_by('-total', 'nome')[:5]
        total_categoria_estoque = sum(cat.total for cat in categorias_estoque) or 1
        context['categorias_estoque'] = [
            {'nome': cat.nome, 'total': cat.total, 'percentual': round((cat.total / total_categoria_estoque) * 100)}
            for cat in categorias_estoque
        ]
        context['chart_categorias_estoque_labels'] = json.dumps([cat['nome'] for cat in context['categorias_estoque']])
        context['chart_categorias_estoque_data'] = json.dumps([cat['total'] for cat in context['categorias_estoque']])

        categorias_vendas = itens_mes.values('produto__categoria__nome').annotate(qtd=Sum('quantidade')).order_by('-qtd')[:5]
        total_categoria_vendas = sum(item['qtd'] or 0 for item in categorias_vendas) or 1
        context['categorias_vendas'] = [
            {
                'nome': item['produto__categoria__nome'] or 'Sem categoria',
                'total': item['qtd'] or 0,
                'percentual': round(((item['qtd'] or 0) / total_categoria_vendas) * 100),
            }
            for item in categorias_vendas
        ]
        context['chart_categorias_vendas_labels'] = json.dumps([cat['nome'] for cat in context['categorias_vendas']])
        context['chart_categorias_vendas_data'] = json.dumps([cat['total'] for cat in context['categorias_vendas']])

        context['produtos_criticos'] = active_products.filter(
            estoque_atual__lte=F('estoque_minimo')
        ).order_by('estoque_atual', 'nome')[:6]
        context['ultimas_vendas'] = Sale.objects.filter(status='FINALIZADA').select_related(
            'vendedor'
        ).annotate(itens_count=Count('itens')).order_by('-data_venda')[:6]

        ano = int(self.request.GET.get('ano', today.year))
        valores_ano = []
        for mes in range(1, 13):
            selected_start, selected_end = month_bounds(ano, mes)
            total_mes = finalized_sales_between(
                selected_start,
                selected_end,
            ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
            valores_ano.append(float(total_mes))
        context['ano_selecionado'] = ano
        context['anos_disponiveis'] = range(today.year - 5, today.year + 1)
        context['chart_anuais_data'] = json.dumps(valores_ano)

        if user.perfil_operacional == 'CAIXA':
            context['vendas_abertas'] = Sale.objects.filter(caixa__operador=user, status='ABERTA').count()
            minhas_finalizadas = Sale.objects.filter(data_venda__date=today, status='FINALIZADA', caixa__operador=user)
            context['minhas_finalizadas_qtd'] = minhas_finalizadas.count()
            context['meu_faturamento'] = minhas_finalizadas.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')

        elif user.perfil_operacional == 'VENDAS':
            minhas_abertas = Sale.objects.filter(data_venda__date=today, status='ABERTA', vendedor=user)
            context['minhas_abertas'] = minhas_abertas
            context['minhas_abertas_qtd'] = minhas_abertas.count()

        return context


class FechamentoCaixaView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'reports/fechamento_caixa.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        data_filter = self.request.GET.get('data', timezone.localtime(timezone.now()).strftime('%Y-%m-%d'))
        caixa_filter = self.request.GET.get('caixa', '')

        vendas = filter_by_local_date_range(
            Sale.objects.all(),
            'data_venda',
            data_filter,
            data_filter,
        )

        if caixa_filter:
            vendas = vendas.filter(caixa_responsavel_id=caixa_filter)

        finalizadas = vendas.filter(status='FINALIZADA')
        estornadas = vendas.filter(status='ESTORNADA')

        context['faturamento_total'] = finalizadas.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        context['vendas_finalizadas_qtd'] = finalizadas.count()
        context['vendas_estornadas_qtd'] = estornadas.count()

        context['total_dinheiro'] = finalizadas.filter(forma_pagamento='DINHEIRO').aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        context['total_pix'] = finalizadas.filter(forma_pagamento='PIX').aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        context['total_cartao'] = finalizadas.filter(forma_pagamento='CARTAO').aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')

        context['data_filter'] = data_filter
        context['caixa_filter'] = caixa_filter
        context['caixas'] = User.objects.filter(
            Q(is_superuser=True) |
            Q(cargo__in=User.CARGOS_ADMINISTRATIVOS | User.CARGOS_CAIXA)
        )

        return context


class FechamentoCaixaCSVView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        data_filter = request.GET.get('data', timezone.localtime(timezone.now()).strftime('%Y-%m-%d'))
        caixa_filter = request.GET.get('caixa', '')

        vendas = filter_by_local_date_range(
            Sale.objects.all(),
            'data_venda',
            data_filter,
            data_filter,
        )
        if caixa_filter:
            vendas = vendas.filter(caixa_responsavel_id=caixa_filter)

        finalizadas = vendas.filter(status='FINALIZADA')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="fechamento_caixa_{data_filter}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Numero Venda', 'Data', 'Vendedor', 'Caixa', 'Forma Pagamento', 'Valor Total'])

        for venda in finalizadas:
            caixa_nome = ''
            if venda.caixa_responsavel:
                caixa_nome = venda.caixa_responsavel.nome_completo or venda.caixa_responsavel.matricula
            writer.writerow([
                venda.numero_venda,
                timezone.localtime(venda.data_finalizacao).strftime('%d/%m/%Y %H:%M') if venda.data_finalizacao else '',
                venda.vendedor.nome_completo or venda.vendedor.matricula,
                caixa_nome,
                {'DINHEIRO': 'Dinheiro', 'PIX': 'Pix', 'CARTAO': 'Cartão'}.get(venda.forma_pagamento, ''),
                f'{venda.valor_total:.2f}',
            ])

        return response


class FechamentoCaixaPDFView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        register_id = request.GET.get('registro', '').strip()
        selected_operator = (
            request.GET.get('operador', '').strip()
            or request.GET.get('caixa', '').strip()
        )
        selected_date = parse_filter_date(request.GET.get('data', ''))
        start_date = parse_filter_date(request.GET.get('data_inicio', ''))
        end_date = parse_filter_date(request.GET.get('data_fim', ''))

        registers = CashRegister.objects.select_related('operador').prefetch_related(
            'vendas__vendedor',
            'vendas__caixa_responsavel',
        )

        if not request.user.eh_administrador:
            registers = registers.filter(operador=request.user)

        if register_id:
            registers = registers.filter(id=register_id, status='FECHADO')
            cash_register = registers.first()
            if cash_register is None:
                raise Http404('Fechamento de caixa não encontrado.')
            registers = [cash_register]
            period_label = (
                f"Caixa #{cash_register.id} - "
                f"{timezone.localtime(cash_register.data_abertura).strftime('%d/%m/%Y')}"
            )
            filename_suffix = f"caixa_{cash_register.id}"
        else:
            registers = registers.filter(status='FECHADO')
            if selected_date:
                start_date = selected_date
                end_date = selected_date
            registers = filter_by_local_date_range(
                registers,
                'data_fechamento',
                start_date.isoformat() if start_date else '',
                end_date.isoformat() if end_date else '',
            ).order_by('data_fechamento')
            if selected_operator and request.user.eh_administrador:
                registers = registers.filter(operador_id=selected_operator)
            if start_date and end_date:
                period_label = (
                    f"{start_date.strftime('%d/%m/%Y')} a "
                    f"{end_date.strftime('%d/%m/%Y')}"
                )
                filename_suffix = (
                    f"{start_date.strftime('%Y-%m-%d')}_"
                    f"{end_date.strftime('%Y-%m-%d')}"
                )
            elif start_date:
                period_label = f"A partir de {start_date.strftime('%d/%m/%Y')}"
                filename_suffix = f"desde_{start_date.strftime('%Y-%m-%d')}"
            elif end_date:
                period_label = f"Até {end_date.strftime('%d/%m/%Y')}"
                filename_suffix = f"ate_{end_date.strftime('%Y-%m-%d')}"
            else:
                period_label = 'Todos os fechamentos'
                filename_suffix = 'todos'

        pdf = build_cash_closing_pdf(
            registers,
            request.user.nome_completo or request.user.matricula,
            period_label,
        )
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="fechamento_caixa_{filename_suffix}.pdf"'
        )
        return response
