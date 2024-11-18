from django.shortcuts import render, redirect, get_object_or_404
from .models import Categoria, Item, Promocao, Pedido, DetalhePedido, TamanhoItem
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, F, ExpressionWrapper, DurationField
from .gerenciador_carrinho import ItemCarrinho, GerenciadorCarrinho
from .servicos_checkout import ServicoCheckout
from users.models import Usuario


def cardapio_view(request):
    categorias = Categoria.objects.all()
    itens = Item.objects.prefetch_related('tamanhos', 'ingredientes_extras')  
    context = {
        'categorias': categorias,
        'itens': itens,
    }
    return render(request, 'kiosk_app/cardapio.html', context)

def item_detalhe_view(request, item_id):
    item = Item.objects.get(id=item_id)
    context = {
        'item': item,
    }
    return render(request, 'item_detalhe.html', context)


@login_required
def pedido_rastreio_view(request):
    pedidos = Pedido.objects.filter(cliente=request.user).exclude(status_pedido=0)
    context = {
        'pedidos': pedidos,
    }
    return render(request, 'pedidos_rastreio.html', context)


@login_required
def adicionar_ao_carrinho(request):
    if request.method == 'POST':
        # Criar ItemCarrinho a partir dos dados da requisição
        item_carrinho = ItemCarrinho(
            item_id=request.POST.get('item_id'),
            tamanho_item_id=request.POST.get('tamanho_item_id'),
            sabor_id=request.POST.get('sabor_id'),
            ingredientes_extras_ids=request.POST.getlist('ingredientes_extras')
        )

        # Usar o GerenciadorCarrinho para adicionar o item
        gerenciador_carrinho = GerenciadorCarrinho(request.user)
        gerenciador_carrinho.adicionar_item(item_carrinho)

        return redirect('kiosk_app:carrinho')
    return redirect('kiosk_app:cardapio')




@login_required
def carrinho_view(request):
    pedido = Pedido.objects.filter(cliente=request.user, status_pedido=0).first()
    if pedido:
        itens_pedido = pedido.itens.select_related('item', 'tamanho_item', 'promocao').prefetch_related('ingredientes_extras')
        total = pedido.get_total()
    else:
        itens_pedido = []
        total = 0.00
    return render(request, 'kiosk_app/carrinho.html', {'itens_pedido': itens_pedido, 'total': total})


@login_required
def atualizar_item_carrinho(request, detalhe_pedido_id):
    detalhe_pedido = get_object_or_404(DetalhePedido, id=detalhe_pedido_id, pedido__cliente=request.user, pedido__status_pedido=0)
    if request.method == 'POST':
        quantidade = int(request.POST.get('quantidade_item', 1))
        if quantidade > 0:
            detalhe_pedido.quantidade_item = quantidade
            detalhe_pedido.save()
        else:
            detalhe_pedido.delete()
    return redirect('kiosk_app:carrinho')


@login_required
def remover_item_carrinho(request, detalhe_pedido_id):
    detalhe_pedido = get_object_or_404(DetalhePedido, id=detalhe_pedido_id, pedido__cliente=request.user, pedido__status_pedido=0)
    detalhe_pedido.delete()
    return redirect('kiosk_app:carrinho') 


@login_required
def finalizar_pedido(request):
    servico_checkout = ServicoCheckout(request.user)
    pedido = servico_checkout.obter_carrinho_ativo()
    
    # Valida o carrinho
    carrinho_valido, erro_carrinho = servico_checkout.validar_carrinho(pedido)
    if not carrinho_valido:
        return redirect('kiosk_app:cardapio')

    if request.method == 'POST':
        # Obtém os dados do formulário
        local_consumo = request.POST.get('local_consumo')
        metodo_pagamento = request.POST.get('metodo_pagamento')

        # Valida os dados do formulário
        dados_validos, mensagem_erro = servico_checkout.validar_dados_checkout(
            local_consumo, 
            metodo_pagamento
        )

        if dados_validos:
            # Processa o checkout
            servico_checkout.processar_checkout(pedido, local_consumo, metodo_pagamento)
            return redirect('kiosk_app:pedido_confirmado', pedido_id=pedido.id)
        else:
            # Retorna o formulário com a mensagem de erro
            return render(request, 'kiosk_app/finalizar_pedido.html', {
                'pedido': pedido,
                'mensagem_erro': mensagem_erro
            })

    # Requisição GET: renderiza o formulário de checkout
    return render(request, 'kiosk_app/finalizar_pedido.html', {'pedido': pedido})


@login_required
def pedido_confirmado(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    return render(request, 'kiosk_app/pedido_confirmado.html', {'pedido': pedido})        


def is_cozinheiro(user):
    return user.papel == 'cozinheiro'


@login_required
@user_passes_test(is_cozinheiro)
def cozinheiro_pedido_fila_view(request):
    """
    Display orders queue for cozinheiro, prioritized by waiting time.
    Only shows pending and in-preparation orders.
    """
    # Calculate waiting time for each order
    pedidos = Pedido.objects.filter(
        status_pedido__in=[1, 2]  # Pending or In Preparation
    ).annotate(
        waiting_time=ExpressionWrapper(
            timezone.now() - F('data_pedido'),
            output_field=DurationField()
        )
    ).order_by('status_pedido', 'data_pedido')

    context = {
        'pedidos': pedidos,
        'status_map': dict(Pedido.OPCOES_STATUS)
    }
    return render(request, 'kiosk_app/cozinha/fila_pedidos.html', context)


@login_required
@user_passes_test(is_cozinheiro)
def cozinheiro_alterar_pedido(request, pedido_id):
    """
    Update order status (In Preparation -> Ready)
    """
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        novo_status = int(request.POST.get('novo_status'))
        
        # Validate status transition
        if novo_status in [2, 3]:  # Only allow transitions to 'In Preparation' or 'Ready'
            if novo_status == 3:
                pedido.data_conclusao = timezone.now()
            pedido.status_pedido = novo_status
            pedido.save()
            messages.success(request, f'Status do pedido {pedido.id} atualizado com sucesso.')
        else:
            messages.error(request, 'Transição de status inválida.')
            
    return redirect('kiosk_app:cozinheiro_pedidos')


@login_required
@user_passes_test(is_cozinheiro)
def cozinheiro_pedido_historico_view(request):
    """
    Exibe o histórico de pedidos concluídos nas últimas 24 horas.
    """
    # Define o período de 24 horas
    data_inicio = timezone.now() - timezone.timedelta(days=1)
    data_fim = timezone.now()
    
    # Filtra pedidos concluídos nas últimas 24 horas
    pedidos_completados = Pedido.objects.filter(
        status_pedido=3,  # Status "Pronto"
        data_pedido__range=(data_inicio, data_fim)
    ).order_by('-data_pedido')

    context = {
        'pedidos': pedidos_completados
    }
    return render(request, 'kiosk_app/cozinha/historico_pedidos.html', context)    