from django.urls import path, include
from . import views
from django.contrib import admin

urlpatterns = [
    # URLs do Cliente
    #path('', views.cardapio_view, name='cardapio'),
    path('item/<int:item_id>/', views.item_detalhe_view, name='item_detalhe'),
    path('carrinho/', views.carrinho_view, name='carrinho'),
    path('pedido/resumo/', views.pedido_resumo_view, name='pedido_resumo'),
    path('pedido/rastreio/', views.pedido_rastreio_view, name='pedido_rastreio'),

    # # Admin URLs
    # path('admin/users/', views.admin_user_management, name='admin_users'),
    # path('admin/menu/', views.admin_menu_management, name='admin_menu'),
    # path('admin/orders/', views.admin_order_management, name='admin_orders'),
    # path('admin/reports/', views.admin_reports_view, name='admin_reports'),
    
    # # URLs do Cozinheiro
    # path('cozinheiro/pedido/', views.cozinheiro_pedido_fila_view, name='cozinheiro_pedidos'),
    # path('cozinheiro/pedido/<int:order_id>/alterar/', views.cozinheiro_update_pedido_status, name='cozinheiro_alterar_pedido'),
    # path('cozinheiro/historico/', views.cozinheiro_pedido_historico_view, name='cozinheiro_historico'),
]