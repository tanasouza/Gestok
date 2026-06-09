"""
Core context processors for Gestok.
Provides global template context variables.
"""

from django.db import models

def gestok_context(request):
    """
    Add global context variables available in all templates.
    - critical_stock_count: number of products with stock at or below minimum
    - user_profile: the profile/group name of the current user
    - user_initials: the initials of the current user for avatar display
    """
    context = {
        'critical_stock_count': 0,
        'user_profile': '',
        'user_initials': '',
    }

    if request.user.is_authenticated:
        # Get user profile from groups
        groups = request.user.groups.all()
        if groups.exists():
            context['user_profile'] = groups.first().name
        elif request.user.is_superuser:
            context['user_profile'] = 'Administrador'

        # Generate user initials
        full_name = request.user.get_full_name()
        if full_name:
            parts = full_name.split()
            if len(parts) >= 2:
                context['user_initials'] = (parts[0][0] + parts[-1][0]).upper()
            else:
                context['user_initials'] = parts[0][0:2].upper()
        else:
            context['user_initials'] = request.user.username[0:2].upper()

        # Critical stock count — will be populated when products app is ready
        try:
            from products.models import Product
            context['critical_stock_count'] = Product.objects.filter(
                ativo=True,
                estoque_atual__lte=models.F('estoque_minimo')
            ).count()
        except Exception:
            context['critical_stock_count'] = 0

    return context
