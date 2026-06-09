from django.db import models
from django.conf import settings
from django.utils import timezone


class Category(models.Model):
    """Product category model."""
    nome = models.CharField(max_length=100, verbose_name='Nome')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Product(models.Model):
    """Product model with auto-generated code and stock control."""
    codigo_produto = models.CharField(
        max_length=20, unique=True, db_index=True, editable=False,
        verbose_name='Código do Produto'
    )
    nome = models.CharField(max_length=200, verbose_name='Nome')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    categoria = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='produtos',
        verbose_name='Categoria'
    )
    preco_custo = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Preço de Custo'
    )
    preco_venda = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Preço de Venda'
    )
    estoque_atual = models.IntegerField(default=0, verbose_name='Estoque Atual')
    estoque_minimo = models.IntegerField(default=5, verbose_name='Estoque Mínimo')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo_produto} - {self.nome}"

    @property
    def estoque_critico(self):
        """Returns True if current stock is at or below minimum."""
        return self.estoque_atual <= self.estoque_minimo

    def save(self, *args, **kwargs):
        if not self.codigo_produto:
            last = Product.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.codigo_produto = f"GST-{next_id:06d}"
        super().save(*args, **kwargs)


class InventoryMovement(models.Model):
    """Records every stock change for audit trail."""
    TIPO_CHOICES = (
        ('ENTRADA', 'Entrada'),
        ('VENDA', 'Venda'),
        ('ESTORNO', 'Estorno'),
        ('AJUSTE', 'Ajuste'),
    )

    codigo_movimentacao = models.CharField(
        max_length=20, unique=True, db_index=True, editable=False,
        verbose_name='Código da Movimentação'
    )
    produto = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='movimentacoes',
        verbose_name='Produto'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')
    quantidade = models.IntegerField(verbose_name='Quantidade')
    estoque_anterior = models.IntegerField(verbose_name='Estoque Anterior')
    estoque_posterior = models.IntegerField(verbose_name='Estoque Posterior')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='movimentacoes', verbose_name='Usuário'
    )
    observacao = models.TextField(blank=True, null=True, verbose_name='Observação')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.codigo_movimentacao} - {self.produto.nome} ({self.tipo})"

    def save(self, *args, **kwargs):
        if not self.codigo_movimentacao:
            last = InventoryMovement.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.codigo_movimentacao = f"MOV-{next_id:06d}"
        super().save(*args, **kwargs)
