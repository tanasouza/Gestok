from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, FormView, TemplateView, View
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q

from accounts.models import CustomUser
from accounts.forms import LoginForm, UserCreateForm, UserEditForm, FirstAccessForm
from accounts.mixins import AdminRequiredMixin

class LoginView(FormView):
    """
    CBV to handle user login.
    """
    template_name = 'accounts/login.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.primeiro_acesso:
                return redirect('accounts:primeiro_acesso')
            return redirect(request.user.pagina_inicial)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        matricula = form.cleaned_data.get('matricula')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=matricula, password=password)

        if user is not None:
            login(self.request, user)
            if user.primeiro_acesso:
                return redirect('accounts:primeiro_acesso')
            messages.success(self.request, f"Bem-vindo(a), {user.nome_completo}!")
            return redirect(user.pagina_inicial)
        else:
            messages.error(self.request, "Matrícula ou senha incorretas, ou usuário inativo.")
            return self.form_invalid(form)

class LogoutView(View):
    """
    CBV to handle user logout (must be a POST request).
    """
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Sessão encerrada com sucesso.")
        return redirect('accounts:login')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(request.user.pagina_inicial)
        return redirect('accounts:login')

class FirstAccessView(LoginRequiredMixin, FormView):
    """
    CBV that forces the user to change password on their first login.
    """
    template_name = 'accounts/primeiro_acesso.html'
    form_class = FirstAccessForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.primeiro_acesso:
            return redirect(request.user.pagina_inicial)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        new_password = form.cleaned_data.get('new_password')
        user.set_password(new_password)
        user.primeiro_acesso = False
        user.save()

        # Keep the session active after password change
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Senha definida com sucesso! Bem-vindo ao Gestok.")
        return redirect(user.pagina_inicial)

class UserListView(AdminRequiredMixin, ListView):
    """
    CBV to list active users.
    Only accessible by ADMINISTRADOR.
    """
    model = CustomUser
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by('nome_completo')

        # Filter by search query (name or matricula)
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(nome_completo__icontains=search_query) |
                Q(matricula__icontains=search_query) |
                Q(cargo__icontains=search_query)
            )

        # Filter by operational role
        cargo_filter = self.request.GET.get('cargo', '')
        if cargo_filter:
            queryset = queryset.filter(cargo=cargo_filter)

        # Filter by status
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'ativo':
            queryset = queryset.filter(ativo=True)
        elif status_filter == 'inativo':
            queryset = queryset.filter(ativo=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['cargo_filter'] = self.request.GET.get('cargo', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['cargo_choices'] = CustomUser.CARGO_CHOICES
        return context

class UserCreateView(AdminRequiredMixin, CreateView):
    """
    CBV to register a new user.
    Only ADMINISTRADOR can register new users.
    """
    model = CustomUser
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_template_names(self):
        if self.request.GET.get('partial') == 'true':
            return ['accounts/user_form_partial.html']
        return [self.template_name]

    def form_valid(self, form):
        # Create user with default password (senha123)
        user = form.save(commit=False)
        user.set_password('senha123')
        user.primeiro_acesso = True
        user.ativo = True
        user.save()

        messages.success(
            self.request,
            f"Usuário {user.nome_completo} cadastrado com sucesso! Matrícula gerada: {user.matricula}. A senha inicial é 'senha123'."
        )
        return super().form_valid(form)

class UserEditView(AdminRequiredMixin, UpdateView):
    """
    CBV to edit user details.
    Only ADMINISTRADOR can edit.
    """
    model = CustomUser
    form_class = UserEditForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_template_names(self):
        if self.request.GET.get('partial') == 'true':
            return ['accounts/user_form_partial.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Dados do usuário {form.instance.nome_completo} atualizados.")
        return super().form_valid(form)


class UserDetailView(AdminRequiredMixin, DetailView):
    """Show user information in the list offcanvas, with a full-page fallback."""
    model = CustomUser
    context_object_name = 'selected_user'
    template_name = 'accounts/user_detail.html'

    def get_template_names(self):
        if self.request.GET.get('partial') == 'true':
            return ['accounts/user_detail_partial.html']
        return [self.template_name]


class UserToggleActiveView(AdminRequiredMixin, View):
    """
    CBV to activate/deactivate (soft delete) a user.
    Only ADMINISTRADOR can do this.
    """
    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=pk)

        # Do not allow administrative suicide (deactivating oneself)
        if user == request.user:
            messages.error(request, "Você não pode desativar seu próprio usuário.")
            return redirect('accounts:user_list')

        user.ativo = not user.ativo
        user.save()

        status_str = "ativado" if user.ativo else "desativado"
        messages.success(request, f"Usuário {user.nome_completo} foi {status_str} com sucesso.")
        return redirect('accounts:user_list')

class InactiveUserListView(AdminRequiredMixin, ListView):
    """
    CBV to list deactivated users.
    Only ADMINISTRADOR can view this.
    """
    model = CustomUser
    template_name = 'accounts/user_inactive_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        return CustomUser.objects.filter(ativo=False).order_by('nome_completo')

class ProfileView(LoginRequiredMixin, TemplateView):
    """
    CBV to show the current user's profile information.
    """
    template_name = 'accounts/profile.html'

class ChangePasswordView(LoginRequiredMixin, FormView):
    """
    CBV for regular password change.
    """
    template_name = 'accounts/change_password.html'
    form_class = FirstAccessForm
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        user = self.request.user
        new_password = form.cleaned_data.get('new_password')
        user.set_password(new_password)
        user.save()

        # Maintain session
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Senha alterada com sucesso!")
        return super().form_valid(form)
