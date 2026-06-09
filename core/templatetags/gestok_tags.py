"""
Core template tags for Gestok.
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


# Status badge mapping
STATUS_CONFIG = {
    'ABERTA': {
        'class': 'bg-warning text-dark',
        'icon': 'bi-hourglass-split',
    },
    'FINALIZADA': {
        'class': 'bg-success',
        'icon': 'bi-check-circle',
    },
    'ESTORNADA': {
        'class': 'bg-danger',
        'icon': 'bi-arrow-counterclockwise',
    },
    'ATIVO': {
        'class': 'bg-success',
        'icon': 'bi-check',
    },
    'INATIVO': {
        'class': 'bg-secondary',
        'icon': 'bi-dash-circle',
    },
    'ENTRADA': {
        'class': 'bg-info',
        'icon': 'bi-arrow-down-circle',
    },
    'VENDA': {
        'class': 'bg-primary',
        'icon': 'bi-cart-check',
    },
    'ESTORNO': {
        'class': 'bg-danger',
        'icon': 'bi-arrow-counterclockwise',
    },
    'AJUSTE': {
        'class': 'bg-warning text-dark',
        'icon': 'bi-tools',
    },
}


@register.simple_tag
def status_badge(status):
    """
    Renders a Bootstrap badge for a given status.
    Usage: {% status_badge "ABERTA" %} or {% status_badge sale.status %}
    """
    status_upper = str(status).upper()
    config = STATUS_CONFIG.get(status_upper, {
        'class': 'bg-secondary',
        'icon': 'bi-question-circle',
    })

    html = (
        f'<span class="badge {config["class"]}">'
        f'<i class="bi {config["icon"]} me-1" aria-hidden="true"></i>'
        f'{status}'
        f'</span>'
    )
    return mark_safe(html)


@register.filter
def currency_brl(value):
    """
    Formats a number as Brazilian Real currency.
    Usage: {{ value|currency_brl }}
    Output: R$ 1.234,56
    """
    try:
        value = float(value)
        formatted = f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f'R$ {formatted}'
    except (ValueError, TypeError):
        return 'R$ 0,00'


@register.filter
def user_has_group(user, group_name):
    """
    Checks if a user belongs to a specific group.
    Usage: {% if user|user_has_group:"Administrador" %}
    """
    return user.groups.filter(name=group_name).exists()


@register.simple_tag
def active_link(request, url_name, css_class='active'):
    """
    Returns the CSS class if the current URL matches the given URL name.
    Usage: {% active_link request 'core:dashboard' %}
    """
    try:
        from django.urls import reverse
        if request.path == reverse(url_name):
            return css_class
        # Also check if current path starts with the URL (for nested pages)
        if request.path.startswith(reverse(url_name)) and url_name != 'core:dashboard':
            return css_class
    except Exception:
        pass
    return ''
