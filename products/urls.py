from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Categorias
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryEditView.as_view(), name='category_update'),

    # Produtos
    path('', views.ProductListView.as_view(), name='product_list'),
    path('new/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/edit/', views.ProductEditView.as_view(), name='product_update'),

    # Estoque (Movimentações)
    path('movements/', views.MovementListView.as_view(), name='movement_list'),
    path('movements/pdf/', views.MovementPDFView.as_view(), name='movement_pdf'),
    path('inventory-entry/', views.InventoryEntryView.as_view(), name='inventory_entry'),
]
