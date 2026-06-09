from django import forms
from products.models import Category, Product


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories."""
    class Meta:
        model = Category
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição da categoria (opcional)',
                'rows': 3
            }),
        }


class ProductForm(forms.ModelForm):
    """Form for creating and editing products."""
    class Meta:
        model = Product
        fields = [
            'nome', 'descricao', 'categoria',
            'preco_custo', 'preco_venda',
            'estoque_atual', 'estoque_minimo', 'ativo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do produto'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição do produto (opcional)',
                'rows': 3
            }),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'preco_custo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0,00',
                'step': '0.01',
                'min': '0'
            }),
            'preco_venda': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0,00',
                'step': '0.01',
                'min': '0'
            }),
            'estoque_atual': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0'
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '5',
                'min': '0'
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input m-0', 'role': 'switch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Category.objects.filter(ativo=True)


class ProductEditForm(forms.ModelForm):
    """
    Form for editing products.
    Price fields are only shown if user is ADMINISTRADOR (controlled in view).
    """
    class Meta:
        model = Product
        fields = [
            'nome', 'descricao', 'categoria',
            'preco_custo', 'preco_venda',
            'estoque_atual', 'estoque_minimo', 'ativo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'preco_custo': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'preco_venda': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'estoque_atual': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0'
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0'
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input m-0', 'role': 'switch'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Category.objects.filter(ativo=True)
        # Only admins can change prices
        if user and not user.eh_administrador:
            self.fields['preco_custo'].widget.attrs['readonly'] = True
            self.fields['preco_venda'].widget.attrs['readonly'] = True
            self.fields['preco_custo'].widget.attrs['class'] += ' bg-light'
            self.fields['preco_venda'].widget.attrs['class'] += ' bg-light'


class InventoryEntryForm(forms.Form):
    """Form for manual stock entry (ENTRADA or AJUSTE)."""
    TIPO_CHOICES = (
        ('ENTRADA', 'Entrada de Estoque'),
        ('AJUSTE', 'Ajuste de Estoque'),
    )

    produto = forms.ModelChoiceField(
        queryset=Product.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Produto'
    )
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Movimentação'
    )
    quantidade = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quantidade',
            'min': '1'
        }),
        label='Quantidade'
    )
    observacao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Observação (opcional)',
            'rows': 2
        }),
        label='Observação'
    )
