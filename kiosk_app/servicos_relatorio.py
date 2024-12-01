from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg, F, DecimalField
from django.db.models.functions import ExtractHour, TruncDate
from decimal import Decimal
from .models import Pedido, DetalhePedido, Item, Categoria

class ServicoRelatorio:
    @staticmethod
    def calcular_vendas_periodo(data_inicio, data_fim):
        pedidos = Pedido.objects.filter(
            data_pedido__range=(data_inicio, data_fim),
            status_pedido__in=[2, 3]
        )

        total_vendas = Decimal('0.00')
        for pedido in pedidos.prefetch_related('itens'):
            total_vendas += sum(
                Decimal(detalhe.get_subtotal())
                for detalhe in pedido.itens.all()
            )

        numero_pedidos = pedidos.count()

        return {
            'total_vendas': total_vendas,
            'numero_pedidos': numero_pedidos,
            'itens_vendidos': DetalhePedido.objects.filter(
                pedido__in=pedidos
            ).aggregate(total=Sum('quantidade_item'))['total'] or 0
        }


    @staticmethod
    def vendas_por_categoria(data_inicio, data_fim):
        """
        Retorna o total de vendas agrupado por categoria, considerando tamanhos e promoções
        """
        pedidos = Pedido.objects.filter(
            data_pedido__range=(data_inicio, data_fim),
            status_pedido__in=[2, 3]
        ).prefetch_related('itens')

        # Dicionário para acumular resultados por categoria
        resultados = {}
        
        for pedido in pedidos:
            for detalhe in pedido.itens.all():
                categoria = detalhe.item.id_categoria
                if categoria.id not in resultados:
                    resultados[categoria.id] = {
                        'nome_categoria': categoria.nome_categoria,
                        'total_vendas': Decimal('0.00'),
                        'quantidade_vendida': 0
                    }
                
                # Usa get_subtotal() que considera decorators
                resultados[categoria.id]['total_vendas'] += Decimal(detalhe.get_subtotal())
                resultados[categoria.id]['quantidade_vendida'] += detalhe.quantidade_item

        # Converte para lista e ordena por total de vendas
        return sorted(
            resultados.values(),
            key=lambda x: x['total_vendas'],
            reverse=True
        )

    @staticmethod
    def produtos_mais_vendidos(data_inicio, data_fim, limite=10):
        """
        Retorna os produtos mais vendidos no período, considerando tamanhos e promoções
        """
        pedidos = Pedido.objects.filter(
            data_pedido__range=(data_inicio, data_fim),
            status_pedido__in=[2, 3]
        ).prefetch_related('itens')

        # Dicionário para acumular resultados por item
        resultados = {}
        
        for pedido in pedidos:
            for detalhe in pedido.itens.all():
                item_key = (
                    detalhe.item.id,
                    detalhe.tamanho_item.id if detalhe.tamanho_item else None
                )
                
                if item_key not in resultados:
                    nome_item = detalhe.item.nome_item
                    if detalhe.tamanho_item:
                        nome_item += f" ({detalhe.tamanho_item.tamanho})"
                    
                    resultados[item_key] = {
                        'nome_item': nome_item,
                        'quantidade_total': 0,
                        'receita_total': Decimal('0.00')
                    }
                
                resultados[item_key]['quantidade_total'] += detalhe.quantidade_item
                resultados[item_key]['receita_total'] += Decimal(detalhe.get_subtotal())

        # Converte para lista, ordena e limita
        return sorted(
            resultados.values(),
            key=lambda x: x['quantidade_total'],
            reverse=True
        )[:limite]
