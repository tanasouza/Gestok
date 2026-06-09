from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Category, InventoryMovement, Product

User = get_user_model()


class MovementPDFTests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user(
            matricula='2100',
            nome_completo='Carlos Atendente',
            cargo='Atendente',
            password='senha123',
            primeiro_acesso=False,
        )
        category = Category.objects.create(nome='Bebidas')
        product = Product.objects.create(
            nome='Água Mineral',
            categoria=category,
            estoque_atual=10,
            estoque_minimo=2,
            preco_custo=2,
            preco_venda=4,
        )
        InventoryMovement.objects.create(
            produto=product,
            tipo='ENTRADA',
            quantidade=10,
            estoque_anterior=0,
            estoque_posterior=10,
            usuario=self.operator,
            observacao='Estoque inicial',
        )
        self.client.login(username='2100', password='senha123')

    def test_movement_pdf_is_generated_with_current_filters(self):
        response = self.client.get(reverse('products:movement_pdf'), {
            'tipo': 'ENTRADA',
            'search': 'Água',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('movimentacoes_estoque.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_stock_clerk_cannot_export_movements(self):
        stock_clerk = User.objects.create_user(
            matricula='2101',
            nome_completo='Rita Estoquista',
            cargo='Estoquista',
            password='senha123',
            primeiro_acesso=False,
        )
        self.client.logout()
        self.client.login(username='2101', password='senha123')

        response = self.client.get(reverse('products:movement_pdf'))

        self.assertRedirects(response, reverse('products:product_list'))
