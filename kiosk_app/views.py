from django.shortcuts import render
from .models import Categoria, Item

def cardapio_view(request):
    categorias = Categoria.objects.all()
    itens = Item.objects.all()
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


def carrinho_view(request):
    # Assume cart is stored in session
    carrinho = request.session.get('carrinho', {})
    itens = Item.objects.filter(id__in=carrinho.keys())
    total = sum(item.preco_item * carrinho[str(item.id)] for item in itens)
    context = {
        'itens': itens,
        'carrinho': carrinho,
        'total': total,
    }
    return render(request, 'carrinho.html', context)


def pedido_resumo_view(request):
    # Similar to cart_view but confirms the order
    # Handle order creation and redirection after confirmation
    pass


def pedido_rastreio_view(request):
    pedidos = Pedido.objects.filter(customer=request.user)
    context = {
        'pedidos': pedidos,
    }
    return render(request, 'pedidos_rastreio.html', context)


def add_carrinho(request, item_id):
    # Fetch the item being added to the cart
    item = get_object_or_404(Item, id=item_id)

    # Get the cart from the session, or create an empty one if not exists
    carrinho = request.session.get('carrinho', {})

    # Get the quantity from the POST request (default to 1)
    qtd= int(request.POST.get('quantidade', 1))
    
    # Check if the item is already in the cart
    if str(item_id) in carrinho:
        # If the item is already in the cart, update its quantity
        carrinho[str(item_id)]['quantidade'] += qtd
    else:
        # Otherwise, add the item to the cart
        carrinho[str(item_id)] = {
            'quantidade': qtd,
            'preco': str(item.preco_item),  # Save the price in case it changes later
            'nome': item.nome_item,
        }

    # Save the updated cart in the session
    request.session['carrinho'] = carrinho

    # Optionally, add a message (e.g., using Django's messages framework)
    # messages.success(request, f'Added {quantity} {item.item_name}(s) to your cart.')

    # Redirect to another page (e.g., the cart view or the menu)
    return redirect('cardapio')  # Adjust the redirect as needed
                