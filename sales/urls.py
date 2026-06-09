from django.urls import path
from sales import views

app_name = 'sales'

urlpatterns = [
    path('my-sales/', views.MySalesListView.as_view(), name='my_sales'),
    path('my-sales/pdf/', views.SalesPDFView.as_view(), name='sales_pdf'),
    path('<int:pk>/', views.SaleDetailView.as_view(), name='sale_detail'),
    path('<int:pk>/estorno/', views.SaleRefundView.as_view(), name='sale_refund'),
]
