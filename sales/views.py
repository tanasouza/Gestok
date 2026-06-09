from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse

from accounts.mixins import AdminRequiredMixin, VendasOrAdminRequiredMixin
from core.date_filters import filter_by_local_date_range
from core.pdf_reports import build_sales_pdf
from sales.models import Sale, SaleItem
from products.models import Product, InventoryMovement


def filtered_sales(request):
    queryset = Sale.objects.select_related(
        'vendedor', 'caixa_responsavel'
    ).annotate(item_count=Count('itens')).order_by('-data_venda')

    if not request.user.eh_administrador:
        queryset = queryset.filter(vendedor=request.user)

    status_filter = request.GET.get('status', '')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    queryset = filter_by_local_date_range(
        queryset,
        'data_venda',
        request.GET.get('data_inicio', ''),
        request.GET.get('data_fim', '')
    )

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(numero_venda__icontains=search) |
            Q(vendedor__nome_completo__icontains=search) |
            Q(vendedor__matricula__icontains=search)
        )

    return queryset


class MySalesListView(VendasOrAdminRequiredMixin, ListView):
    """
    CBV to list sales.
    - Sellers see only their own sales.
    - Admins see all sales in the system.
    """
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 10

    def get_queryset(self):
        return filtered_sales(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['data_inicio'] = self.request.GET.get('data_inicio', '')
        context['data_fim'] = self.request.GET.get('data_fim', '')
        context['status_choices'] = Sale.STATUS_CHOICES
        return context


class SalesPDFView(VendasOrAdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        status_filter = request.GET.get('status', '')
        filters = [
            ('Busca', request.GET.get('search', '')),
            ('Status', dict(Sale.STATUS_CHOICES).get(status_filter, '')),
            ('Data inicial', request.GET.get('data_inicio', '')),
            ('Data final', request.GET.get('data_fim', '')),
        ]
        pdf = build_sales_pdf(
            filtered_sales(request),
            request.user.nome_completo or request.user.matricula,
            filters,
        )
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="relatorio_vendas.pdf"'
        )
        return response


class SaleDetailView(VendasOrAdminRequiredMixin, DetailView):
    """CBV to view the full details of a specific sale."""
    model = Sale
    context_object_name = 'sale'

    def get_template_names(self):
        if self.request.GET.get('partial') == 'true':
            return ['sales/sale_detail_partial.html']
        return ['sales/sale_detail.html']

    def get_queryset(self):
        queryset = Sale.objects.prefetch_related('itens__produto')
        # Standard users can only view their own sales
        if not self.request.user.eh_administrador:
            queryset = queryset.filter(vendedor=self.request.user)
        return queryset


class SaleRefundView(AdminRequiredMixin, View):
    """
    CBV to process a sale refund (estorno).
    Only ADMINISTRADOR can perform refunds.
    Restores inventory levels and logs movement type ESTORNO.
    """
    def post(self, request, pk, *args, **kwargs):
        sale = get_object_or_404(Sale, pk=pk)

        if sale.status != 'FINALIZADA':
            messages.error(request, f"Apenas vendas FINALIZADAS podem ser estornadas. Status atual: {sale.status}.")
            return redirect('sales:sale_detail', pk=pk)

        if sale.estornada:
            messages.error(request, "Esta venda já foi estornada anteriormente.")
            return redirect('sales:sale_detail', pk=pk)

        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, "O motivo do estorno é obrigatório.")
            return redirect('sales:sale_detail', pk=pk)

        try:
            with transaction.atomic():
                # Loop items to revert stock
                for item in sale.itens.all():
                    produto = item.produto
                    estoque_anterior = produto.estoque_atual
                    produto.estoque_atual += item.quantidade
                    produto.save()

                    # Create stock movement log
                    InventoryMovement.objects.create(
                        produto=produto,
                        tipo='ESTORNO',
                        quantidade=item.quantidade,
                        estoque_anterior=estoque_anterior,
                        estoque_posterior=produto.estoque_atual,
                        usuario=request.user,
                        observacao=f"Estorno da venda {sale.numero_venda}. Motivo: {motivo}"
                    )

                # Update sale status
                sale.status = 'ESTORNADA'
                sale.estornada = True
                sale.save()

            messages.success(request, f"Venda {sale.numero_venda} estornada com sucesso! Estoque devolvido.")
        except Exception as e:
            messages.error(request, f"Erro ao realizar o estorno da venda: {str(e)}")

        return redirect('sales:sale_detail', pk=pk)
