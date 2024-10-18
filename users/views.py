from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistroClienteForm, LoginForm
from django.contrib.auth.views import LoginView

def registrar_cliente(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('home')
    else:
        form = RegistroClienteForm()
    return render(request, 'users/registrar_cliente.html', {'form': form})


class LoginUsuarioView(LoginView):
    template_name = 'users/login.html'
    authentication_form = LoginForm




