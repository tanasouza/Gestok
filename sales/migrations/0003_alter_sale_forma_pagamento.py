from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_sale_caixa'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='forma_pagamento',
            field=models.CharField(
                blank=True,
                choices=[
                    ('DINHEIRO', 'Dinheiro'),
                    ('PIX', 'Pix'),
                    ('CARTAO', 'Cartão'),
                    ('OUTROS', 'Outros'),
                ],
                max_length=20,
                null=True,
                verbose_name='Forma de Pagamento',
            ),
        ),
    ]
