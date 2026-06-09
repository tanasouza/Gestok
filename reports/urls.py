from django.urls import path
from reports import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('fechamento/', views.FechamentoCaixaView.as_view(), name='cash_closing'),
    path('fechamento-caixa/csv/', views.FechamentoCaixaCSVView.as_view(), name='cash_closing_csv'),
    path('fechamento-caixa/pdf/', views.FechamentoCaixaPDFView.as_view(), name='cash_closing_pdf'),
]
