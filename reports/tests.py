import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cashier.models import CashRegister
from products.models import Category, Product
from sales.models import Sale, SaleItem

User = get_user_model()


class SalesDashboardTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_superuser(
            matricula='1000',
            nome_completo='Gestor Teste',
            password='senha123',
        )
        self.category = Category.objects.create(nome='Bebidas')
        self.product = Product.objects.create(
            nome='Suco',
            categoria=self.category,
            preco_custo=Decimal('4.00'),
            preco_venda=Decimal('10.00'),
            estoque_atual=20,
        )
        self.client.login(username='1000', password='senha123')

    def create_sale(self, payment, total, opened_at, finalized_at):
        sale = Sale.objects.create(
            vendedor=self.manager,
            status='FINALIZADA',
            forma_pagamento=payment,
            data_venda=opened_at,
            data_finalizacao=finalized_at,
        )
        SaleItem.objects.create(
            venda=sale,
            produto=self.product,
            quantidade=1,
            preco_unitario=Decimal(total),
        )
        return sale

    def test_sales_kpis_use_finalization_date(self):
        now = timezone.localtime()
        yesterday = now - timedelta(days=1)
        self.create_sale('PIX', '10.00', yesterday, now)

        response = self.client.get(reverse('reports:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['vendas_hoje_qtd'], 1)
        self.assertEqual(response.context['faturamento_hoje'], Decimal('10.00'))
        self.assertEqual(response.context['vendas_mes_qtd'], 1)

    def test_payment_chart_includes_all_supported_methods(self):
        now = timezone.localtime()
        for payment, total in (
            ('PIX', '10.00'),
            ('CARTAO', '20.00'),
            ('DINHEIRO', '30.00'),
            ('OUTROS', '40.00'),
        ):
            self.create_sale(payment, total, now, now)

        response = self.client.get(reverse('reports:dashboard'))

        labels = json.loads(response.context['chart_pagamentos_labels'])
        values = json.loads(response.context['chart_pagamentos_data'])
        self.assertEqual(labels, ['Pix', 'Cartão', 'Dinheiro', 'Outros'])
        self.assertEqual(values, [10.0, 20.0, 30.0, 40.0])

    def test_revenue_chart_has_seven_days_and_current_total(self):
        now = timezone.localtime()
        self.create_sale('PIX', '25.00', now, now)

        response = self.client.get(reverse('reports:dashboard'))

        labels = json.loads(response.context['chart_7d_labels'])
        values = json.loads(response.context['chart_7d_data'])
        self.assertEqual(len(labels), 7)
        self.assertEqual(len(values), 7)
        self.assertEqual(values[-1], 25.0)


class CashClosingPDFTests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user(
            matricula='2200',
            nome_completo='Paula Atendente',
            cargo='Atendente',
            password='senha123',
            primeiro_acesso=False,
        )
        self.other_operator = User.objects.create_user(
            matricula='2201',
            nome_completo='João Atendente',
            cargo='Atendente',
            password='senha123',
            primeiro_acesso=False,
        )
        self.cash_register = CashRegister.objects.create(
            operador=self.operator,
            valor_abertura=Decimal('40.00'),
            valor_esperado=Decimal('40.00'),
            valor_fechamento=Decimal('40.00'),
            diferenca_fechamento=Decimal('0.00'),
            status='FECHADO',
            data_fechamento=timezone.now(),
        )
        self.client.login(username='2200', password='senha123')

    def test_operator_can_export_own_closing_pdf(self):
        response = self.client.get(reverse('reports:cash_closing_pdf'), {
            'registro': self.cash_register.id,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_operator_cannot_export_another_operators_closing(self):
        other_register = CashRegister.objects.create(
            operador=self.other_operator,
            valor_abertura=Decimal('10.00'),
            status='FECHADO',
            data_fechamento=timezone.now(),
        )

        response = self.client.get(reverse('reports:cash_closing_pdf'), {
            'registro': other_register.id,
        })

        self.assertEqual(response.status_code, 404)

    def test_operator_can_export_own_closings_by_period(self):
        response = self.client.get(reverse('reports:cash_closing_pdf'), {
            'data_inicio': timezone.localdate().isoformat(),
            'data_fim': timezone.localdate().isoformat(),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
