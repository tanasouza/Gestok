import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse

from accounts.mixins import CaixaOrAdminRequiredMixin
from cashier.models import CashRegister
from cashier.services import cash_register_summary
from core.date_filters import filter_by_local_date_range, local_day_bounds
from sales.models import Sale, SaleItem
from products.models import Product, InventoryMovement

User = get_user_model()


def parse_money(value):
    normalized = str(value or '0').strip().replace(',', '.')
    try:
        amount = Decimal(normalized)
    except (InvalidOperation, ValueError):
        raise ValueError('Valor monetário inválido.')

    if amount < 0:
        raise ValueError('O valor não pode ser negativo.')
    return amount.quantize(Decimal('0.01'))


class PDVView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    """
    Main view for the POS.
    Handles the daily opening, pending closure and active POS states.
    """
    def get(self, request, *args, **kwargs):
        today = timezone.localdate()
        day_start, day_end = local_day_bounds(today)
        open_registers = CashRegister.objects.filter(
            operador=request.user,
            status='ABERTO'
        ).order_by('data_abertura')
        current_register = open_registers.filter(
            data_abertura__gte=day_start,
            data_abertura__lt=day_end,
        ).first()
        stale_register = open_registers.exclude(
            data_abertura__gte=day_start,
            data_abertura__lt=day_end,
        ).first()

        context = {
            'caixa': current_register or stale_register,
            'estado': 'sem_caixa'
        }

        closed_id = request.GET.get('fechado')
        if closed_id:
            context['ultimo_caixa_fechado'] = CashRegister.objects.filter(
                id=closed_id,
                operador=request.user,
                status='FECHADO',
            ).first()

        if stale_register:
            context['estado'] = 'caixa_pendente'
            context['resumo_caixa'] = cash_register_summary(stale_register)
        elif current_register:
            venda_aberta = Sale.objects.filter(
                caixa=current_register,
                status='ABERTA'
            ).first()
            if not venda_aberta:
                venda_aberta = Sale.objects.create(
                    vendedor=request.user,
                    caixa=current_register,
                    caixa_responsavel=request.user,
                    status='ABERTA'
                )

            context['estado'] = 'venda_em_andamento'
            context['venda'] = venda_aberta
            context['produtos'] = Product.objects.filter(ativo=True).order_by('nome')
            context['resumo_caixa'] = cash_register_summary(current_register)

        return render(request, 'cashier/pdv.html', context)


class AbrirCaixaView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            valor_abertura = parse_money(request.POST.get('valor_abertura', '0'))
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('cashier:pdv')

        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            existing_register = CashRegister.objects.filter(
                operador=request.user,
                status='ABERTO',
            ).order_by('data_abertura').first()

            if existing_register:
                if timezone.localdate(existing_register.data_abertura) == timezone.localdate():
                    messages.info(request, "Seu caixa de hoje já está aberto.")
                else:
                    messages.error(
                        request,
                        "Existe um caixa de outro dia aguardando fechamento."
                    )
                return redirect('cashier:pdv')

            CashRegister.objects.create(
                operador=request.user,
                valor_abertura=valor_abertura,
                status='ABERTO'
            )

        messages.success(request, "Caixa aberto com sucesso!")
        return redirect('cashier:pdv')


class FecharCaixaView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            valor_fechamento = parse_money(
                request.POST.get('valor_fechamento', '0')
            )
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('cashier:pdv')

        observacao = request.POST.get('observacao', '').strip()

        with transaction.atomic():
            caixa = get_object_or_404(
                CashRegister.objects.select_for_update(),
                id=request.POST.get('caixa_id'),
                operador=request.user,
                status='ABERTO',
            )

            vendas_abertas = Sale.objects.filter(caixa=caixa, status='ABERTA')
            if SaleItem.objects.filter(venda__in=vendas_abertas).exists():
                messages.error(request, "Não é possível fechar o caixa. Conclua ou cancele a venda em andamento.")
                return redirect('cashier:pdv')

            vendas_abertas.delete()
            summary = cash_register_summary(caixa)

            caixa.status = 'FECHADO'
            caixa.data_fechamento = timezone.now()
            caixa.valor_fechamento = valor_fechamento
            caixa.valor_esperado = summary['expected_cash']
            caixa.diferenca_fechamento = (
                valor_fechamento - summary['expected_cash']
            )
            caixa.observacao_fechamento = observacao
            caixa.save(update_fields=[
                'status',
                'data_fechamento',
                'valor_fechamento',
                'valor_esperado',
                'diferenca_fechamento',
                'observacao_fechamento',
            ])

        messages.success(request, "Caixa fechado com sucesso!")
        return redirect(f"{reverse('cashier:pdv')}?fechado={caixa.id}")


class CashClosingHistoryView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, ListView):
    model = CashRegister
    template_name = 'cashier/closing_history.html'
    context_object_name = 'cash_registers'
    paginate_by = 10

    def get_queryset(self):
        queryset = CashRegister.objects.filter(
            status='FECHADO'
        ).select_related('operador').order_by('-data_fechamento')

        if not self.request.user.eh_administrador:
            queryset = queryset.filter(operador=self.request.user)

        operator_id = self.request.GET.get('operador', '').strip()
        if operator_id and self.request.user.eh_administrador:
            queryset = queryset.filter(operador_id=operator_id)

        return filter_by_local_date_range(
            queryset,
            'data_fechamento',
            self.request.GET.get('data_inicio', ''),
            self.request.GET.get('data_fim', ''),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data_inicio'] = self.request.GET.get('data_inicio', '')
        context['data_fim'] = self.request.GET.get('data_fim', '')
        context['operador_filter'] = self.request.GET.get('operador', '')
        if self.request.user.eh_administrador:
            context['operadores'] = User.objects.filter(
                cargo__in=User.CARGOS_ADMINISTRATIVOS | User.CARGOS_CAIXA,
                ativo=True,
            ).order_by('nome_completo')
        return context



class AdicionarItemView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            venda_id = data.get('venda_id')
            produto_id = data.get('produto_id')
            quantidade = int(data.get('quantidade', 1))

            venda = get_object_or_404(Sale, id=venda_id, status='ABERTA', caixa__operador=request.user)
            produto = get_object_or_404(Product, id=produto_id, ativo=True)

            if quantidade <= 0:
                return JsonResponse({'success': False, 'message': 'Quantidade deve ser maior que zero.'})

            if produto.estoque_atual < quantidade:
                return JsonResponse({'success': False, 'message': f'Estoque insuficiente. Disponível: {produto.estoque_atual}'})

            # Check if item already exists in sale
            item, created = SaleItem.objects.get_or_create(
                venda=venda,
                produto=produto,
                defaults={'quantidade': quantidade, 'preco_unitario': produto.preco_venda, 'subtotal': produto.preco_venda * quantidade}
            )

            if not created:
                if produto.estoque_atual < (item.quantidade + quantidade):
                    return JsonResponse({'success': False, 'message': f'Estoque insuficiente. Disponível: {produto.estoque_atual}'})

                item.quantidade += quantidade
                item.save() # will recalculate subtotal and sale total in model save method

            venda.refresh_from_db()

            return JsonResponse({
                'success': True,
                'item_id': item.id,
                'produto_nome': produto.nome,
                'quantidade': item.quantidade,
                'preco_unitario': float(item.preco_unitario),
                'subtotal': float(item.subtotal),
                'venda_total': float(venda.valor_total)
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class RemoverItemView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    def post(self, request, item_id, *args, **kwargs):
        item = get_object_or_404(SaleItem, id=item_id, venda__status='ABERTA', venda__caixa__operador=request.user)
        venda = item.venda
        item.delete() # Recalculates total in model delete method
        venda.refresh_from_db()

        return JsonResponse({
            'success': True,
            'venda_total': float(venda.valor_total)
        })


class AtualizarItemQuantidadeView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    def post(self, request, item_id, *args, **kwargs):
        try:
            data = json.loads(request.body or '{}')
            delta = int(data.get('delta', 0))
        except (TypeError, ValueError, json.JSONDecodeError):
            return JsonResponse({'success': False, 'message': 'Quantidade invÃ¡lida.'})

        if delta == 0:
            return JsonResponse({'success': False, 'message': 'Nenhuma alteraÃ§Ã£o informada.'})

        item = get_object_or_404(
            SaleItem,
            id=item_id,
            venda__status='ABERTA',
            venda__caixa__operador=request.user
        )
        venda = item.venda
        nova_quantidade = item.quantidade + delta

        if nova_quantidade <= 0:
            item.delete()
            venda.refresh_from_db()
            return JsonResponse({
                'success': True,
                'removed': True,
                'venda_total': float(venda.valor_total)
            })

        if delta > 0 and item.produto.estoque_atual < nova_quantidade:
            return JsonResponse({
                'success': False,
                'message': f'Estoque insuficiente. DisponÃ­vel: {item.produto.estoque_atual}'
            })

        item.quantidade = nova_quantidade
        item.save()
        venda.refresh_from_db()

        return JsonResponse({
            'success': True,
            'removed': False,
            'quantidade': item.quantidade,
            'subtotal': float(item.subtotal),
            'venda_total': float(venda.valor_total)
        })


class FinalizarVendaView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        venda_id = request.POST.get('venda_id')
        venda = get_object_or_404(Sale, id=venda_id, status='ABERTA', caixa__operador=request.user)
        forma_pagamento = request.POST.get('forma_pagamento')

        if not forma_pagamento:
            messages.error(request, "Por favor, selecione uma forma de pagamento.")
            return redirect('cashier:pdv')

        if not venda.itens.exists():
            messages.error(request, "Não é possível finalizar uma venda sem itens.")
            return redirect('cashier:pdv')

        try:
            with transaction.atomic():
                for item in venda.itens.all():
                    produto = item.produto

                    if produto.estoque_atual < item.quantidade:
                        raise ValueError(f"Estoque insuficiente para '{produto.nome}'. Disponível: {produto.estoque_atual}")

                    estoque_anterior = produto.estoque_atual
                    produto.estoque_atual -= item.quantidade
                    produto.save()

                    InventoryMovement.objects.create(
                        produto=produto,
                        tipo='VENDA',
                        quantidade=item.quantidade,
                        estoque_anterior=estoque_anterior,
                        estoque_posterior=produto.estoque_atual,
                        usuario=request.user,
                        observacao=f"Venda {venda.numero_venda}"
                    )

                venda.status = 'FINALIZADA'
                venda.data_finalizacao = timezone.now()
                venda.forma_pagamento = forma_pagamento
                venda.save()

            messages.success(request, f"Venda {venda.numero_venda} finalizada com sucesso! ({venda.get_forma_pagamento_display()})")

        except ValueError as ve:
            messages.error(request, str(ve))
        except Exception as e:
            messages.error(request, f"Erro inesperado: {str(e)}")

        return redirect('cashier:pdv')


class CancelarVendaView(LoginRequiredMixin, CaixaOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        venda_id = request.POST.get('venda_id')
        venda = get_object_or_404(Sale, id=venda_id, status='ABERTA', caixa__operador=request.user)

        # Deleting the sale, no stock was deducted yet because it's ABERTA
        venda.delete()
        messages.success(request, "Venda cancelada.")
        return redirect('cashier:pdv')
