from django.db import models
from django.conf import settings
from django.utils import timezone
from products.models import Product

class Sale(models.Model):
    """Sale header model containing global sale details."""
    STATUS_CHOICES = (
        ('ABERTA', 'Aberta'),
        ('FINALIZADA', 'Finalizada'),
        ('ESTORNADA', 'Estornada'),
    )
    PAGAMENTO_CHOICES = (
        ('DINHEIRO', 'Dinheiro'),
        ('PIX', 'Pix'),
        ('CARTAO', 'Cartão'),
        ('OUTROS', 'Outros'),
    )

    numero_venda = models.CharField(
        max_length=20, unique=True, db_index=True, editable=False,
        verbose_name='Número da Venda'
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='vendas_vendedor', verbose_name='Vendedor'
    )
    caixa_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='vendas_caixa', null=True, blank=True,
        verbose_name='Operador do Caixa'
    )
    caixa = models.ForeignKey(
        'cashier.CashRegister', on_delete=models.PROTECT,
        related_name='vendas', null=True, blank=True,
        verbose_name='Caixa Registradora'
    )
    data_venda = models.DateTimeField(default=timezone.now, verbose_name='Data de Abertura')
    data_finalizacao = models.DateTimeField(null=True, blank=True, verbose_name='Data de Finalização')
    forma_pagamento = models.CharField(
        max_length=20, choices=PAGAMENTO_CHOICES, null=True, blank=True,
        verbose_name='Forma de Pagamento'
    )
    valor_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        verbose_name='Valor Total'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='ABERTA',
        verbose_name='Status'
    )
    estornada = models.BooleanField(default=False, verbose_name='Estornada')

    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-data_venda']

    def __str__(self):
        return f"{self.numero_venda} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.numero_venda:
            last = Sale.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.numero_venda = f"VEN-{next_id:06d}"
        super().save(*args, **kwargs)

    def calcular_total(self):
        """Calculates total value of the sale based on its items and saves."""
        total = self.itens.aggregate(total=models.Sum('subtotal'))['total'] or 0.00
        self.valor_total = total
        self.save(update_fields=['valor_total'])


class SaleItem(models.Model):
    """Individual product item in a sale."""
    venda = models.ForeignKey(
        Sale, on_delete=models.CASCADE, related_name='itens',
        verbose_name='Venda'
    )
    produto = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='itens_venda',
        verbose_name='Produto'
    )
    quantidade = models.IntegerField(verbose_name='Quantidade')
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Unitário')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal')

    class Meta:
        verbose_name = 'Item da Venda'
        verbose_name_plural = 'Itens da Venda'

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} em {self.venda.numero_venda}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)
        # Recalculate global sale total
        self.venda.calcular_total()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.venda.calcular_total()
