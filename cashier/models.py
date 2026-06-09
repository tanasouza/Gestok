from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class CashRegister(models.Model):
    """Represents a cashier shift — opened and closed by a cashier operator."""
    STATUS_CHOICES = (
        ('ABERTO', 'Aberto'),
        ('FECHADO', 'Fechado'),
    )

    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='caixas', verbose_name='Operador'
    )
    data_abertura = models.DateTimeField(default=timezone.now, verbose_name='Data de Abertura')
    data_fechamento = models.DateTimeField(null=True, blank=True, verbose_name='Data de Fechamento')
    valor_abertura = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        verbose_name='Valor de Abertura (Troco)'
    )
    valor_fechamento = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Valor Declarado no Fechamento'
    )
    valor_esperado = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Valor Esperado no Fechamento'
    )
    diferenca_fechamento = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Diferença de Fechamento'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='ABERTO',
        verbose_name='Status'
    )
    observacao_fechamento = models.TextField(
        blank=True, null=True, verbose_name='Observação de Fechamento'
    )

    class Meta:
        verbose_name = 'Caixa'
        verbose_name_plural = 'Caixas'
        ordering = ['-data_abertura']

    def __str__(self):
        return f"Caixa #{self.pk} — {self.operador.nome_completo} ({self.get_status_display()}) em {self.data_abertura.strftime('%d/%m/%Y')}"

    @property
    def total_vendas_dia(self):
        """Returns sum of all finalized sales linked to this cash register."""
        from django.db.models import Sum
        return self.vendas.filter(status='FINALIZADA').aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')

    @property
    def qtd_vendas_dia(self):
        """Returns count of finalized sales linked to this cash register."""
        return self.vendas.filter(status='FINALIZADA').count()
