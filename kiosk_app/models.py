from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    PAPEL_USUARIO = (
        ('cliente', 'Cliente'),
        ('admin', 'Administrador'),
        ('cozinheiro', 'Cozinheiro'),
    )
    papel_usuario = models.CharField(max_length=50, choices=PAPEL_USUARIO)
    

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_set',  # Set a unique related_name
        blank=True
    )
    
    # Change the permissions field
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_permissions_set',  # Ensure this also has a unique related_name
        blank=True
    )


class Categoria(models.Model):
    nome_categoria = models.CharField(max_length=100)

    def __str__(self):
        return self.nome_categoria

class Item(models.Model):
    nome_item = models.CharField(max_length=100)
    preco_item = models.FloatField()
    descricao = models.CharField(max_length=100)
    tempo_prep = models.IntegerField()
    imagem_item = models.ImageField(upload_to='itens/', null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome_item

class Pedido(models.Model):
    OPCOES_STATUS = (
        (0, 'Pendente'),
        (1, 'Em Preparação'),
        (2, 'Pronto'),
        (3, 'Cancelado'),
    )
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    local_consumo = models.CharField(max_length=15)
    metodo_pagamento = models.CharField(max_length=30)
    status_pedido = models.IntegerField(choices=OPCOES_STATUS, default=0)
    data_pedido = models.DateTimeField(auto_now_add=True)

class DetalhePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantidade_item = models.PositiveIntegerField()
    obs_item = models.CharField(max_length=50, null=True, blank=True)
    tamanho_item = models.CharField(max_length=10, null=True, blank=True)
    preco_item_pedido = models.FloatField()
