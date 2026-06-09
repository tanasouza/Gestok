from decimal import Decimal

from django.db.models import Sum


PAYMENT_METHODS = (
    ('DINHEIRO', 'Dinheiro'),
    ('PIX', 'Pix'),
    ('CARTAO', 'Cartão'),
    ('OUTROS', 'Outros'),
)


def cash_register_summary(cash_register):
    finalized_sales = cash_register.vendas.filter(status='FINALIZADA')
    payment_totals = {
        key: finalized_sales.filter(forma_pagamento=key).aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        for key, _label in PAYMENT_METHODS
    }
    total_sales = sum(payment_totals.values(), Decimal('0.00'))
    expected_cash = cash_register.valor_abertura + payment_totals['DINHEIRO']

    return {
        'finalized_sales': finalized_sales.select_related(
            'vendedor', 'caixa_responsavel'
        ).order_by('data_finalizacao'),
        'payment_totals': payment_totals,
        'total_dinheiro': payment_totals['DINHEIRO'],
        'total_pix': payment_totals['PIX'],
        'total_cartao': payment_totals['CARTAO'],
        'total_outros': payment_totals['OUTROS'],
        'total_sales': total_sales,
        'sales_count': finalized_sales.count(),
        'expected_cash': expected_cash,
    }
