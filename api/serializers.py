from rest_framework import serializers
from products.models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'codigo_produto', 'nome', 'descricao', 'categoria',
            'categoria_nome', 'preco_custo', 'preco_venda',
            'estoque_atual', 'estoque_minimo', 'ativo'
        ]
