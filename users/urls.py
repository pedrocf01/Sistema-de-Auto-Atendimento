from django.urls import path
from .views import registrar_cliente, LoginUsuarioView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('registrar/', registrar_cliente, name='registrar_cliente'),
    path('login/', LoginUsuarioView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]