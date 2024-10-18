from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'papel', 'is_staff')
    list_filter = ('papel', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Papel', {'fields': ('papel',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Papel', {'fields': ('papel',)}),
    )

admin.site.register(Usuario, UsuarioAdmin)
