from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsTestCase(TestCase):
    def setUp(self):
        # Create a superuser / admin
        self.admin = User.objects.create_superuser(
            matricula='1000',
            password='password123',
            nome_completo='Administrador'
        )
        # Create a regular user (defaults to primeiro_acesso=True, perfil=VENDAS)
        self.vendedor = User.objects.create_user(
            nome_completo='João Vendedor',
            email='joao@exemplo.com',
            cargo='Atendente',
        )

    def test_matricula_auto_generation(self):
        """Tests if the sequential matrícula generation works correctly."""
        self.assertEqual(self.admin.matricula, '1000')
        # João should be '1001' (next sequential)
        self.assertEqual(self.vendedor.matricula, '1001')

        # Create another user and check if matricula is '1002'
        another_user = User.objects.create_user(
            nome_completo='Maria Caixa',
            email='maria@exemplo.com',
            cargo='Atendente',
        )
        self.assertEqual(another_user.matricula, '1002')

    def test_login_by_matricula(self):
        """Tests if login works using the matrícula instead of username."""
        # Authenticate admin
        login_success = self.client.login(username='1000', password='password123')
        self.assertTrue(login_success)

    def test_inactive_user_cannot_login(self):
        """Tests that deactivated/inactive users cannot authenticate."""
        self.vendedor.ativo = False
        self.vendedor.save()

        login_success = self.client.login(username='1001', password='senha123')
        self.assertFalse(login_success)

    def test_first_access_redirection(self):
        """Tests that users with primeiro_acesso=True are forced to change their password."""
        # Authenticate regular user
        login_success = self.client.login(username='1001', password='senha123')
        self.assertTrue(login_success)

        # Access dashboard - should be redirected to primeiro_acesso
        response = self.client.get(reverse('reports:dashboard'))
        self.assertRedirects(response, reverse('accounts:primeiro_acesso'))

    def test_change_password_on_first_access(self):
        """Tests successfully setting a new password on first access."""
        self.client.login(username='1001', password='senha123')

        # Post new password
        response = self.client.post(reverse('accounts:primeiro_acesso'), {
            'new_password': 'novasenha123',
            'confirm_password': 'novasenha123'
        })
        self.assertRedirects(response, reverse('sales:my_sales'))

        # Check that user profile is no longer on first access
        self.vendedor.refresh_from_db()
        self.assertFalse(self.vendedor.primeiro_acesso)

        # Check login works with the new password
        self.client.logout()
        login_success = self.client.login(username='1001', password='novasenha123')
        self.assertTrue(login_success)

    def test_admin_permission_required_for_user_crud(self):
        """Tests that only administrators can access user CRUD views."""
        # João (Vendedor) should be blocked from list/create
        self.vendedor.primeiro_acesso = False
        self.vendedor.save(update_fields=['primeiro_acesso'])
        self.client.login(username='1001', password='senha123')

        response = self.client.get(reverse('accounts:user_list'))
        # Should redirect to dashboard with an error message or back to dashboard
        self.assertRedirects(response, reverse('sales:my_sales'))

        self.client.logout()

        # Admin should access successfully
        self.client.login(username='1000', password='password123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_actions_render_offcanvas_partials(self):
        """Add, view and edit actions provide content for the users offcanvas."""
        self.client.login(username='1000', password='password123')

        create_response = self.client.get(
            reverse('accounts:user_create'),
            {'partial': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        detail_response = self.client.get(
            reverse('accounts:user_detail', args=[self.vendedor.pk]),
            {'partial': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        edit_response = self.client.get(
            reverse('accounts:user_edit', args=[self.vendedor.pk]),
            {'partial': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertTemplateUsed(create_response, 'accounts/user_form_partial.html')
        self.assertTemplateUsed(detail_response, 'accounts/user_detail_partial.html')
        self.assertTemplateUsed(edit_response, 'accounts/user_form_partial.html')
        self.assertContains(create_response, 'id="userForm"')
        self.assertContains(detail_response, 'Detalhes do Usuário')
        self.assertContains(edit_response, 'Editar Usuário')

    def test_invalid_user_create_stays_in_offcanvas_form(self):
        """Validation errors return the partial form instead of another page."""
        self.client.login(username='1000', password='password123')

        response = self.client.post(
            f"{reverse('accounts:user_create')}?partial=true",
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/user_form_partial.html')
        self.assertContains(response, 'id="userForm"')
        self.assertContains(response, 'invalid-feedback')

    def test_user_address_fields_support_properties_without_number(self):
        """Structured address fields are consolidated and accept homes without a number."""
        self.client.login(username='1000', password='password123')

        response = self.client.post(
            reverse('accounts:user_create'),
            {
                'nome_completo': 'Morador Sem Número',
                'email': 'morador@example.com',
                'telefone': '(92) 99999-9999',
                'cargo': 'Atendente',
                'cep': '69000000',
                'rua': 'Rua das Flores',
                'setor': 'Centro',
                'numero': '',
                'sem_numero': 'on',
            },
        )

        self.assertRedirects(response, reverse('accounts:user_list'))
        created_user = User.objects.get(email='morador@example.com')
        self.assertEqual(
            created_user.endereco,
            'CEP: 69000-000 | Rua: Rua das Flores | Setor: Centro | Número: S/N',
        )

    def test_user_address_requires_number_or_no_number_option(self):
        """An informed address must include a number or the explicit no-number option."""
        self.client.login(username='1000', password='password123')

        response = self.client.post(
            f"{reverse('accounts:user_create')}?partial=true",
            {
                'nome_completo': 'Morador Com Endereço',
                'cargo': 'Atendente',
                'cep': '69000-000',
                'rua': 'Rua Principal',
                'setor': 'Centro',
                'numero': '',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Informe o número ou marque a opção')

    def test_permissions_are_derived_from_operational_role(self):
        """The operational role automatically defines the internal permission profile."""
        cases = {
            'Gerente': 'ADMINISTRADOR',
            'Atendente': 'VENDAS',
            'Estoquista': 'ESTOQUE',
        }

        for index, (cargo, expected_profile) in enumerate(cases.items(), start=1):
            user = User.objects.create_user(
                nome_completo=f'Usuário {index}',
                email=f'cargo{index}@example.com',
                cargo=cargo,
            )
            self.assertEqual(user.perfil, expected_profile)

    def test_user_form_exposes_role_but_not_access_profile(self):
        """Administrators choose only the operational role in user forms."""
        self.client.login(username='1000', password='password123')

        response = self.client.get(
            reverse('accounts:user_create'),
            {'partial': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertContains(response, 'id="id_cargo"')
        self.assertNotContains(response, 'id="id_perfil"')
        self.assertNotContains(response, 'Perfil de acesso')

    def test_header_and_sidebar_show_simplified_account_actions(self):
        """The header has profile/logout only and the sidebar has no reports item."""
        self.admin.nome_completo = 'Ana Silva Castro'
        self.admin.save()
        self.client.login(username='1000', password='password123')

        response = self.client.get(reverse('reports:dashboard'))

        self.assertContains(response, 'Ana C.')
        self.assertContains(response, 'Ver Perfil')
        self.assertContains(response, '>Logout<')
        self.assertContains(response, '>Perfil<')
        self.assertNotContains(response, 'topbar-brand-logo')
        self.assertNotContains(response, 'Alterar Senha')
        self.assertNotContains(response, '>Relatórios<')

    def test_market_roles_enforce_screen_access(self):
        """Each market role can access only its operational screens."""
        gerente = self.admin
        atendente = self.vendedor
        atendente.primeiro_acesso = False
        atendente.save(update_fields=['primeiro_acesso'])
        estoquista = User.objects.create_user(
            nome_completo='Maria Estoquista',
            email='estoque@example.com',
            cargo='Estoquista',
            password='password123',
            primeiro_acesso=False,
        )

        protected_routes = {
            'dashboard': reverse('reports:dashboard'),
            'products': reverse('products:product_list'),
            'movements': reverse('products:movement_list'),
            'sales': reverse('sales:my_sales'),
            'cashier': reverse('cashier:pdv'),
            'users': reverse('accounts:user_list'),
            'profile': reverse('accounts:profile'),
        }
        expected_access = {
            gerente: set(protected_routes),
            atendente: {'movements', 'sales', 'cashier', 'profile'},
            estoquista: {'products', 'profile'},
        }

        for user, allowed_routes in expected_access.items():
            self.client.force_login(user)
            for route_name, route_url in protected_routes.items():
                response = self.client.get(route_url)
                if route_name in allowed_routes:
                    self.assertEqual(response.status_code, 200, f'{user.cargo} should access {route_name}')
                else:
                    self.assertRedirects(
                        response,
                        reverse(user.pagina_inicial),
                        msg_prefix=f'{user.cargo} should not access {route_name}',
                    )
