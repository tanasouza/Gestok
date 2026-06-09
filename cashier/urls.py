from django.urls import path
from cashier import views

app_name = 'cashier'

urlpatterns = [
    path('', views.PDVView.as_view(), name='pdv'),
    path('fechamentos/', views.CashClosingHistoryView.as_view(), name='closing_history'),
    path('abrir/', views.AbrirCaixaView.as_view(), name='abrir_caixa'),
    path('fechar/', views.FecharCaixaView.as_view(), name='fechar_caixa'),
    path('adicionar-item/', views.AdicionarItemView.as_view(), name='adicionar_item'),
    path('atualizar-item/<int:item_id>/', views.AtualizarItemQuantidadeView.as_view(), name='atualizar_item'),
    path('remover-item/<int:item_id>/', views.RemoverItemView.as_view(), name='remover_item'),
    path('finalizar-venda/', views.FinalizarVendaView.as_view(), name='finalizar_venda'),
    path('cancelar-venda/', views.CancelarVendaView.as_view(), name='cancelar_venda'),
]
