from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class Categoria(models.Model):
    nome_categoria = models.CharField(max_length=100)

    def __str__(self):
        return self.nome_categoria


class Ingrediente(models.Model):
    nome = models.CharField(max_length=100)
    valor_nutricional = models.PositiveIntegerField(blank=True)
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
    nome = models.CharField(max_length=255)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    desconto = models.FloatField()

    def __str__(self):
        return self.nome

    @property    
    def is_ativa(self) -> bool:
        hoje = timezone.now().date()
        return self.data_inicio <= hoje <= self.data_fim    

    def clean(self):
        if self.data_fim <= self.data_inicio:
            raise ValidationError("Data fim deve ser posterior à data início.")
        if not (0 <= self.desconto <= 100):
            raise ValidationError("Desconto deve estar entre 0% e 100%.")

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
    preco_base = models.FloatField()
    ingredientes_extras = models.ManyToManyField(Ingrediente, related_name='itens_extras', blank=True)
    sabores = models.ManyToManyField(Sabor, related_name='itens', blank=True)

    def calcular_preco(self) -> float:
        return self.preco_base

    def __str__(self):
        return self.nome_item

    def clean(self):
        if self.preco_base < 0:
            raise ValidationError("O preço base não pode ser negativo.")

    class Meta:
        verbose_name_plural = 'itens'


class TamanhoItem(models.Model):
    item = models.ForeignKey(Item, related_name='tamanhos', on_delete=models.CASCADE)
    tamanho = models.CharField(max_length=10)  # Ex. 'P', 'M', 'G'
    preco = models.FloatField()

    def __str__(self):
        return f"{self.item.nome_item} - {self.tamanho} ({self.preco})"

    def clean(self):
        if self.preco < 0:
            raise ValidationError("O preço não pode ser negativo.")

    class Meta:
        unique_together = ('item', 'tamanho')
        verbose_name_plural = 'Tamanhos do Item'



class ItemDecorator:
    def __init__(self, item):
        self._item = item

    def calcular_preco(self) -> float:
        return self._item.calcular_preco()

    def __getattr__(self, name):
        return getattr(self._item, name)


class TamanhoDecorator(ItemDecorator):
    def __init__(self, item, tamanho_item):
        super().__init__(item)
        self.tamanho_item = tamanho_item

    def calcular_preco(self) -> float:
        return self.tamanho_item.preco


class PromocaoDecorator(ItemDecorator):
    def __init__(self, item, promocao):
        super().__init__(item)
        self.promocao = promocao

    def calcular_preco(self) -> float:
        preco_atual = self._item.calcular_preco()
        desconto = self.promocao.desconto
        preco_descontado = preco_atual * (1 - desconto / 100)
        return preco_descontado


class SaborDecorator(ItemDecorator):
    def __init__(self, item, sabor):
        super().__init__(item)
        self.sabor = sabor

    def get_nome(self) -> str:
        return f"{self._item.nome_item} - {self.sabor.nome}"

    def calcular_preco(self) -> float:
        return self._item.calcular_preco() + self.sabor.preco_adicional


class IngredienteExtraDecorator(ItemDecorator):
    def __init__(self, item, ingrediente_extra):
        super().__init__(item)
        self.ingrediente_extra = ingrediente_extra

    def calcular_preco(self) -> float:
        return self._item.calcular_preco() + self.ingrediente_extra.custo

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
    data_conclusao = models.DateTimeField(null=True, blank=True)

    def get_total(self) -> float:
        total = sum([item.get_subtotal() for item in self.itens.all()])
        return total

    @property
    def tempo_espera(self) -> timedelta:
        """Calcula o tempo de espera desde a criação do pedido"""
        agora = timezone.now()
        return agora - self.data_pedido   

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.username}"


# class ServicoDecorator:
#     @staticmethod
#     def create_decorated_item(detalhe_pedido: 'DetalhePedido') -> ItemDecorator:
#         decorated_item = detalhe_pedido.item
#         if detalhe_pedido.tamanho_item:
#             decorated_item = TamanhoDecorator(decorated_item, detalhe_pedido.tamanho_item)
#         if detalhe_pedido.promocao_ativa:
#             decorated_item = PromocaoDecorator(decorated_item, detalhe_pedido.promocao)
#         if detalhe_pedido.sabor:
#             decorated_item = SaborDecorator(decorated_item, detalhe_pedido.sabor)
#         for ingrediente in detalhe_pedido.ingredientes_extras.all():
#             decorated_item = IngredienteExtraDecorator(decorated_item, ingrediente)
#         return decorated_item


class ServicoDecorator:
    def __init__(self, detalhe_pedido: 'DetalhePedido'):
        self.detalhe_pedido = detalhe_pedido

    def aplicar_decorators(self) -> ItemDecorator:
        item = self.detalhe_pedido.item
        item = self.aplicar_tamanho(item)
        item = self.aplicar_promocao(item)
        item = self.aplicar_sabor(item)
        item = self.aplicar_ingredientes_extras(item)
        return item

    def aplicar_tamanho(self, item: ItemDecorator) -> ItemDecorator:
        if self.detalhe_pedido.tamanho_item:
            return TamanhoDecorator(item, self.detalhe_pedido.tamanho_item)
        return item

    def aplicar_promocao(self, item: ItemDecorator) -> ItemDecorator:
        if self.detalhe_pedido.promocao_ativa:
            return PromocaoDecorator(item, self.detalhe_pedido.promocao)
        return item

    def aplicar_sabor(self, item: ItemDecorator) -> ItemDecorator:
        if self.detalhe_pedido.sabor:
            return SaborDecorator(item, self.detalhe_pedido.sabor)
        return item

    def aplicar_ingredientes_extras(self, item: ItemDecorator) -> ItemDecorator:
        for ingrediente in self.detalhe_pedido.ingredientes_extras.all():
            item = IngredienteExtraDecorator(item, ingrediente)
        return item


class DetalhePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantidade_item = models.PositiveIntegerField()
    tamanho_item = models.ForeignKey(TamanhoItem, on_delete=models.CASCADE, null=True, blank=True)
    promocao = models.ForeignKey(Promocao, on_delete=models.SET_NULL, null=True, blank=True)
    ingredientes_extras = models.ManyToManyField(Ingrediente, related_name='detalhe_pedido', blank=True)
    obs_item = models.CharField(max_length=50, null=True, blank=True)
    sabor = models.ForeignKey(Sabor, on_delete=models.SET_NULL, null=True, blank=True)

    def get_decorated_item(self) -> ItemDecorator:
        # return ServicoDecorator.create_decorated_item(self)
        servico = ServicoDecorator(self)
        return servico.aplicar_decorators()

    def get_subtotal(self) -> float:
        decorated_item = self.get_decorated_item()
        return decorated_item.calcular_preco() * self.quantidade_item

    @property
    def promocao_ativa(self):
        return self.promocao.is_ativa if self.promocao else False    

    def __str__(self):
        size_info = f" ({self.tamanho_item.tamanho})" if self.tamanho_item else ""
        return f"{self.quantidade_item} x {self.item.nome_item}{size_info}"

    def clean(self):
        if self.quantidade_item <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")
