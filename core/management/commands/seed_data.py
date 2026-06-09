import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from products.models import Category, Product, InventoryMovement
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados iniciais (grupos, usuários, categorias, produtos)'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando o seed_data...')

        # 1. Criar Grupos (opcional, já que o controle usa perfil, mas foi pedido no prompt)
        grupos = ['Administrador', 'Vendas', 'Caixa']
        for g_nome in grupos:
            Group.objects.get_or_create(name=g_nome)

        self.stdout.write(self.style.SUCCESS('Grupos criados.'))

        # 2. Criar Usuários
        usuarios_data = [
            {
                'matricula': '1000',
                'nome_completo': 'Administrador Geral',
                'perfil': 'ADMINISTRADOR',
                'cargo': 'Gerente Geral',
            },
            {
                'matricula': '1001',
                'nome_completo': 'Atendente Vendas',
                'perfil': 'VENDAS',
                'cargo': 'Atendente de Vendas',
            },
            {
                'matricula': '1002',
                'nome_completo': 'Operador Caixa',
                'perfil': 'CAIXA',
                'cargo': 'Operador de Caixa',
            }
        ]

        usuarios_objs = {}
        for u_data in usuarios_data:
            user, created = User.objects.get_or_create(
                matricula=u_data['matricula'],
                defaults={
                    'nome_completo': u_data['nome_completo'],
                    'perfil': u_data['perfil'],
                    'cargo': u_data['cargo'],
                    'primeiro_acesso': True,
                    'is_staff': True if u_data['perfil'] == 'ADMINISTRADOR' else False,
                    'is_superuser': True if u_data['perfil'] == 'ADMINISTRADOR' else False,
                    'ativo': True,
                }
            )

            # Forçamos a senha e o status ativo para garantir o login,
            # mesmo que o usuário já existisse de testes anteriores.
            user.set_password('senha123')
            user.ativo = True
            user.save()

            # Associar ao grupo correspondente
            grupo_nome = 'Administrador' if user.perfil == 'ADMINISTRADOR' else ('Vendas' if user.perfil == 'VENDAS' else 'Caixa')
            g = Group.objects.get(name=grupo_nome)
            user.groups.add(g)

            usuarios_objs[u_data['perfil']] = user

        self.stdout.write(self.style.SUCCESS('Usuários de teste criados (admin, vendas, caixa). Senha: senha123'))

        # 3. Criar Categorias
        cat_bebidas, _ = Category.objects.get_or_create(nome='Bebidas', defaults={'descricao': 'Sucos, refrigerantes, água'})
        cat_alimentos, _ = Category.objects.get_or_create(nome='Alimentos', defaults={'descricao': 'Biscoitos, salgadinhos'})
        cat_limpeza, _ = Category.objects.get_or_create(nome='Limpeza', defaults={'descricao': 'Produtos de limpeza em geral'})

        self.stdout.write(self.style.SUCCESS('Categorias criadas.'))

        # 4. Criar Produtos e Movimentações Iniciais
        produtos_data = [
            {'nome': 'Refrigerante Cola 2L', 'categoria': cat_bebidas, 'custo': 5.00, 'venda': 9.00, 'estoque': 50, 'minimo': 20},
            {'nome': 'Água Mineral 500ml', 'categoria': cat_bebidas, 'custo': 1.00, 'venda': 2.50, 'estoque': 100, 'minimo': 30},
            {'nome': 'Biscoito Recheado', 'categoria': cat_alimentos, 'custo': 2.00, 'venda': 4.50, 'estoque': 5, 'minimo': 10}, # Estoque Crítico
            {'nome': 'Detergente Neutro', 'categoria': cat_limpeza, 'custo': 1.50, 'venda': 3.00, 'estoque': 8, 'minimo': 15}, # Estoque Crítico
            {'nome': 'Suco Laranja 1L', 'categoria': cat_bebidas, 'custo': 4.00, 'venda': 8.50, 'estoque': 40, 'minimo': 15},
        ]

        admin_user = usuarios_objs['ADMINISTRADOR']

        for p_data in produtos_data:
            produto, created = Product.objects.get_or_create(
                nome=p_data['nome'],
                defaults={
                    'categoria': p_data['categoria'],
                    'descricao': f"{p_data['nome']} - Descrição padrão",
                    'preco_custo': p_data['custo'],
                    'preco_venda': p_data['venda'],
                    'estoque_atual': p_data['estoque'],
                    'estoque_minimo': p_data['minimo'],
                    'ativo': True
                }
            )

            if created:
                # Gerar log de ENTRADA para o estoque inicial
                InventoryMovement.objects.create(
                    produto=produto,
                    tipo='ENTRADA',
                    quantidade=p_data['estoque'],
                    estoque_anterior=0,
                    estoque_posterior=p_data['estoque'],
                    usuario=admin_user,
                    observacao='Estoque inicial via seed_data'
                )

        self.stdout.write(self.style.SUCCESS('Produtos e logs de entrada criados.'))
        self.stdout.write(self.style.SUCCESS('--- Seed concluído com sucesso! ---'))
