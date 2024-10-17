from django.contrib import admin
from .models import Categoria, Item, Pedido, DetalhePedido

admin.site.register(Categoria)
admin.site.register(Item)
admin.site.register(Pedido)
admin.site.register(DetalhePedido)
