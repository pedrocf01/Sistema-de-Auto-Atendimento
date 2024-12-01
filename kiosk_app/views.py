from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.db.models import Count, F, ExpressionWrapper, DurationField
from .models import Categoria, Item, Promocao, Pedido, DetalhePedido, TamanhoItem
from .gerenciador_carrinho import ItemCarrinho, GerenciadorCarrinho
from .servicos_relatorio import ServicoRelatorio
from .servicos_checkout import ServicoCheckout
from users.models import Usuario


class CardapioView(ListView):
    """
    View para exibir o cardápio, organizando os itens por categorias.
    """
    template_name = 'kiosk_app/cardapio.html'
    model = Categoria
    context_object_name = 'categorias'

    def get_context_data(self, **kwargs):
        """
        Adiciona ao contexto os itens do cardápio com tamanhos e ingredientes extras.
        """
        context = super().get_context_data(**kwargs)
        context['itens'] = Item.objects.prefetch_related('tamanhos', 'ingredientes_extras')
        return context


class ItemDetalheView(DetailView):
    """
    View para exibir os detalhes de um item específico do cardápio.
    """
    template_name = 'item_detalhe.html'
    model = Item
    context_object_name = 'item'
    pk_url_kwarg = 'item_id'


class PedidoRastreioView(LoginRequiredMixin, ListView):
    """
    View para listar os pedidos do cliente, excluindo os que ainda estão no status 'Carrinho'.
    """
    template_name = 'pedidos_rastreio.html'
    context_object_name = 'pedidos'

    def get_queryset(self):
        """
        Recupera os pedidos do cliente atual que não estão no status de carrinho.
        """
        return Pedido.objects.filter(cliente=self.request.user).exclude(status_pedido=0)


class AdicionarAoCarrinhoView(LoginRequiredMixin, View):
    """
    View para adicionar itens ao carrinho do cliente.
    """
    def post(self, request):
        """
        Processa o formulário de adição de itens ao carrinho.
        """
        item_carrinho = ItemCarrinho(
            item_id=request.POST.get('item_id'),
            tamanho_item_id=request.POST.get('tamanho_item_id'),
            sabor_id=request.POST.get('sabor_id'),
            ingredientes_extras_ids=request.POST.getlist('ingredientes_extras')
        )

        gerenciador_carrinho = GerenciadorCarrinho(request.user)
        gerenciador_carrinho.adicionar_item(item_carrinho)

        return redirect('kiosk_app:carrinho')

    def get(self, request):
        return redirect('kiosk_app:cardapio')


class CarrinhoView(LoginRequiredMixin, TemplateView):
    """
    View para mostrar os itens do carrinho do cliente
    """
    template_name = 'kiosk_app/carrinho.html'

    @staticmethod
    def revalidar_promocoes(pedido: Pedido) -> None:
        """Revalida todas as promoções do pedido"""
        for detalhe in pedido.itens.all():
            if detalhe.item.id_promocao and detalhe.item.id_promocao.is_ativa:
                detalhe.promocao = detalhe.item.id_promocao
            else:
                detalhe.promocao = None
            detalhe.save()    

    def get_context_data(self, **kwargs):
        """
        Recupera o carrinho do cliente atual e calcula o total do pedido
        """
        context = super().get_context_data(**kwargs)
        pedido = Pedido.objects.filter(cliente=self.request.user, status_pedido=0).first()
        
        if pedido:
            # Recalcula promoções ativas para cada item no carrinho
            CarrinhoView.revalidar_promocoes(pedido)

            context['itens_pedido'] = pedido.itens.select_related(
                'item', 'tamanho_item', 'promocao'
            ).prefetch_related('ingredientes_extras')
            context['total'] = pedido.get_total()
        else:
            context['itens_pedido'] = []
            context['total'] = 0.00
            
        return context


class AtualizarItemCarrinhoView(LoginRequiredMixin, View):
    """
    View para atualizar a quantidade de um item no carrinho.
    """
    def post(self, request, detalhe_pedido_id):
        """
        Atualiza a quantidade de um item no carrinho ou o remove se a quantidade for zero.
        """
        detalhe_pedido = get_object_or_404(
            DetalhePedido,
            id=detalhe_pedido_id,
            pedido__cliente=request.user,
            pedido__status_pedido=0
        )
        
        quantidade = int(request.POST.get('quantidade_item', 1))
        if quantidade > 0:
            detalhe_pedido.quantidade_item = quantidade
            detalhe_pedido.save()
        else:
            detalhe_pedido.delete()
            
        return redirect('kiosk_app:carrinho')


class RemoverItemCarrinhoView(LoginRequiredMixin, View):
    """
    View para remover um item do carrinho.
    """
    def get(self, request, detalhe_pedido_id):
        """
        Remove o item especificado do carrinho.
        """
        detalhe_pedido = get_object_or_404(
            DetalhePedido,
            id=detalhe_pedido_id,
            pedido__cliente=request.user,
            pedido__status_pedido=0
        )
        detalhe_pedido.delete()
        return redirect('kiosk_app:carrinho')


class FinalizarPedidoView(LoginRequiredMixin, View):
    """
    View para processar o checkout do carrinho.
    """
    template_name = 'kiosk_app/finalizar_pedido.html'

    def get_servico_checkout(self):
        return ServicoCheckout(self.request.user)

    def get(self, request):
        """
        Mostra a página de finalização do pedido.
        """
        servico_checkout = self.get_servico_checkout()
        pedido = servico_checkout.obter_carrinho_ativo()
        
        carrinho_valido, erro_carrinho = servico_checkout.validar_carrinho(pedido)
        if not carrinho_valido:
            return redirect('kiosk_app:cardapio')
            
        return render(request, self.template_name, {'pedido': pedido})

    def post(self, request):
        """
        Processa a finalização do pedido e redireciona para a página de confirmação.
        """
        servico_checkout = self.get_servico_checkout()
        pedido = servico_checkout.obter_carrinho_ativo()
        
        CarrinhoView.revalidar_promocoes(pedido)

        local_consumo = request.POST.get('local_consumo')
        metodo_pagamento = request.POST.get('metodo_pagamento')

        dados_validos, mensagem_erro = servico_checkout.validar_dados_checkout(
            local_consumo,
            metodo_pagamento
        )

        if dados_validos:
            servico_checkout.processar_checkout(pedido, local_consumo, metodo_pagamento)
            return redirect('kiosk_app:pedido_confirmado', pedido_id=pedido.id)

        return render(request, self.template_name, {
            'pedido': pedido,
            'mensagem_erro': mensagem_erro
        })

class PedidoConfirmadoView(LoginRequiredMixin, DetailView):
    """
    View para exibir a confirmação de um pedido finalizado
    """
    template_name = 'kiosk_app/pedido_confirmado.html'
    model = Pedido
    context_object_name = 'pedido'
    pk_url_kwarg = 'pedido_id'

    def get_queryset(self):
        """
        Recupera apenas os pedidos pertencentes ao usuário atual
        """
        return Pedido.objects.filter(cliente=self.request.user)


class CozinheiroRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.papel == 'cozinheiro'


class CozinheiroPedidoFilaView(LoginRequiredMixin, CozinheiroRequiredMixin, ListView):
    """
    View para exibir a fila de pedidos pendentes ou em preparação para o cozinheiro.
    """
    template_name = 'kiosk_app/cozinha/fila_pedidos.html'
    context_object_name = 'pedidos'

    def get_queryset(self):
        """
        Recupera os pedidos em status 'Pendente' ou 'Em Preparação', 
        calculando o tempo de espera.
        """
        return Pedido.objects.filter(
            status_pedido__in=[1, 2]
        ).annotate(
            waiting_time=ExpressionWrapper(
                timezone.now() - F('data_pedido'),
                output_field=DurationField()
            )
        ).order_by('status_pedido', 'data_pedido')

    def get_context_data(self, **kwargs):
        """
        Adiciona o dicionário de status do pedido ao contexto.
        """
        context = super().get_context_data(**kwargs)
        context['status_map'] = dict(Pedido.OPCOES_STATUS)
        return context


class CozinheiroAlterarPedidoView(LoginRequiredMixin, CozinheiroRequiredMixin, View):
    """
    View para permitir que o cozinheiro altere o status de um pedido.
    """
    def post(self, request, pedido_id):
        """
        Atualiza o status de um pedido, permitindo transições para 
        'Em Preparação' ou 'Pronto'.
        """
        pedido = get_object_or_404(Pedido, id=pedido_id)
        novo_status = int(request.POST.get('novo_status'))
        
        if novo_status in [2, 3]:  # Status válidos: 'Em Preparação' ou 'Pronto'
            if novo_status == 3:
                pedido.data_conclusao = timezone.now()
            pedido.status_pedido = novo_status
            pedido.save()
            messages.success(request, f'Status do pedido {pedido.id} atualizado com sucesso.')
        else:
            messages.error(request, 'Transição de status inválida.')
            
        return redirect('kiosk_app:cozinheiro_pedidos')


class CozinheiroPedidoHistoricoView(LoginRequiredMixin, CozinheiroRequiredMixin, ListView):
    """
    View para exibir o histórico de pedidos concluídos
    """
    template_name = 'kiosk_app/cozinha/historico_pedidos.html'
    context_object_name = 'pedidos'

    def get_queryset(self):
        """
        Recupera os pedidos concluídos nas últimas 24 horas.
        """
        data_inicio = timezone.now() - timezone.timedelta(days=1)
        return Pedido.objects.filter(
            status_pedido=3,  # Status 'Pronto'
            data_pedido__range=(data_inicio, timezone.now())
        ).order_by('-data_pedido')


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.papel == 'administrador'


class RelatorioVendasView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """
    View para exibir relatórios de vendas ao administrador.
    """
    template_name = 'admin/relatorio_vendas.html'

    def get_intervalo_datas(self):
        """
        Recupera o intervalo de datas para o relatório, 
        usando os parâmetros da requisição ou um intervalo padrão de 30 dias.
        """
        data_fim = timezone.now()
        data_inicio = data_fim - timedelta(days=30)

        if self.request.GET.get('data_inicio'):
            data_inicio = timezone.datetime.strptime(
                self.request.GET.get('data_inicio'),
                '%Y-%m-%d'
            )
        if self.request.GET.get('data_fim'):
            data_fim = timezone.datetime.strptime(
                self.request.GET.get('data_fim'),
                '%Y-%m-%d'
            )

        return data_inicio, data_fim

    def get_context_data(self, **kwargs):
        """
        Adiciona as métricas de vendas ao contexto
        """
        context = super().get_context_data(**kwargs)
        data_inicio, data_fim = self.get_intervalo_datas()

        context.update({
            'metricas_gerais': ServicoRelatorio.calcular_vendas_periodo(data_inicio, data_fim),
            'vendas_categorias': ServicoRelatorio.vendas_por_categoria(data_inicio, data_fim),
            'produtos_top': ServicoRelatorio.produtos_mais_vendidos(data_inicio, data_fim),
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        })

        return context

