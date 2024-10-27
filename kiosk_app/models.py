from django.db import models
from django.conf import settings
# from django.contrib.auth.models import AbstractUser

# class Usuario(AbstractUser):
#     PAPEL_USUARIO = (
#         ('cliente', 'Cliente'),
#         ('admin', 'Administrador'),
#         ('cozinheiro', 'Cozinheiro'),
#     )
#     papel_usuario = models.CharField(max_length=50, choices=PAPEL_USUARIO)
    

#     groups = models.ManyToManyField(
#         'auth.Group',
#         related_name='usuario_set',  # Set a unique related_name
#         blank=True
#     )
    
#     # Change the permissions field
#     user_permissions = models.ManyToManyField(
#         'auth.Permission',
#         related_name='usuario_permissions_set',  # Ensure this also has a unique related_name
#         blank=True
#     )


class Categoria(models.Model):
    nome_categoria = models.CharField(max_length=100)

    def __str__(self):
        return self.nome_categoria


class Promocao(models.Model):
    nome = models.CharField(max_length=255, null=False)
    data_inicio = models.DateField(null=False)
    data_fim = models.DateField(null=False)
    desconto = models.FloatField(null=False)

    def __str__(self):
        return self.nome  


class Item(models.Model):
    nome_item = models.CharField(max_length=100)
    descricao = models.CharField(max_length=100)
    tempo_prep = models.IntegerField()
    imagem_item = models.ImageField(upload_to='itens/', null=True, blank=True)
    id_categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    id_promocao = models.ForeignKey(Promocao, on_delete=models.SET_NULL, null=True, blank=True)
    ingredientes = models.ManyToManyField('Ingrediente', related_name='itens', blank=True)

    def __str__(self):
        return self.nome_item


class Ingrediente(models.Model):
    nome = models.CharField(max_length=100)
    valor_nutricional = models.PositiveIntegerField(blank=True)  # Informação nutricional

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    OPCOES_STATUS = (
        (0, 'Pendente'),
        (1, 'Em Preparação'),
        (2, 'Pronto'),
        (3, 'Cancelado'),
    )
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    local_consumo = models.CharField(max_length=15, null=False)
    metodo_pagamento = models.CharField(max_length=30, null=False)
    status_pedido = models.IntegerField(choices=OPCOES_STATUS, default=0)
    data_pedido = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.username}"


class TamanhoItem(models.Model):
    id_item = models.ForeignKey(Item, on_delete=models.CASCADE)
    tamanho = models.CharField(max_length=10, null=False)  # Ex: 'P', 'M', 'G'
    preco = models.FloatField(null=False)

    class Meta:
        unique_together = ('id_item', 'tamanho')


class DetalhePedido(models.Model):
    id_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    id_item = models.ForeignKey(TamanhoItem, on_delete=models.CASCADE)
    quantidade_item = models.PositiveIntegerField(null=False)
    obs_item = models.CharField(max_length=50, null=True, blank=True)
    preco_item_pedido = models.FloatField()

    class Meta:
        unique_together = ('id_pedido', 'id_item')
