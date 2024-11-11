from django.shortcuts import render, redirect, get_object_or_404
from .models import (Categoria, Ingrediente, Item, Promocao, Sabor, Pedido, DetalhePedido,
    TamanhoItem, TamanhoDecorator, PromocaoDecorator, IngredienteExtraDecorator)
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count


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

def pedido_resumo_view(request):
    # Confirmação do pedido
    pass


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
    
        item_id = request.POST.get('item_id')
        tamanho_item_id = request.POST.get('tamanho_item_id')
        sabor_id = request.POST.get('sabor_id') 
        ingredientes_extras_ids = request.POST.getlist('ingredientes_extras')

        item = get_object_or_404(Item, id=item_id)
        tamanho_item = None
        if tamanho_item_id:
            tamanho_item = get_object_or_404(TamanhoItem, id=tamanho_item_id, item=item)
        sabor = None
        if sabor_id:
            sabor = get_object_or_404(Sabor, id=sabor_id)
            if not item.sabores.filter(id=sabor.id).exists():
                sabor = None

        ingredientes_extras_validos = item.ingredientes_extras.filter(id__in=ingredientes_extras_ids)

        pedido, created = Pedido.objects.get_or_create(cliente=request.user, status_pedido=0)

        current_date = timezone.now().date()
        promocao = item.id_promocao if item.id_promocao and item.id_promocao.data_inicio <= current_date <= item.id_promocao.data_fim else None

        detalhe_pedido_queryset = DetalhePedido.objects.filter(
            pedido=pedido,
            item=item,
            tamanho_item=tamanho_item,
            promocao=promocao,
            sabor=sabor  
        )

        detalhe_pedido = None
        for dp in detalhe_pedido_queryset:
            ingredientes_existentes = set(dp.ingredientes_extras.all())
            ingredientes_selecionados = set(ingredientes_extras_validos)
            if ingredientes_existentes == ingredientes_selecionados:
                detalhe_pedido = dp
                break

        if detalhe_pedido:
            detalhe_pedido.quantidade_item += 1
            detalhe_pedido.save()
        else:
            detalhe_pedido = DetalhePedido.objects.create(
                pedido=pedido,
                item=item,
                tamanho_item=tamanho_item,
                sabor=sabor,  
                promocao=promocao,
                quantidade_item=1,
            )
            detalhe_pedido.ingredientes_extras.set(ingredientes_extras_validos)

        return redirect('kiosk_app:carrinho')
    else:
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
    # Get the user's current cart (Pedido with status 'Carrinho')
    pedido = Pedido.objects.filter(cliente=request.user, status_pedido=0).first()
    
    if not pedido:
        # If no cart exists, redirect to the menu
        return redirect('kiosk_app:cardapio')
    else:
        # Check if the cart has items
        if not pedido.itens.exists():
            # If the cart is empty, redirect to the menu
            return redirect('kiosk_app:cardapio')

    if request.method == 'POST':
        # Process the form data
        local_consumo = request.POST.get('local_consumo')
        metodo_pagamento = request.POST.get('metodo_pagamento')

        # Validate the form data
        if local_consumo and metodo_pagamento:
            # Update the pedido with the provided information
            pedido.local_consumo = local_consumo
            pedido.metodo_pagamento = metodo_pagamento
            pedido.status_pedido = 1  # Update status to 'Pendente'
            pedido.save()

            # Redirect to the order confirmation page
            return redirect('kiosk_app:pedido_confirmado', pedido_id=pedido.id)
        else:
            # If data is missing, render the form again with an error message
            error_message = 'Por favor, preencha todos os campos.'
            return render(request, 'kiosk_app/finalizar_pedido.html', {'pedido': pedido, 'error_message': error_message})
    else:
        # GET request: render the checkout form
        return render(request, 'kiosk_app/finalizar_pedido.html', {'pedido': pedido})


@login_required
def pedido_confirmado(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    return render(request, 'kiosk_app/pedido_confirmado.html', {'pedido': pedido})        