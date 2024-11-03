from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistroClienteForm, LoginForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout

def registrar_cliente(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('kiosk_app:cardapio')
    else:
        form = RegistroClienteForm()
    return render(request, 'users/registrar_cliente.html', {'form': form})


class LoginUsuarioView(LoginView):
    template_name = 'users/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True  # Redireciona se já estiver logado
    success_url = reverse_lazy('kiosk_app:cardapio')  


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('kiosk_app:cardapio'))
