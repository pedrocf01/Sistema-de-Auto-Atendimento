from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario

class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(required=True)
    cpf = forms.CharField(max_length=14, required=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'cpf', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.papel = 'cliente'
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuário', max_length=254)
    password = forms.CharField(label='Senha', strip=False, widget=forms.PasswordInput)
