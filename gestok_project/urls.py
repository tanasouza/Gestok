"""
gestok_project URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('sales/', include('sales.urls')),
    path('cashier/', include('cashier.urls')),
    path('reports/', include('reports.urls')),
    path('api/', include('api.urls')),
]
