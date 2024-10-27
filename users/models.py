from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('cliente', 'Cliente'),
        ('administrador', 'Administrador'),
        ('cozinheiro', 'Cozinheiro'),
    )
    papel = models.CharField(max_length=20, choices=ROLES, default='cliente')
    cpf = models.CharField(max_length=14, unique=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_papel_display()})"
