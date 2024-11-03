from django.contrib import admin
from .models import Categoria, Item, Ingrediente, TamanhoItem, Pedido, Promocao

admin.site.register(Categoria)
admin.site.register(Ingrediente)
admin.site.register(Item)
admin.site.register(TamanhoItem)
admin.site.register(Pedido)
admin.site.register(Promocao)
# admin.site.register(DetalhePedido)


