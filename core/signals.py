from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings

from core.models import log_action
from accounts.models import CustomUser
from products.models import Product, InventoryMovement
from sales.models import Sale
from cashier.models import CashRegister


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_action(user, f"Login efetuado com sucesso. Perfil: {user.get_perfil_display()}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_action(user, "Logout efetuado.")


@receiver(post_save, sender=CustomUser)
def log_user_changes(sender, instance, created, **kwargs):
    if created:
        log_action(None, f"Novo usuário cadastrado: {instance.nome_completo} (Matrícula: {instance.matricula}, Perfil: {instance.get_perfil_display()})")
    else:
        # Check if active status changed
        log_action(None, f"Usuário atualizado: {instance.nome_completo} (Matrícula: {instance.matricula}, Perfil: {instance.get_perfil_display()}, Ativo: {instance.ativo})")


@receiver(pre_save, sender=Product)
def log_product_price_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_product = Product.objects.get(pk=instance.pk)
            changes = []
            if old_product.preco_venda != instance.preco_venda:
                changes.append(f"Venda: R$ {old_product.preco_venda} -> R$ {instance.preco_venda}")
            if old_product.preco_custo != instance.preco_custo:
                changes.append(f"Custo: R$ {old_product.preco_custo} -> R$ {instance.preco_custo}")

            if changes:
                log_action(None, f"Preço do produto '{instance.nome}' ({instance.codigo_produto}) alterado. {', '.join(changes)}")
        except Product.DoesNotExist:
            pass


@receiver(post_save, sender=Sale)
def log_sale_changes(sender, instance, created, **kwargs):
    if created:
        log_action(instance.vendedor, f"Venda {instance.numero_venda} criada (Status: ABERTA)")
    else:
        # If status was updated to finalizada or estornada
        log_action(None, f"Venda {instance.numero_venda} atualizada. Status: {instance.status}, Valor Total: R$ {instance.valor_total}")


@receiver(post_save, sender=InventoryMovement)
def log_inventory_movements(sender, instance, created, **kwargs):
    if created and instance.tipo in ['ENTRADA', 'AJUSTE']:
        log_action(instance.usuario, f"Movimentação de estoque ({instance.tipo}) para '{instance.produto.nome}' ({instance.produto.codigo_produto}): {instance.quantidade} unidades. Estoque: {instance.estoque_anterior} -> {instance.estoque_posterior}")

@receiver(post_save, sender=CashRegister)
def log_cash_register_changes(sender, instance, created, **kwargs):
    if created:
        log_action(instance.operador, f"Abertura de Caixa. Valor: R$ {instance.valor_abertura}")
    elif instance.status == 'FECHADO' and instance.data_fechamento:
        log_action(instance.operador, f"Fechamento de Caixa. Apurado: R$ {instance.valor_fechamento}")
