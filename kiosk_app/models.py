from django.db import models
from django.conf import settings
from abc import ABC, abstractmethod


class Categoria(models.Model):
    nome_categoria = models.CharField(max_length=100)

    def __str__(self):
        return self.nome_categoria


class Ingrediente(models.Model):
    nome = models.CharField(max_length=100)
    valor_nutricional = models.PositiveIntegerField(blank=True)  # Informação nutricional
    custo = models.FloatField(default=3.00)

    def __str__(self):
        return self.nome


class Sabor(models.Model):
    nome = models.CharField(max_length=50)
    preco_adicional = models.FloatField(default=0.0)  

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = 'sabores'    


class Promocao(models.Model):
    nome = models.CharField(max_length=255, null=False)
    data_inicio = models.DateField(null=False)
    data_fim = models.DateField(null=False)
    desconto = models.FloatField(null=False)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = 'promoções'      


class Item(models.Model):
    nome_item = models.CharField(max_length=100)
    descricao = models.CharField(max_length=100)
    tempo_prep = models.IntegerField()
    imagem_item = models.ImageField(upload_to='itens/', null=True, blank=True)
    id_categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    id_promocao = models.ForeignKey(Promocao, on_delete=models.SET_NULL, null=True, blank=True)
    ingredientes = models.ManyToManyField(Ingrediente, related_name='itens', blank=True)
    preco_base = models.FloatField(null=False)
    ingredientes_extras = models.ManyToManyField(Ingrediente, related_name='itens_extras', blank=True)
    sabores = models.ManyToManyField(Sabor, related_name='itens', blank=True)  

    def get_preco(self):
        return self.preco_base

    def __str__(self):
        return self.nome_item

    class Meta:
        verbose_name_plural = 'itens'


class TamanhoItem(models.Model):
    item = models.ForeignKey(Item, related_name='tamanhos', on_delete=models.CASCADE)
    tamanho = models.CharField(max_length=10)  # Ex. 'P', 'M', 'G'
    preco = models.FloatField()

    def __str__(self):
        return f"{self.item.nome_item} - {self.tamanho} ({self.preco})"

    class Meta:
        unique_together = ('item', 'tamanho')
        verbose_name_plural = 'Tamanhos do Item'


class ItemDecorator(ABC):
    def __init__(self, item):
        self._item = item

    @abstractmethod
    def get_preco(self):
        pass

    def __getattr__(self, name):
        return getattr(self._item, name)


class TamanhoDecorator(ItemDecorator):
    def __init__(self, item, tamanho_item):
        super().__init__(item)
        self.tamanho_item = tamanho_item 

    def get_preco(self):
        return self.tamanho_item.preco


class PromocaoDecorator(ItemDecorator):
    def __init__(self, item, promocao):
        super().__init__(item)
        self.promocao = promocao

    def get_preco(self):
        desconto = self.promocao.desconto
        preco_atual = self._item.get_preco()
        preco_descontado = preco_atual - (preco_atual * (desconto / 100))
        return preco_descontado


class SaborDecorator(ItemDecorator):
    def __init__(self, item, sabor):
        super().__init__(item)
        self.sabor = sabor

    def get_nome(self):
        return f"{self._item.get_nome()} - {self.sabor.nome}"

    def get_preco(self):
        return self._item.get_preco() + self.sabor.preco_adicional


class IngredienteExtraDecorator(ItemDecorator):
    def __init__(self, item, ingrediente_extra):
        super().__init__(item)
        self.ingrediente_extra = ingrediente_extra

    def get_preco(self):
        return self._item.get_preco() + self.ingrediente_extra.custo

    def get_ingredientes(self):
        return self._item.ingredientes.all() | Ingrediente.objects.filter(id=self.ingrediente_extra.id)


class Pedido(models.Model):
    OPCOES_STATUS = (
        (0, 'Carrinho'),
        (1, 'Pendente'),
        (2, 'Em Preparação'),
        (3, 'Pronto'),
        (4, 'Cancelado'),
    )
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    local_consumo = models.CharField(max_length=15, null=True, blank=True)  
    metodo_pagamento = models.CharField(max_length=30, null=True, blank=True)  
    status_pedido = models.IntegerField(choices=OPCOES_STATUS, default=0)
    data_pedido = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        total = sum([item.get_subtotal() for item in self.itens.all()])
        return total

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.username}"


class DetalhePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantidade_item = models.PositiveIntegerField()
    tamanho_item = models.ForeignKey(TamanhoItem, on_delete=models.CASCADE, null=True, blank=True)
    promocao = models.ForeignKey(Promocao, on_delete=models.SET_NULL, null=True, blank=True)
    ingredientes_extras = models.ManyToManyField(Ingrediente, related_name='detalhe_pedido', blank=True)
    obs_item = models.CharField(max_length=50, null=True, blank=True)
    sabor = models.ForeignKey(Sabor, on_delete=models.SET_NULL, null=True, blank=True)
    
    def get_decorated_item(self):
        decorated_item = self.item
        if self.tamanho_item:
            decorated_item = TamanhoDecorator(decorated_item, self.tamanho_item)
        if self.promocao:
            decorated_item = PromocaoDecorator(decorated_item, self.promocao)
        if self.sabor:
            decorated_item = SaborDecorator(decorated_item, self.sabor)    
        for ingrediente in self.ingredientes_extras.all():
            decorated_item = IngredienteExtraDecorator(decorated_item, ingrediente)
        return decorated_item

    def get_subtotal(self):
        decorated_item = self.get_decorated_item()
        return decorated_item.get_preco() * self.quantidade_item

    def __str__(self):
        size_info = f" ({self.tamanho_item.tamanho})" if self.tamanho_item else ""
        return f"{self.quantidade_item} x {self.item.nome_item}{size_info}"

    # class Meta:
    #     unique_together = ('pedido', 'item', 'tamanho_item')

