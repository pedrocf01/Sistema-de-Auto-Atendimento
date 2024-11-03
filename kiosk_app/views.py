from django.shortcuts import render, redirect, get_object_or_404
from .models import Categoria, Item, TamanhoItem, Pedido, DetalhePedido, Carrinho
from django.contrib.auth.decorators import login_required

def cardapio_view(request):
    categorias = Categoria.objects.all()
    itens = Item.objects.all()
    tam_itens = TamanhoItem.objects.all()
    context = {
        'categorias': categorias,
        'itens': itens,
        'tam_itens': tam_itens
    }
    return render(request, 'kiosk_app/cardapio.html', context)


def item_detalhe_view(request, item_id):
    item = Item.objects.get(id=item_id)
    context = {
        'item': item,
    }
    return render(request, 'item_detalhe.html', context)


def pedido_resumo_view(request):
    # Similar to cart_view but confirms the order
    # Handle order creation and redirection after confirmation
    pass


@login_required
def pedido_rastreio_view(request):
    pedidos = Pedido.objects.filter(cliente=request.user)
    context = {
        'pedidos': pedidos,
    }
    return render(request, 'pedidos_rastreio.html', context)


@login_required
def adicionar_ao_carrinho(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        tamanho_item_id = request.POST.get('tamanho_item_id')

        item = get_object_or_404(Item, id=item_id)
        tamanho_item = get_object_or_404(TamanhoItem, id=tamanho_item_id, id_item=item)

        # Obter ou criar o pedido com status 'carrinho' para o usuário atual
        pedido, created = Pedido.objects.get_or_create(cliente=request.user, status_pedido=0)

        # Tentar obter o DetalhePedido para este tamanho de item
        detalhe_pedido, created = DetalhePedido.objects.get_or_create(
            pedido=pedido,
            id_item=tamanho_item,
            defaults={'quantidade_item': 1}
        )
        if not created:
            detalhe_pedido.quantidade_item += 1
            detalhe_pedido.save()

        return redirect('kiosk_app:carrinho')
    else:
        return redirect('kiosk_app:cardapio')



@login_required
def carrinho_view(request):
    pedido = Pedido.objects.filter(cliente=request.user, status_pedido=0).first()
    itens_pedido = pedido.itens.all() if pedido else []
    total = pedido.get_total() if pedido else 0.00
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
    return redirect('carrinho')


@login_required
def remover_item_carrinho(request, detalhe_pedido_id):
    detalhe_pedido = get_object_or_404(DetalhePedido, id=detalhe_pedido_id, pedido__cliente=request.user, pedido__status_pedido=0)
    detalhe_pedido.delete()
    return redirect('carrinho') 

# def add_carrinho(request, item_id):
#     # Fetch the item being added to the cart
#     item = get_object_or_404(Item, id=item_id)

#     # Get the cart from the session, or create an empty one if not exists
#     carrinho = request.session.get('carrinho', {})

#     # Get the quantity from the POST request (default to 1)
#     qtd= int(request.POST.get('quantidade', 1))
    
#     # Check if the item is already in the cart
#     if str(item_id) in carrinho:
#         # If the item is already in the cart, update its quantity
#         carrinho[str(item_id)]['quantidade'] += qtd
#     else:
#         # Otherwise, add the item to the cart
#         carrinho[str(item_id)] = {
#             'quantidade': qtd,
#             'preco': str(item.preco_item),  # Save the price in case it changes later
#             'nome': item.nome_item,
#         }

#     # Save the updated cart in the session
#     request.session['carrinho'] = carrinho

#     # Optionally, add a message (e.g., using Django's messages framework) messages.success(request, f'Added {quantity} {item.item_name}(s) to your cart.')

#     # Redirect to another page (e.g., the cart view or the menu)
#     return redirect('cardapio')  # Adjust the redirect as needed
                

# def carrinho_view(request):
#     # Assume cart is stored in session
#     carrinho = request.session.get('carrinho', {})
#     itens = Item.objects.filter(id__in=carrinho.keys())
#     total = sum(item.preco_item * carrinho[str(item.id)] for item in itens)
#     context = {
#         'itens': itens,
#         'carrinho': carrinho,
#         'total': total,
#     }
#     return render(request, 'carrinho.html', context)                
