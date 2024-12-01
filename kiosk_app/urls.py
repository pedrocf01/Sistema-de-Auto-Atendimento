from django.urls import path, include
from . import views
from django.contrib import admin

urlpatterns = [
    # URLs do Cliente
    path('', views.CardapioView.as_view(), name='cardapio'),
    path('item/<int:item_id>/', views.ItemDetalheView.as_view(), name='item_detalhe'),
    path('adicionar_ao_carrinho/', views.AdicionarAoCarrinhoView.as_view(), name='adicionar_ao_carrinho'),
    path('carrinho/', views.CarrinhoView.as_view(), name='carrinho'),
    path('atualizar_item_carrinho/<int:detalhe_pedido_id>/', 
         views.AtualizarItemCarrinhoView.as_view(), 
         name='atualizar_item_carrinho'),
    path('remover_item_carrinho/<int:detalhe_pedido_id>/', 
         views.RemoverItemCarrinhoView.as_view(), 
         name='remover_item_carrinho'),
    path('finalizar_pedido/', 
         views.FinalizarPedidoView.as_view(), 
         name='finalizar_pedido'),
    path('pedido_confirmado/<int:pedido_id>/', 
         views.PedidoConfirmadoView.as_view(), 
         name='pedido_confirmado'),
    path('pedido/rastreio/', 
         views.PedidoRastreioView.as_view(), 
         name='pedido_rastreio'),
    
    # URLs do Cozinheiro
    path('cozinha/pedidos/', 
         views.CozinheiroPedidoFilaView.as_view(), 
         name='cozinheiro_pedidos'),
    path('cozinha/pedido/<int:pedido_id>/status/', 
         views.CozinheiroAlterarPedidoView.as_view(), 
         name='cozinheiro_alterar_pedido'),
    path('cozinha/historico/', 
         views.CozinheiroPedidoHistoricoView.as_view(), 
         name='cozinheiro_historico'),
    
    # URLs do Administrador
    path('admin/relatorios/vendas/', 
         views.RelatorioVendasView.as_view(), 
         name='relatorio_vendas'),
    
    # Auth URLs
    path('', include('users.urls')),

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