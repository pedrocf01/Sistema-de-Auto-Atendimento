from django.shortcuts import get_object_or_404
from typing import Optional, Tuple
from .models import Pedido

class ServicoCheckout:
    def __init__(self, usuario):
        self.usuario = usuario

    def obter_carrinho_ativo(self) -> Optional[Pedido]:
        """Recupera o carrinho ativo do usuário (Pedido com status 'Carrinho')"""
        return Pedido.objects.filter(
            cliente=self.usuario,
            status_pedido=0
        ).first()

    def validar_carrinho(self, pedido: Optional[Pedido]) -> Tuple[bool, Optional[str]]:
        """Valida se o carrinho existe e possui itens"""
        if not pedido:
            return False, "Carrinho não encontrado."
        if not pedido.itens.exists():
            return False, "Carrinho está vazio."
        return True, None

    def validar_dados_checkout(self, local_consumo: str, metodo_pagamento: str) -> Tuple[bool, Optional[str]]:
        """Valida os dados do formulário de checkout"""
        if not local_consumo or not metodo_pagamento:
            return False, "Por favor, preencha todos os campos."
        return True, None

    def processar_checkout(self, pedido: Pedido, local_consumo: str, metodo_pagamento: str) -> None:
        """Processa o checkout atualizando o pedido com as informações fornecidas"""
        pedido.local_consumo = local_consumo
        pedido.metodo_pagamento = metodo_pagamento
        pedido.status_pedido = 1  # Atualiza o status para 'Pendente'
        pedido.save()