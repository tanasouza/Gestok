from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, F
from django.http import HttpResponse

from accounts.mixins import AdminRequiredMixin, MovementViewerRequiredMixin, ProductViewerRequiredMixin
from core.date_filters import filter_by_local_date_range
from core.pdf_reports import build_movements_pdf
from products.models import Category, Product, InventoryMovement
from products.forms import CategoryForm, ProductForm, ProductEditForm, InventoryEntryForm


# ─── Categories ──────────────────────────────────────────────────────

class CategoryListView(ProductViewerRequiredMixin, ListView):
    """List all active categories."""
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_queryset(self):
        queryset = Category.objects.filter(ativo=True).order_by('nome')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(nome__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CategoryCreateView(AdminRequiredMixin, CreateView):
    """Create a new category. Admin only."""
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')

    def form_valid(self, form):
        messages.success(self.request, f"Categoria '{form.cleaned_data['nome']}' cadastrada com sucesso!")
        return super().form_valid(form)


class CategoryEditView(AdminRequiredMixin, UpdateView):
    """Edit an existing category. Admin only."""
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Categoria '{form.cleaned_data['nome']}' atualizada.")
        return super().form_valid(form)


class CategoryToggleActiveView(AdminRequiredMixin, View):
    """Activate/deactivate a category."""
    def post(self, request, pk, *args, **kwargs):
        category = get_object_or_404(Category, pk=pk)
        category.ativo = not category.ativo
        category.save()
        status = "ativada" if category.ativo else "desativada"
        messages.success(request, f"Categoria '{category.nome}' foi {status}.")
        return redirect('products:category_list')


# ─── Products ────────────────────────────────────────────────────────

class ProductListView(ProductViewerRequiredMixin, ListView):
    """List all products with search and filters."""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.select_related('categoria').order_by('nome')

        # Active filter (default: show all so inactive products remain visible)
        status_filter = self.request.GET.get('status', 'todos')
        if status_filter == 'ativo':
            queryset = queryset.filter(ativo=True)
        elif status_filter == 'inativo':
            queryset = queryset.filter(ativo=False)
        # 'todos' shows all

        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) |
                Q(codigo_produto__icontains=search) |
                Q(categoria__nome__icontains=search)
            )

        # Category filter
        cat_filter = self.request.GET.get('categoria', '')
        if cat_filter:
            queryset = queryset.filter(categoria_id=cat_filter)

        # Critical stock filter
        critico = self.request.GET.get('critico', '')
        if critico == '1':
            queryset = queryset.filter(estoque_atual__lte=F('estoque_minimo'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', 'todos')
        context['categoria_filter'] = self.request.GET.get('categoria', '')
        context['critico_filter'] = self.request.GET.get('critico', '')
        context['categorias'] = Category.objects.filter(ativo=True).order_by('nome')
        return context


class ProductCreateView(AdminRequiredMixin, CreateView):
    """Create a new product. Admin only."""
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')

    def get_template_names(self):
        if self.request.GET.get('partial') == 'true':
            return ['products/product_form_partial.html']
        return [self.template_name]

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Produto '{self.object.nome}' cadastrado com sucesso! Código: {self.object.codigo_produto}"
        )
        return response


class ProductEditView(AdminRequiredMixin, UpdateView):
    """Edit an existing product. Admin only (price editing restricted)."""
    model = Product
    form_class = ProductEditForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')

    def get_template_names(self):
        if self.request.GET.get('partial') == 'true':
            return ['products/product_form_partial.html']
        return [self.template_name]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Produto '{form.instance.nome}' atualizado.")
        return super().form_valid(form)


class ProductToggleActiveView(AdminRequiredMixin, View):
    """Activate/deactivate a product (soft delete)."""
    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        product.ativo = not product.ativo
        product.save()
        status = "ativado" if product.ativo else "desativado"
        messages.success(request, f"Produto '{product.nome}' foi {status}.")
        return redirect('products:product_list')


# ─── Inventory Movements ─────────────────────────────────────────────


def filtered_movements(request):
    queryset = InventoryMovement.objects.select_related(
        'produto', 'usuario'
    ).order_by('-criado_em')

    movement_type = request.GET.get('tipo', '')
    if movement_type:
        queryset = queryset.filter(tipo=movement_type)

    queryset = filter_by_local_date_range(
        queryset,
        'criado_em',
        request.GET.get('data_inicio', ''),
        request.GET.get('data_fim', '')
    )

    product_id = request.GET.get('produto', '')
    if product_id:
        queryset = queryset.filter(produto_id=product_id)

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(codigo_movimentacao__icontains=search) |
            Q(produto__codigo_produto__icontains=search) |
            Q(produto__nome__icontains=search) |
            Q(usuario__nome_completo__icontains=search)
        )

    return queryset


class MovementListView(MovementViewerRequiredMixin, ListView):
    """List all inventory movements."""
    model = InventoryMovement
    template_name = 'products/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 10

    def get_queryset(self):
        return filtered_movements(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        context['data_inicio'] = self.request.GET.get('data_inicio', '')
        context['data_fim'] = self.request.GET.get('data_fim', '')
        context['produto_filter'] = self.request.GET.get('produto', '')
        context['tipo_choices'] = InventoryMovement.TIPO_CHOICES
        context['produtos'] = Product.objects.filter(ativo=True).order_by('nome')
        return context


class MovementPDFView(MovementViewerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        movement_type = request.GET.get('tipo', '')
        product_id = request.GET.get('produto', '')
        product_name = ''
        if product_id:
            product_name = Product.objects.filter(id=product_id).values_list(
                'nome', flat=True
            ).first() or ''

        filters = [
            ('Busca', request.GET.get('search', '')),
            ('Tipo', dict(InventoryMovement.TIPO_CHOICES).get(movement_type, '')),
            ('Data inicial', request.GET.get('data_inicio', '')),
            ('Data final', request.GET.get('data_fim', '')),
            ('Produto', product_name),
        ]
        pdf = build_movements_pdf(
            filtered_movements(request),
            request.user.nome_completo or request.user.matricula,
            filters,
        )
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="movimentacoes_estoque.pdf"'
        )
        return response


class InventoryEntryView(AdminRequiredMixin, FormView):
    """Manual stock entry (ENTRADA or AJUSTE). Admin only."""
    template_name = 'products/inventory_entry_form.html'
    form_class = InventoryEntryForm
    success_url = reverse_lazy('products:movement_list')

    def form_valid(self, form):
        produto = form.cleaned_data['produto']
        tipo = form.cleaned_data['tipo']
        quantidade = form.cleaned_data['quantidade']
        observacao = form.cleaned_data['observacao']

        estoque_anterior = produto.estoque_atual
        produto.estoque_atual += quantidade
        produto.save()

        InventoryMovement.objects.create(
            produto=produto,
            tipo=tipo,
            quantidade=quantidade,
            estoque_anterior=estoque_anterior,
            estoque_posterior=produto.estoque_atual,
            usuario=self.request.user,
            observacao=observacao
        )

        messages.success(
            self.request,
            f"Movimentação de {tipo} registrada: {quantidade} unidades de '{produto.nome}'. "
            f"Estoque: {estoque_anterior} → {produto.estoque_atual}"
        )
        return super().form_valid(form)
