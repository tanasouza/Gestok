from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sales.models import Sale

User = get_user_model()


class SalesPDFTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            matricula='2300',
            nome_completo='Marina Atendente',
            cargo='Atendente',
            password='senha123',
            primeiro_acesso=False,
        )
        self.other_seller = User.objects.create_user(
            matricula='2301',
            nome_completo='Outro Vendedor',
            cargo='Atendente',
            password='senha123',
            primeiro_acesso=False,
        )
        self.sale = Sale.objects.create(
            vendedor=self.seller,
            caixa_responsavel=self.seller,
            status='FINALIZADA',
            forma_pagamento='PIX',
            valor_total=Decimal('75.00'),
            data_finalizacao=timezone.now(),
        )
        Sale.objects.create(
            vendedor=self.other_seller,
            caixa_responsavel=self.other_seller,
            status='FINALIZADA',
            forma_pagamento='DINHEIRO',
            valor_total=Decimal('90.00'),
            data_finalizacao=timezone.now(),
        )
        self.client.login(username='2300', password='senha123')

    def test_sales_page_exposes_pdf_export_with_current_filters(self):
        response = self.client.get(reverse('sales:my_sales'), {
            'status': 'FINALIZADA',
            'search': self.sale.numero_venda,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Exportar PDF')
        self.assertEqual(list(response.context['sales']), [self.sale])

    def test_seller_can_export_filtered_sales_pdf(self):
        response = self.client.get(reverse('sales:sales_pdf'), {
            'status': 'FINALIZADA',
            'search': self.sale.numero_venda,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('relatorio_vendas.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))
