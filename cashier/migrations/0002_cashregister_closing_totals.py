from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cashier', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashregister',
            name='diferenca_fechamento',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name='Diferença de Fechamento',
            ),
        ),
        migrations.AddField(
            model_name='cashregister',
            name='valor_esperado',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name='Valor Esperado no Fechamento',
            ),
        ),
    ]
