from django.contrib import admin
from .models import Categoria, Item, Ingrediente, TamanhoItem, Pedido, Promocao, DetalhePedido, Sabor

class ItemAdmin(admin.ModelAdmin):
    list_display = ('nome_item', 'id_categoria', 'preco_base')
    filter_horizontal = ('ingredientes', 'ingredientes_extras')  

admin.site.register(Item, ItemAdmin)
admin.site.register(Categoria)
admin.site.register(Ingrediente)
admin.site.register(Sabor)
admin.site.register(TamanhoItem)
admin.site.register(Pedido)
admin.site.register(Promocao)



