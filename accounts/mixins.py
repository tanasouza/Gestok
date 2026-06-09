from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin that verifies if the current user is an ADMINISTRADOR.
    If not, it displays an error message and redirects to the home/dashboard.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.eh_administrador

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Acesso negado. Apenas administradores podem acessar esta página.")
            return redirect(self.request.user.pagina_inicial)
        return redirect('accounts:login')


class VendasOrAdminRequiredMixin(UserPassesTestMixin):
    """Allows only VENDAS or ADMINISTRADOR profiles."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.pode_vender

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Acesso negado. Apenas vendedores ou administradores podem acessar esta página.")
            return redirect(self.request.user.pagina_inicial)
        return redirect('accounts:login')


class CaixaOrAdminRequiredMixin(UserPassesTestMixin):
    """Allows only CAIXA or ADMINISTRADOR profiles."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.pode_operar_caixa

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Acesso negado. Apenas operadores de caixa ou administradores podem acessar esta página.")
            return redirect(self.request.user.pagina_inicial)
        return redirect('accounts:login')


class ProductViewerRequiredMixin(UserPassesTestMixin):
    """Allows managers and stock clerks to view the product catalog."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.pode_ver_produtos

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Acesso negado. Apenas gerentes e estoquistas podem acessar os produtos.")
            return redirect(self.request.user.pagina_inicial)
        return redirect('accounts:login')


class MovementViewerRequiredMixin(UserPassesTestMixin):
    """Allows managers and attendants to view inventory movements."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.pode_ver_movimentacoes

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Acesso negado. Apenas gerentes e atendentes podem acessar as movimentações.")
            return redirect(self.request.user.pagina_inicial)
        return redirect('accounts:login')
