from django import forms
from django.forms import inlineformset_factory
from sales.models import Sale, SaleItem
from products.models import Product

class SaleForm(forms.ModelForm):
    """Form for Sale header. During creation, most fields are set programmatically."""
    class Meta:
        model = Sale
        fields = []  # Vendedor is set to request.user, other fields are set at checkout or auto-generated.


class SaleItemForm(forms.ModelForm):
    """Form for individual Sale items."""
    class Meta:
        model = SaleItem
        fields = ['produto', 'quantidade', 'preco_unitario']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-select select-produto'}),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control input-quantidade',
                'min': '1',
                'placeholder': 'Qtd'
            }),
            'preco_unitario': forms.NumberInput(attrs={
                'class': 'form-control input-preco-unitario bg-light',
                'step': '0.01',
                'readonly': 'readonly',
                'placeholder': 'R$ 0,00'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow active products
        self.fields['produto'].queryset = Product.objects.filter(ativo=True).order_by('nome')
        self.fields['produto'].empty_label = "Selecione o produto..."

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        quantidade = cleaned_data.get('quantidade')

        if produto and quantidade:
            # Check if stock is sufficient (we do a preliminary check here, but cashier has final validation)
            if produto.estoque_atual < quantidade:
                self.add_error(
                    'quantidade',
                    f"Estoque insuficiente. Disponível: {produto.estoque_atual} unidades."
                )
        return cleaned_data


# Inline Formset to manage sale items within the sale form
SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)
