from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cashier.models import CashRegister

User = get_user_model()


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
