from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Item, TamanhoItem, Sabor, Pedido, DetalhePedido

class ItemCarrinho:
    """Detalhes do item do carrinho"""
    def __init__(self, item_id, tamanho_item_id=None, sabor_id=None, ingredientes_extras_ids=None):
        self.item_id = item_id
        self.tamanho_item_id = tamanho_item_id
        self.sabor_id = sabor_id
        self.ingredientes_extras_ids = ingredientes_extras_ids or []


class ValidadorItemCarrinho:
    """Valida componentes do item do carrinho"""
    @staticmethod
    def validar_item(item_id):
        return get_object_or_404(Item, id=item_id)

    @staticmethod
    def validar_tamanho(item, tamanho_item_id):
        if not tamanho_item_id:
            return None
        return get_object_or_404(TamanhoItem, id=tamanho_item_id, item=item)

    @staticmethod
    def validar_sabor(item, sabor_id):
        if not sabor_id:
            return None
        sabor = get_object_or_404(Sabor, id=sabor_id)
        return sabor if item.sabores.filter(id=sabor.id).exists() else None

    @staticmethod
    def validar_ingredientes_extras(item, ingredientes_extras_ids):
        return item.ingredientes_extras.filter(id__in=ingredientes_extras_ids)


class GerenciadorPromocao:
    """Gerencia a validação e aplicação de promoções"""
    @staticmethod
    def obter_promocao_valida(item):
        data_atual = timezone.now().date()
        if item.id_promocao and item.id_promocao.is_ativa:
            return item.id_promocao
        return None


class ComparadorDetalhePedido:
    """Encontra detalhes do pedido existentes com base nas características do item"""
    @staticmethod
    def encontrar_detalhe_compatível(pedido, item, tamanho_item, promocao, sabor, ingredientes_extras):
        queryset_detalhe_pedido = DetalhePedido.objects.filter(
            pedido=pedido,
            item=item,
            tamanho_item=tamanho_item,
            promocao=promocao,
            sabor=sabor
        )

        for dp in queryset_detalhe_pedido:
            ingredientes_existentes = set(dp.ingredientes_extras.all())
            ingredientes_selecionados = set(ingredientes_extras)
            if ingredientes_existentes == ingredientes_selecionados:
                return dp
        return None


class GerenciadorCarrinho:
    """Gerencia as operações do carrinho"""
    def __init__(self, usuario):
        self.usuario = usuario
        self.validador = ValidadorItemCarrinho()
        self.gerenciador_promocao = GerenciadorPromocao()
        self.comparador_detalhe = ComparadorDetalhePedido()

    def obter_ou_criar_carrinho(self):
        return Pedido.objects.get_or_create(
            cliente=self.usuario,
            status_pedido=0
        )[0]

    def adicionar_item(self, item_carrinho):
        # Validar componentes
        item = self.validador.validar_item(item_carrinho.item_id)
        tamanho_item = self.validador.validar_tamanho(item, item_carrinho.tamanho_item_id)
        sabor = self.validador.validar_sabor(item, item_carrinho.sabor_id)
        ingredientes_extras = self.validador.validar_ingredientes_extras(
            item, 
            item_carrinho.ingredientes_extras_ids
        )

        # Obter ou criar carrinho
        pedido = self.obter_ou_criar_carrinho()

        # Verificar promoção válida
        promocao = self.gerenciador_promocao.obter_promocao_valida(item)

        # Tentar encontrar um detalhe de pedido compatível
        detalhe_pedido = self.comparador_detalhe.encontrar_detalhe_compatível(
            pedido, item, tamanho_item, promocao, sabor, ingredientes_extras
        )

        if detalhe_pedido:
            self._atualizar_item_existente(detalhe_pedido)
        else:
            try:
                self._criar_novo_item(
                    pedido, item, tamanho_item, promocao, 
                    sabor, ingredientes_extras
                )
            except ValidationError as e:
                print(f"Erro ao criar item no carrinho: {e.message_dict}")
                raise  

    def _atualizar_item_existente(self, detalhe_pedido):
        detalhe_pedido.quantidade_item += 1
        detalhe_pedido.save()

    def _criar_novo_item(self, pedido, item, tamanho_item, promocao, sabor, ingredientes_extras):
        detalhe_pedido = DetalhePedido.objects.create(
            pedido=pedido,
            item=item,
            tamanho_item=tamanho_item,
            sabor=sabor,
            promocao=promocao,
            quantidade_item=1
        )

        detalhe_pedido.full_clean()  # Invoca o método clean() do modelo
        detalhe_pedido.save()
        detalhe_pedido.ingredientes_extras.set(ingredientes_extras)

    
      
