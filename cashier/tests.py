from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cashier.models import CashRegister
from sales.models import Sale

User = get_user_model()


class CashRegisterFlowTests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user(
            matricula='2000',
            nome_completo='Ana Operadora',
            cargo='Atendente',
            password='senha123',
            primeiro_acesso=False,
        )
        self.client.login(username='2000', password='senha123')

    def test_pdv_requires_opening_when_no_register_is_open(self):
        response = self.client.get(reverse('cashier:pdv'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Abertura de Caixa')
        self.assertEqual(response.context['estado'], 'sem_caixa')

    def test_opening_uses_decimal_and_prevents_duplicate_register(self):
        self.client.post(reverse('cashier:abrir_caixa'), {
            'valor_abertura': '125,50',
        })
        self.client.post(reverse('cashier:abrir_caixa'), {
            'valor_abertura': '50,00',
        })

        registers = CashRegister.objects.filter(
            operador=self.operator,
            status='ABERTO',
        )
        self.assertEqual(registers.count(), 1)
        self.assertEqual(registers.get().valor_abertura, Decimal('125.50'))

    def test_stale_register_blocks_new_sales_until_it_is_closed(self):
        cash_register = CashRegister.objects.create(
            operador=self.operator,
            data_abertura=timezone.now() - timedelta(days=1),
            valor_abertura=Decimal('20.00'),
        )

        response = self.client.get(reverse('cashier:pdv'))

        self.assertEqual(response.context['estado'], 'caixa_pendente')
        self.assertContains(response, 'Caixa Pendente de Fechamento')
        self.assertFalse(Sale.objects.filter(caixa=cash_register).exists())

    def test_open_register_replaces_status_with_close_button(self):
        CashRegister.objects.create(
            operador=self.operator,
            valor_abertura=Decimal('20.00'),
        )

        response = self.client.get(reverse('cashier:pdv'))

        self.assertContains(response, 'Finalizar Caixa')
        self.assertNotContains(response, '<span>Caixa Aberto</span>', html=True)

    def test_closing_saves_expected_amount_and_difference(self):
        cash_register = CashRegister.objects.create(
            operador=self.operator,
            valor_abertura=Decimal('50.00'),
        )
        Sale.objects.create(
            vendedor=self.operator,
            caixa_responsavel=self.operator,
            caixa=cash_register,
            status='FINALIZADA',
            forma_pagamento='DINHEIRO',
            valor_total=Decimal('30.00'),
            data_finalizacao=timezone.now(),
        )

        response = self.client.post(reverse('cashier:fechar_caixa'), {
            'caixa_id': cash_register.id,
            'valor_fechamento': '78,50',
            'observacao': 'Diferença conferida.',
        })

        cash_register.refresh_from_db()
        self.assertRedirects(
            response,
            f"{reverse('cashier:pdv')}?fechado={cash_register.id}",
        )
        self.assertEqual(cash_register.status, 'FECHADO')
        self.assertEqual(cash_register.valor_esperado, Decimal('80.00'))
        self.assertEqual(cash_register.diferenca_fechamento, Decimal('-1.50'))

    def test_closing_history_only_lists_the_operators_registers(self):
        own_register = CashRegister.objects.create(
            operador=self.operator,
            valor_abertura=Decimal('20.00'),
            valor_esperado=Decimal('20.00'),
            valor_fechamento=Decimal('20.00'),
            diferenca_fechamento=Decimal('0.00'),
            status='FECHADO',
            data_fechamento=timezone.now(),
        )
        other_operator = User.objects.create_user(
            matricula='2001',
            nome_completo='Outro Atendente',
            cargo='Atendente',
            password='senha123',
            primeiro_acesso=False,
        )
        other_register = CashRegister.objects.create(
            operador=other_operator,
            valor_abertura=Decimal('10.00'),
            valor_esperado=Decimal('10.00'),
            valor_fechamento=Decimal('10.00'),
            diferenca_fechamento=Decimal('0.00'),
            status='FECHADO',
            data_fechamento=timezone.now(),
        )

        response = self.client.get(reverse('cashier:closing_history'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'#{own_register.id}')
        self.assertNotContains(response, f'#{other_register.id}')
        self.assertContains(response, 'Exportar Período')
