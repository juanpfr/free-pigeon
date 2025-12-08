# ===============================
# IMPORTS GERAIS
# ===============================
import stripe
import re
from functools import wraps
from .utils_frete import calcular_frete_correios
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.contrib.auth import logout
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum, F
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db.models import Count
from django.urls import reverse



# ===============================
# MODELOS
# ===============================
from .models import (
    Usuario, Loja, Categoria, Produto,
    Carrinho, CarrinhoProduto,
    Pedido, PedidoProduto,
    Endereco, Plano, AdminUser
)

def usuario_login_required(view_func):
    """
    Verifica se existe 'usuario_id' na sessão.
    Se não tiver, manda pra tela de login, com ?next=<url>.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            login_url = reverse('login')
            next_param = request.path
            return redirect(f"{login_url}?next={next_param}")
        return view_func(request, *args, **kwargs)
    return _wrapped

# ============================================================
# PLANOS
# ============================================================
def get_default_plan():
    """
    Retorna o plano default (marcado como is_default=True).
    Se não tiver, pega o mais barato ativo.
    Se não tiver nada, retorna None.
    """
    plano = Plano.objects.filter(ativo=True, is_default=True).order_by('preco_mensal').first()
    if plano:
        return plano
    return Plano.objects.filter(ativo=True).order_by('preco_mensal').first()

@usuario_login_required
def planos(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    planos = Plano.objects.filter(ativo=True).order_by('preco_mensal')

    # escolhe a public key do Stripe como você já faz
    if settings.STRIPE_LIVE_MODE:
        stripe_public_key = settings.STRIPE_LIVE_PUBLIC_KEY
    else:
        stripe_public_key = settings.STRIPE_TEST_PUBLIC_KEY

    return render(request, 'planos.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'planos': planos,
        'stripe_public_key': stripe_public_key,
    })

def criar_checkout_plano(usuario, plano, origem='upgrade'):
    """
    Helper para criar uma sessão de checkout de plano no Stripe.
    Usado tanto no upgrade (/planos) quanto no cadastro.
    """
    # Se for plano gratuito, não precisa Stripe
    if plano.preco_mensal <= 0:
        return None

    valor_centavos = int(plano.preco_mensal * 100)

    domain_url = usuario._request.build_absolute_uri('/')[:-1]  # explico já já
    success_url = domain_url + '/planos/sucesso/?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = domain_url + '/planos/'

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card', 'pix'],
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': 'brl',
                'product_data': {'name': f'Plano {plano.nome}'},
                'unit_amount': valor_centavos,
            },
            'quantity': 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(usuario.id),
        customer_email=usuario.email,
        metadata={
            'usuario_id': usuario.id,
            'plano_slug': plano.slug,
            'origem': origem,
        },
    )
    return checkout_session


@usuario_login_required
@require_POST
def create_plan_checkout_session(request):
    """Cria uma Checkout Session para upgrade de plano (página /planos)."""
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    plano_slug = request.POST.get('plano_slug')
    plano = get_object_or_404(Plano, slug=plano_slug)

    # Se for plano gratuito, não precisa Stripe
    if plano.preco_mensal <= 0:
        usuario.plano = plano
        usuario.save()
        messages.success(request, f'Você mudou para o plano {plano.nome}.')
        return JsonResponse({'free': True})

    valor_centavos = int(plano.preco_mensal * 100)

    domain_url = request.build_absolute_uri('/')[:-1]
    success_url = domain_url + '/planos/sucesso/?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = domain_url + '/planos/'

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],  # 👈 apenas cartão aqui também
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': 'brl',
                'product_data': {
                    'name': f'Plano {plano.nome}',
                },
                'unit_amount': valor_centavos,
            },
            'quantity': 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(usuario.id),
        customer_email=usuario.email,
        metadata={
            'usuario_id': usuario.id,
            'plano_slug': plano.slug,
        },
    )


    return JsonResponse({'sessionId': checkout_session.id})


def plan_success(request):
    """Confirma pagamento do plano e ativa no usuário, garantindo login."""
    session_id = request.GET.get('session_id')

    if not session_id:
        return redirect('planos')

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            # Pega infos da sessão do Stripe
            metadata = session.get('metadata', {}) or {}
            plano_slug = metadata.get('plano_slug')
            usuario_id_meta = metadata.get('usuario_id')
            origem = metadata.get('origem')  # 'cadastro' ou vazio

            if not (plano_slug and usuario_id_meta):
                messages.error(request, 'Não foi possível identificar o plano ou usuário.')
                return redirect('planos')

            plano = Plano.objects.get(slug=plano_slug)
            usuario = Usuario.objects.get(id=usuario_id_meta)

            # Atualiza plano do usuário
            usuario.plano = plano
            usuario.save()

            # 🔑 Garante que o usuário esteja logado na sua sessão manual
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nome'] = usuario.nome

            messages.success(request, f'Seu plano {plano.nome} foi ativado com sucesso!')

            # Se veio do cadastro, manda pra home
            if origem == 'cadastro':
                return redirect('home')

            # Se veio de upgrade dentro do sistema, volta pra tela de planos
            return redirect('planos')

        else:
            messages.error(request, 'Pagamento do plano ainda não foi concluído.')
            return redirect('planos')

    except Exception as e:
        messages.error(request, f'Erro ao confirmar pagamento do plano: {e}')
        return redirect('planos')

# ============================================================
# USUÁRIO / LOGIN / LOGOUT / CADASTRO
# ============================================================
def so_digitos(valor):
    """
    Remove tudo que não for número.
    Ex: '123.456.789-10' -> '12345678910'
        '(11) 91234-5678' -> '11912345678'
        None -> ''
    """
    if not valor:
        return ''
    return re.sub(r'\D', '', str(valor))

def cadastrar_usuario(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cpf = request.POST.get('cpf')
        senha = request.POST.get('senha')
        plano_slug = request.POST.get('plano')

        plano_escolhido = Plano.objects.filter(slug=plano_slug).first()

        # Segurança: se não veio plano, usa o default
        if not plano_escolhido:
            plano_escolhido = Plano.objects.filter(is_default=True).first()

        # Cria o usuário
        usuario = Usuario.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            cpf=cpf,
            senha=senha,
            plano=plano_escolhido
        )

        request.session['usuario_id'] = usuario.id

        # -----------------------------------------------------
        # >>> É AQUI <<< onde você coloca o print e o if
        # -----------------------------------------------------

        is_plano_pago = plano_escolhido.preco_mensal > 0

        print("PLANO ESCOLHIDO:", plano_escolhido.nome)
        print("É PAGO?", is_plano_pago)
        print("Valor:", plano_escolhido.preco_mensal)

        # Se o plano é pago → iniciar Stripe Checkout
        if plano_escolhido and plano_escolhido.preco_mensal and plano_escolhido.preco_mensal > 0:
            try:
                valor_centavos = int(plano_escolhido.preco_mensal * 100)

                domain_url = request.build_absolute_uri('/')[:-1]
                success_url = domain_url + '/planos/sucesso/?session_id={CHECKOUT_SESSION_ID}'
                cancel_url = domain_url + '/planos/'

                checkout_session = stripe.checkout.Session.create(
                    # 👇 POR ENQUANTO SOMENTE CARTÃO
                    payment_method_types=['card'],
                    mode='payment',
                    line_items=[{
                        'price_data': {
                            'currency': 'brl',
                            'product_data': {
                                'name': f'Plano {plano_escolhido.nome}',
                            },
                            'unit_amount': valor_centavos,
                        },
                        'quantity': 1,
                    }],
                    success_url=success_url,
                    cancel_url=cancel_url,
                    client_reference_id=str(usuario.id),
                    customer_email=usuario.email,
                    metadata={
                        'usuario_id': usuario.id,
                        'plano_slug': plano_escolhido.slug,
                        'origem': 'cadastro',
                    },
                )

                return redirect(checkout_session.url)

            except Exception as e:
                print('Erro ao criar sessão de plano no Stripe (cadastro):', e)
                messages.error(
                    request,
                    'Sua conta foi criada, mas ocorreu um erro ao iniciar o pagamento do plano. '
                    'Você pode tentar novamente na página "Mudar plano".'
                )
                return redirect('planos')


    # GET
    planos = Plano.objects.filter(ativo=True)
    return render(request, "cadastro.html", { "planos": planos })



def login_view(request):
    previous_url = request.META.get('HTTP_REFERER', '')
    veio_do_auth = 'auth' in previous_url

    if request.method == 'POST':
        username = request.POST.get('username')
        senha = request.POST.get('senha')

        usuario = None
        try:
            usuario = Usuario.objects.get(email=username)
        except Usuario.DoesNotExist:
            try:
                usuario = Usuario.objects.get(cpf=username)
            except Usuario.DoesNotExist:
                pass

        if usuario and check_password(senha, usuario.senha):
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nome'] = usuario.nome
            return redirect('home')
        else:
            return render(request, 'login.html', {
                'mensagem_erro': 'Usuário ou senha inválidos.',
                'veio_do_auth': veio_do_auth
            })

    return render(request, 'login.html', {'veio_do_auth': veio_do_auth})


def logout_view(request):
    logout(request)

    response = redirect('home')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response



def google_login_redirect(request):
    if not request.user.is_authenticated:
        return redirect('/')

    email = request.user.email
    nome = (
        request.user.get_full_name()
        or getattr(request.user, 'first_name', '')
        or (email.split('@')[0] if email else 'Usuário')
    )

    plano_default = get_default_plan()

    usuario, created = Usuario.objects.get_or_create(
        email=email,
        defaults={
            'nome': nome,
            'telefone': None,
            'cpf': None,
            'senha': make_password(None),
            'plano': plano_default,
        }
    )

    if not usuario.plano and plano_default:
        usuario.plano = plano_default
        usuario.save()

    request.session['usuario_id'] = usuario.id
    request.session['usuario_nome'] = usuario.nome

    return redirect('home')


def auth_view(request):
    return render(request, 'auth.html')


# ============================================================
# PERFIL / ÁREA DO VENDEDOR
# ============================================================

@usuario_login_required
def perfil(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    produtos_pessoais = Produto.objects.filter(vendedor=usuario, loja__isnull=True).count()
    produtos_loja = 0
    if usuario.loja:
        produtos_loja = Produto.objects.filter(loja=usuario.loja).count()

    enderecos = usuario.enderecos.all().order_by('-principal', 'id')

    # total de anúncios ativos (com ou sem loja)
    anuncios_ativos = Produto.objects.filter(
        Q(vendedor=usuario) | Q(loja=usuario.loja)
    ).count() if usuario.loja else Produto.objects.filter(vendedor=usuario).count()

    return render(request, 'perfil.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'produtos_pessoais': produtos_pessoais,
        'produtos_loja': produtos_loja,
        'enderecos': enderecos,
        'anuncios_ativos': anuncios_ativos,
    })


@usuario_login_required
def editar_perfil(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    if request.method == 'POST':
        nome = (request.POST.get('nome') or '').strip()
        telefone = so_digitos(request.POST.get('telefone'))
        cpf = so_digitos(request.POST.get('cpf'))

        if not nome:
            messages.error(request, 'O nome é obrigatório.')
        else:
            usuario.nome = nome
            usuario.telefone = telefone or None  # evita string vazia no banco
            usuario.cpf = cpf or None
            usuario.save()

            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('perfil')

    return render(request, 'editar_perfil.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
    })


@usuario_login_required
def alterar_senha(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual') or ''
        nova_senha = request.POST.get('nova_senha') or ''
        nova_senha2 = request.POST.get('nova_senha2') or ''

        # SE estiver usando hash:
        # if not check_password(senha_atual, usuario.senha):

        if senha_atual != usuario.senha:
            messages.error(request, 'Senha atual incorreta.')
        elif not nova_senha:
            messages.error(request, 'Informe a nova senha.')
        elif nova_senha != nova_senha2:
            messages.error(request, 'A confirmação da nova senha não confere.')
        else:
            # Se usar hash:
            # usuario.senha = make_password(nova_senha)
            usuario.senha = nova_senha
            usuario.save()
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('perfil')

    return render(request, 'alterar_senha.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
    })

@usuario_login_required
def enderecos(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    if request.method == 'POST':
        apelido = (request.POST.get('apelido') or '').strip()
        rua = (request.POST.get('rua') or '').strip()
        numero = request.POST.get('numero')
        bairro = (request.POST.get('bairro') or '').strip()
        cidade = (request.POST.get('cidade') or '').strip()
        estado = (request.POST.get('estado') or '').strip()
        cep = (request.POST.get('cep') or '').strip()
        complemento = (request.POST.get('complemento') or '').strip()
        principal = bool(request.POST.get('principal'))

        if not (rua and numero and bairro and cidade and estado and cep):
            messages.error(request, 'Preencha todos os campos obrigatórios.')
        else:
            if principal:
                usuario.enderecos.update(principal=False)

            Endereco.objects.create(
                usuario=usuario,
                apelido=apelido or None,
                rua=rua,
                numero=numero,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                cep=cep,
                complemento=complemento or None,
                principal=principal,
            )
            messages.success(request, 'Endereço cadastrado com sucesso!')
            return redirect('enderecos')

    enderecos = usuario.enderecos.all().order_by('-principal', 'id')
    return render(request, 'enderecos.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'enderecos': enderecos,
    })

@usuario_login_required
def editar_endereco(request, endereco_id):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    endereco = get_object_or_404(Endereco, id=endereco_id, usuario=usuario)

    if request.method == 'POST':
        apelido = (request.POST.get('apelido') or '').strip()
        rua = (request.POST.get('rua') or '').strip()
        numero = request.POST.get('numero')
        bairro = (request.POST.get('bairro') or '').strip()
        cidade = (request.POST.get('cidade') or '').strip()
        estado = (request.POST.get('estado') or '').strip()
        cep = (request.POST.get('cep') or '').strip()
        complemento = (request.POST.get('complemento') or '').strip()
        principal = bool(request.POST.get('principal'))

        if not (rua and numero and bairro and cidade and estado and cep):
            messages.error(request, 'Preencha todos os campos obrigatórios.')
        else:
            if principal:
                usuario.enderecos.update(principal=False)

            endereco.apelido = apelido or None
            endereco.rua = rua
            endereco.numero = numero
            endereco.bairro = bairro
            endereco.cidade = cidade
            endereco.estado = estado
            endereco.cep = cep
            endereco.complemento = complemento or None
            endereco.principal = principal
            endereco.save()

            messages.success(request, 'Endereço atualizado com sucesso!')
            return redirect('enderecos')

    return render(request, 'editar_endereco.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'endereco': endereco,
    })

@usuario_login_required
def excluir_endereco(request, endereco_id):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    endereco = get_object_or_404(Endereco, id=endereco_id, usuario=usuario)

    if request.method == 'POST':
        endereco.delete()
        messages.success(request, 'Endereço removido com sucesso!')
        return redirect('enderecos')

    return render(request, 'confirmar_exclusao_endereco.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'endereco': endereco,
    })

@usuario_login_required
def definir_endereco_principal(request, endereco_id):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    endereco = get_object_or_404(Endereco, id=endereco_id, usuario=usuario)

    usuario.enderecos.update(principal=False)
    endereco.principal = True
    endereco.save()
    messages.success(request, 'Endereço definido como principal.')
    return redirect('enderecos')


@usuario_login_required
def vender(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    return render(request, 'vender.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
    })

def _get_produto_do_usuario(usuario, produto_id):
    """
    Busca um produto que pertença ao usuário:
      - como vendedor pessoa física (vendedor=usuario), ou
      - via loja do usuário (loja=usuario.loja, se existir).
    Levanta 404 se não for dele.
    """
    filtros = Q(vendedor=usuario)
    if usuario.loja:
        filtros |= Q(loja=usuario.loja)

    return get_object_or_404(Produto, Q(id=produto_id) & filtros)


@usuario_login_required
def anuncios(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id=usuario_id)

    # produtos do usuário como vendedor
    filtros = Q(vendedor=usuario)

    # se o usuário tiver loja, também mostra produtos vinculados à loja
    if usuario.loja:
        filtros |= Q(loja=usuario.loja)

    produtos = Produto.objects.filter(filtros)

    return render(request, 'anuncios.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'produtos': produtos,
    })

from django.contrib.auth.decorators import login_required

@usuario_login_required
def editar_anuncio(request, produto_id):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    produto = _get_produto_do_usuario(usuario, produto_id)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        nome = (request.POST.get('nome') or '').strip()
        categoria_id = request.POST.get('categoria')
        descricao = (request.POST.get('descricao') or '').strip()
        valor_raw = (request.POST.get('valor') or '').strip()
        desconto_raw = (request.POST.get('desconto') or '').strip()
        q_estoque_raw = (request.POST.get('q_estoque') or '').strip()
        ativo_flag = bool(request.POST.get('ativo'))
        imagem = request.FILES.get('imagem')

        erros = []

        if not nome:
            erros.append('Informe o nome do produto.')
        if not categoria_id:
            erros.append('Selecione uma categoria.')
        if not valor_raw:
            erros.append('Informe o preço do produto.')
        if not q_estoque_raw:
            erros.append('Informe o estoque disponível.')

        try:
            valor = Decimal(valor_raw.replace(',', '.')) if valor_raw else None
        except Exception:
            erros.append('Preço inválido.')

        try:
            q_estoque = int(q_estoque_raw) if q_estoque_raw else None
            if q_estoque is not None and q_estoque < 0:
                erros.append('O estoque não pode ser negativo.')
        except Exception:
            erros.append('Estoque inválido.')

        desconto = None
        if desconto_raw:
            try:
                desconto = Decimal(desconto_raw.replace(',', '.'))
                if desconto < 0 or desconto > 100:
                    erros.append('O desconto deve estar entre 0 e 100%.')
            except Exception:
                erros.append('Desconto inválido.')

        if erros:
            for e in erros:
                messages.error(request, e)
            return render(request, 'editar_anuncio.html', {
                'usuario_nome': usuario.nome,
                'usuario': usuario,
                'produto': produto,
                'categorias': categorias,
            })

        categoria = get_object_or_404(Categoria, id=categoria_id)

        # Atualiza o produto
        produto.nome = nome
        produto.categoria = categoria
        produto.descricao = descricao or None
        produto.valor = valor
        produto.desconto = desconto
        produto.q_estoque = q_estoque
        produto.ativo = ativo_flag

        if imagem:
            produto.imagem = imagem

        produto.save()

        messages.success(request, 'Anúncio atualizado com sucesso!')
        return redirect('anuncios')

    # GET
    return render(request, 'editar_anuncio.html', {
        'usuario_nome': usuario.nome,
        'usuario': usuario,
        'produto': produto,
        'categorias': categorias,
    })

@usuario_login_required
def excluir_anuncio(request, produto_id):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    produto = _get_produto_do_usuario(usuario, produto_id)

    if request.method == 'POST':
        nome_produto = produto.nome
        produto.delete()
        messages.success(request, f"O anúncio '{nome_produto}' foi excluído com sucesso.")
        return redirect('anuncios')

    # GET: mostra tela de confirmação
    return render(request, 'confirmar_exlusao_anuncio.html', {
        'usuario_nome': usuario.nome,
        'usuario': usuario,
        'produto': produto,
    })

@usuario_login_required
def toggle_status_anuncio(request, produto_id):
    if request.method != 'POST':
        return redirect('anuncios')

    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    produto = _get_produto_do_usuario(usuario, produto_id)

    produto.ativo = not produto.ativo
    produto.save()

    if produto.ativo:
        messages.success(request, f"O anúncio '{produto.nome}' foi ativado.")
    else:
        messages.info(request, f"O anúncio '{produto.nome}' foi desativado.")

    return redirect('anuncios')


@usuario_login_required
def resumo(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    # Exemplo simples de cálculo – ajuste conforme precisar
    pedidos = Pedido.objects.filter(usuario=usuario)
    total_pedidos = pedidos.count()

    total_itens = 0
    faturamento = 0
    for pedido in pedidos:
        for item in pedido.itens.all():
            total_itens += item.quantidade
        faturamento += pedido.total()

    ultimos_pedidos = pedidos.order_by('-data_efetuado')[:5]

    return render(request, 'resumo.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'total_pedidos': total_pedidos,
        'total_itens_vendidos': total_itens,
        'faturamento_total': f"{faturamento:.2f}",
        'ultimos_pedidos': ultimos_pedidos,
    })


# ====== NOVO: CRIAR LOJA ======

@usuario_login_required
def criar_loja(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    plano_usuario = usuario.plano or get_default_plan()

    # ❌ Bloquear criação de loja no plano gratuito padrão
    if plano_usuario and plano_usuario.is_default:
        messages.error(
            request,
            'No plano gratuito você não pode criar uma loja. '
            'Faça upgrade de plano para poder criar uma loja.'
        )
        return redirect('planos')

    if request.method == 'POST':
        nome = (request.POST.get('nome') or '').strip()
        if not nome:
            messages.error(request, 'Informe um nome para a loja.')
        else:
            loja = Loja.objects.create(nome=nome)
            usuario.loja = loja
            usuario.save()
            messages.success(request, 'Loja criada com sucesso!')
            return redirect('vender')

    return render(request, 'criar_loja.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
    })


# ====== NOVO: CADASTRAR PRODUTO ======

@usuario_login_required
def cadastrar_produto(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    categorias = Categoria.objects.all()

    plano_usuario = usuario.plano or get_default_plan()
    limite = plano_usuario.limite_anuncios if plano_usuario else None

    if request.method == 'POST':
        # Limite de anúncios
        if limite is not None:
            total_atual = Produto.objects.filter(
                Q(vendedor=usuario) | Q(loja=usuario.loja)
            ).count()

            if total_atual >= limite:
                messages.error(
                    request,
                    f'Você atingiu o limite de {limite} anúncios do seu plano {plano_usuario.nome}.'
                    if plano_usuario else 'Você atingiu o limite de anúncios do seu plano.'
                )
                return redirect('planos')

        nome = request.POST.get('nome')
        categoria_id = request.POST.get('categoria')
        descricao = request.POST.get('descricao')
        valor = request.POST.get('valor')
        desconto = request.POST.get('desconto') or None
        q_estoque = request.POST.get('q_estoque')
        imagem = request.FILES.get('imagem')
        vincular_loja = request.POST.get('vincular_loja')

        if not nome or not categoria_id or not valor or not q_estoque:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
        else:
            categoria = get_object_or_404(Categoria, id=categoria_id)

            produto = Produto.objects.create(
                nome=nome,
                descricao=descricao,
                valor=valor,
                desconto=desconto,
                q_estoque=q_estoque,
                categoria=categoria,
                vendedor=usuario,
                loja=usuario.loja if (usuario.loja and vincular_loja) else None,
                imagem=imagem
            )

            messages.success(request, 'Produto cadastrado com sucesso!')
            return redirect('anuncios')

    return render(request, 'cadastrar_produto.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'categorias': categorias,
    })


# ============================================================
# HOME / CATEGORIAS / PRODUTOS / PESQUISA
# ============================================================

def home_view(request):
    usuario_nome = request.session.get('usuario_nome')
    categorias = Categoria.objects.all()
    produtos = Produto.objects.all()[:10]  # mostra alguns na home
    return render(request, 'home.html', {
        'usuario_nome': usuario_nome,
        'categorias': categorias,
        'produtos': produtos
    })


def categoria_view(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    produtos = Produto.objects.filter(categoria=categoria)
    usuario_nome = request.session.get('usuario_nome')
    return render(request, 'categoria.html', {
        'categoria': categoria,
        'produtos': produtos,
        'usuario_nome': usuario_nome
    })


def buscar_produtos(request):
    query = request.GET.get('q', '')
    produtos = Produto.objects.filter(nome__icontains=query) if query else []
    usuario_nome = request.session.get('usuario_nome')
    return render(request, 'buscar.html', {
        'query': query,
        'produtos': produtos,
        'usuario_nome': usuario_nome
    })


def produto_view(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    usuario_nome = request.session.get('usuario_nome')
    return render(request, 'product.html', {
        'produto': produto,
        'usuario_nome': usuario_nome
    })


# ============================================================
# CARRINHO
# ============================================================

def ver_carrinho(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = get_object_or_404(Usuario, id=usuario_id)
    carrinho, _ = Carrinho.objects.get_or_create(usuario=usuario)

    itens = carrinho.itens.select_related('produto', 'produto__categoria')

    subtotal = sum(item.subtotal() for item in itens) if itens else Decimal('0.00')
    total_itens = sum(item.quantidade for item in itens) if itens else 0
    frete = Decimal('0.00')  # calculado no checkout
    total = subtotal + frete

    return render(request, 'cart.html', {
        'itens': itens,
        'subtotal': subtotal,
        'total_itens': total_itens,
        'frete': frete,
        'total': total,
        'usuario_nome': usuario.nome,
    })


def adicionar_ao_carrinho(request, produto_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    carrinho, _ = Carrinho.objects.get_or_create(usuario=usuario)
    produto = get_object_or_404(Produto, id=produto_id)
    item, created = CarrinhoProduto.objects.get_or_create(carrinho=carrinho, produto=produto)
    if not created:
        item.quantidade += 1
    item.save()

    return redirect('ver_carrinho')


def remover_do_carrinho(request, produto_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    carrinho = Carrinho.objects.filter(usuario=usuario).first()
    if carrinho:
        CarrinhoProduto.objects.filter(carrinho=carrinho, produto_id=produto_id).delete()
    return redirect('ver_carrinho')


# ============================================================
# CHECKOUT / PEDIDO / FRETE
# ============================================================

def checkout_view(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    carrinho = Carrinho.objects.filter(usuario=usuario).first()
    if not carrinho:
        return redirect('ver_carrinho')

    itens = CarrinhoProduto.objects.filter(carrinho=carrinho)
    total = sum(item.subtotal() for item in itens)

    # PEGAR ENDEREÇOS DO USUÁRIO
    enderecos_qs = Endereco.objects.filter(usuario=usuario)

    endereco_principal = (
        enderecos_qs.filter(principal=True).first()
        or enderecos_qs.first()
    )

    # ESCOLHER CHAVE PÚBLICA DO STRIPE (TESTE x PRODUÇÃO)
    if settings.STRIPE_LIVE_MODE:
        stripe_public_key = settings.STRIPE_LIVE_PUBLIC_KEY
    else:
        stripe_public_key = settings.STRIPE_TEST_PUBLIC_KEY

    return render(request, 'checkout.html', {
        'itens': itens,
        'total': total,
        'enderecos': enderecos_qs,
        'endereco': endereco_principal,      # usado nos value="{{ endereco.* }}"
        'usuario_nome': usuario.nome,
        'stripe_public_key': stripe_public_key,  # usado no JS
    })



# ============================================================
# MEUS PEDIDOS
# ============================================================

def meus_pedidos(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    pedidos = Pedido.objects.filter(usuario=usuario).order_by('-data_efetuado')

    # Calcula o total de cada pedido
    for pedido in pedidos:
        for item in pedido.itens.all():  # usa o related_name
            item.subtotal_valor = item.subtotal()
        pedido.total_valor = pedido.total()

    return render(request, 'meus_pedidos.html', {
        'pedidos': pedidos,
        'usuario_nome': usuario.nome
    })


# Configurar Stripe
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

#@login_required  # Comentar por enquanto para testar
def checkout_page(request):
    """Renderiza a página de checkout"""
    usuario_id = request.session.get('usuario_id')
    usuario_nome = request.session.get('usuario_nome')

    if usuario_id:
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            carrinho, created = Carrinho.objects.get_or_create(usuario=usuario)
            itens = carrinho.itens.all()
            total = carrinho.total()
            endereco = (
                usuario.enderecos.filter(principal=True).first()
                or usuario.enderecos.first()
            )


            print(f"✓ Usuário: {usuario.nome}")
            print(f"✓ Itens no carrinho: {itens.count()}")
            print(f"✓ Total: R$ {total}")

        except Usuario.DoesNotExist:
            print("✗ Usuário não encontrado")
            return redirect('login')
        except Exception as e:
            print(f"✗ Erro: {e}")
            itens = []
            total = 0
            endereco = None
    else:
        print("✗ Usuário não está logado")
        return redirect('login')

    context = {
        'itens': itens,
        'total': total,
        'endereco': endereco,
        'stripe_public_key': settings.STRIPE_TEST_PUBLIC_KEY,
        'usuario_nome': usuario_nome,
    }

    return render(request, 'checkout.html', context)


#@login_required

@require_POST
def create_checkout_session(request):
    """Cria uma Checkout Session no Stripe com suporte a PIX, frete e endereços do usuário."""
    try:
        usuario_id = request.session.get('usuario_id')

        if not usuario_id:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)

        usuario = Usuario.objects.get(id=usuario_id)

        # Pegar dados do formulário
        cep = request.POST.get('cep')
        rua = request.POST.get('rua')
        numero = request.POST.get('numero')
        bairro = request.POST.get('bairro')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        complemento = request.POST.get('complemento', '')
        metodo_pagamento = request.POST.get('pagamento', 'cartao')
        endereco_id = request.POST.get('endereco_id')  # pode vir vazio ou ser um ID

        # 🔹 NOVO: frete vindo do checkout.html
        frete_codigo = (request.POST.get('frete_codigo') or '').strip()  # ex: "PAC"
        frete_valor_str = (request.POST.get('frete_valor') or '').strip()  # ex: "24.9" ou "24.90"

        # Converter número para int de forma segura
        try:
            numero_int = int(numero) if numero else 0
        except (TypeError, ValueError):
            numero_int = 0

        # Descobrir/atualizar endereço escolhido
        endereco = None

        if endereco_id:
            # Usuário escolheu um endereço salvo
            endereco = Endereco.objects.filter(id=endereco_id, usuario=usuario).first()
            if endereco:
                # Atualiza com o que veio do form, se quiser manter sempre em dia
                endereco.cep = cep
                endereco.rua = rua
                endereco.numero = numero_int
                endereco.bairro = bairro
                endereco.cidade = cidade
                endereco.estado = estado
                endereco.complemento = complemento or None
                endereco.save()
        else:
            # Nenhum endereço escolhido – criar um novo (não necessariamente principal)
            endereco = Endereco.objects.create(
                usuario=usuario,
                apelido=None,
                cep=cep,
                rua=rua,
                numero=numero_int,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                complemento=complemento or None,
                principal=False if usuario.enderecos.exists() else True,
            )

        # Buscar itens do carrinho
        carrinho = Carrinho.objects.get(usuario=usuario)
        itens = carrinho.itens.all()

        if not itens:
            return JsonResponse({'error': 'Carrinho vazio'}, status=400)

        # Criar line_items (produtos)
        line_items = []
        for item in itens:
            preco_centavos = int(float(item.produto.preco_final()) * 100)

            product_data = {'name': item.produto.nome}
            if item.produto.descricao and item.produto.descricao.strip():
                product_data['description'] = item.produto.descricao[:500]

            line_items.append({
                'price_data': {
                    'currency': 'brl',
                    'product_data': product_data,
                    'unit_amount': preco_centavos,
                },
                'quantity': item.quantidade,
            })

        # 🔹 NOVO: adicionar o FRETE como mais um line_item (se tiver sido calculado)
        frete_centavos = 0
        if frete_valor_str:
            try:
                # troca vírgula por ponto se vier assim: "24,90"
                frete_decimal = Decimal(frete_valor_str.replace(',', '.'))
                if frete_decimal > 0:
                    frete_centavos = int(frete_decimal * 100)
            except (ValueError, ArithmeticError):
                frete_centavos = 0

        if frete_centavos > 0:
            line_items.append({
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': f"Frete {frete_codigo or ''}".strip() or "Frete",
                    },
                    'unit_amount': frete_centavos,
                },
                'quantity': 1,
            })

        # Definir métodos de pagamento baseado na escolha
        payment_method_types = ['pix'] if metodo_pagamento == 'pix' else ['card']

        # URLs
        domain_url = request.build_absolute_uri('/')[:-1]
        success_url = domain_url + '/pagamento/sucesso/?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = domain_url + '/checkout/'

        # Criar sessão Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=payment_method_types,
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(usuario.id),
            customer_email=usuario.email,
            metadata={
                'usuario_id': usuario.id,
                'metodo_pagamento': metodo_pagamento,
                'cep': cep,
                'rua': rua,
                'numero': numero,
                'bairro': bairro,
                'cidade': cidade,
                'estado': estado,
                'complemento': complemento,
                'endereco_id': str(endereco.id) if endereco else '',
                # 🔹 manter o frete salvo na sessão para uso no Pedido / debug
                'frete_codigo': frete_codigo,
                'frete_valor': frete_valor_str,
            },
        )

        return JsonResponse({'sessionId': checkout_session.id})

    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuário não encontrado'}, status=404)
    except Exception as e:
        print(f"Erro: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


def payment_success(request):
    """Página de sucesso após pagamento"""
    session_id = request.GET.get('session_id')
    usuario_nome = request.session.get('usuario_nome')

    if session_id:
        try:
            usuario_id = request.session.get('usuario_id')

            if not usuario_id:
                return redirect('login')

            usuario = Usuario.objects.get(id=usuario_id)

            # Recuperar sessão do Stripe
            session = stripe.checkout.Session.retrieve(session_id)

            # Verificar se o pagamento foi concluído
            if session.payment_status == 'paid':
                # Buscar carrinho
                carrinho = Carrinho.objects.get(usuario=usuario)
                itens_carrinho = carrinho.itens.all()

                # Verificar se o pagamento foi concluído
                if session.payment_status == 'paid':
                    # Descobrir endereço usado no checkout
                    meta = session.get('metadata', {}) or {}
                    endereco_id = meta.get('endereco_id')

                    endereco = None
                    if endereco_id:
                        endereco = Endereco.objects.filter(id=endereco_id, usuario=usuario).first()
                    if not endereco:
                        # fallback: principal ou primeiro endereço do usuário
                        endereco = (
                            Endereco.objects.filter(usuario=usuario, principal=True).first()
                            or Endereco.objects.filter(usuario=usuario).first()
                        )

                    # Buscar carrinho
                    carrinho = Carrinho.objects.get(usuario=usuario)
                    itens_carrinho = carrinho.itens.all()

                    # Criar pedido
                    pedido = Pedido.objects.create(
                        usuario=usuario,
                        endereco=endereco,
                        status='Pago'
                    )


                # Adicionar produtos ao pedido
                for item in itens_carrinho:
                    PedidoProduto.objects.create(
                        pedido=pedido,
                        produto=item.produto,
                        quantidade=item.quantidade,
                        preco_unitario=item.produto.preco_final()
                    )

                    # Atualizar estoque
                    item.produto.q_estoque -= item.quantidade
                    item.produto.save()

                # Limpar carrinho
                carrinho.itens.all().delete()

                context = {
                    'success': True,
                    'pedido': pedido,
                    'session_id': session_id,
                    'total': session.amount_total / 100,
                    'usuario_nome': usuario_nome,
                }
                return render(request, 'payment_success.html', context)
            else:
                context = {
                    'success': False,
                    'error': 'Pagamento ainda não foi concluído',
                    'usuario_nome': usuario_nome,
                }
                return render(request, 'payment_success.html', context)

        except Exception as e:
            context = {
                'success': False,
                'error': str(e),
                'usuario_nome': usuario_nome,
            }
            return render(request, 'payment_success.html', context)

    return redirect('home')

def _frete_simulado(peso_total: Decimal, cep_destino: str):
    """
    Fallback para TCC: se os Correios falharem, gera valores plausíveis.
    """
    peso_float = float(peso_total or Decimal('0.3'))

    base_pac = 15.0 + (peso_float * 5)      # ex: 0.3kg -> ~16.5
    base_sedex = base_pac + 10.0           # sedex um pouco mais caro

    return [
        {
            "codigo": "PAC",
            "nome": "PAC - (simulado)",
            "valor": round(base_pac, 2),
            "prazo_dias": 8,
        },
        {
            "codigo": "SEDEX",
            "nome": "SEDEX - (simulado)",
            "valor": round(base_sedex, 2),
            "prazo_dias": 3,
        },
    ]


@usuario_login_required
@require_POST
def calcular_frete(request):
    """
    Calcula frete usando:
      - CEP informado no POST (campo 'cep'), OU
      - CEP do endereço principal do usuário logado, se 'cep' não for enviado.

    Peso:
      - Se houver itens no carrinho => soma pesos do carrinho
      - Se carrinho estiver vazio, mas vier 'produto_id' => usa peso do produto * quantidade
      - Senão => peso padrão 0.3kg
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'Usuário não autenticado'}, status=401)

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuário não encontrado'}, status=404)

    # ========= CEP DESTINO =========
    cep_param = (request.POST.get('cep') or '').strip()

    if cep_param:
        cep_destino = ''.join(c for c in cep_param if c.isdigit())
    else:
        # Tentar CEP do endereço principal do usuário
        endereco = (
            usuario.enderecos.filter(principal=True).first()
            or usuario.enderecos.first()
        )

        if not endereco or not endereco.cep:
            return JsonResponse({
                'error': 'Informe um CEP ou cadastre um endereço com CEP para calcular o frete.'
            }, status=400)

        cep_destino = ''.join(c for c in endereco.cep if c.isdigit())

    if len(cep_destino) != 8:
        return JsonResponse({'error': 'CEP inválido.'}, status=400)

    # CEP de origem vem do settings
    cep_origem = getattr(settings, 'CORREIOS_CEP_ORIGEM', '01001000')

    # ========= PESO TOTAL =========
    peso_total = None

    # 1) Primeiro tenta pelo carrinho
    carrinho = Carrinho.objects.filter(usuario=usuario).first()
    if carrinho:
        itens = list(carrinho.itens.all())
        if itens:
            peso_total = Decimal('0.0')
            for item in itens:
                peso = getattr(item.produto, 'peso_kg', None)
                if not peso:
                    peso = Decimal('0.3')  # 300g default
                peso_total += peso * item.quantidade

    # 2) Se carrinho estiver vazio, tenta pelo produto_id enviado
    if peso_total is None:
        produto_id = request.POST.get('produto_id')
        qtd = request.POST.get('quantidade') or '1'
        try:
            qtd_int = int(qtd)
            if qtd_int <= 0:
                qtd_int = 1
        except ValueError:
            qtd_int = 1

        if produto_id:
            try:
                produto = Produto.objects.get(id=produto_id)
                peso = getattr(produto, 'peso_kg', None)
                if not peso:
                    peso = Decimal('0.3')
                peso_total = peso * qtd_int
            except Produto.DoesNotExist:
                pass

    # 3) Último fallback: peso padrão
    if peso_total is None:
        peso_total = Decimal('0.3')

    # ========= CHAMAR CORREIOS / FALLBACK =========
    opcoes = []

    try:
        opcoes = calcular_frete_correios(
            cep_origem=cep_origem,
            cep_destino=cep_destino,
            peso_kg=peso_total
        )
    except Exception as e:
        print('[FRETE] Exceção chamando Correios:', e)

    if not opcoes:
        print('[FRETE] Usando valores simulados de frete.')
        opcoes = _frete_simulado(peso_total, cep_destino)

    return JsonResponse({'success': True, 'opcoes': opcoes})

@csrf_exempt
def stripe_webhook(request):
    # Por enquanto só responde 200 pra não quebrar nada.
    # Depois a gente coloca a lógica do Stripe aqui.
    return HttpResponse(status=200)

#============================================================
# DASHBOARD ADMIN
#============================================================

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("admin_id"):
            return redirect("admin_login")
        return view_func(request, *args, **kwargs)
    return _wrapped

def _get_admin_username(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return "Admin"
    admin = AdminUser.objects.filter(id=admin_id).first()
    return admin.username if admin else "Admin"

@csrf_exempt
def admin_login(request):
    # Se já está logado como admin, manda pro dashboard
    if request.session.get("admin_id"):
        return redirect("admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        admin = None
        try:
            admin = AdminUser.objects.get(username=username)
        except AdminUser.DoesNotExist:
            admin = None

        if admin and admin.verify_password(password):
            request.session["admin_id"] = admin.id

            # Se for AJAX, responde JSON
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True})

            # Se for form normal, redireciona
            return redirect("admin_dashboard")
        else:
            # Se for AJAX, responde JSON de erro
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False})

            # Se for form normal, mostra erro na tela
            messages.error(request, "Usuário ou senha inválidos.")
            return render(request, "admin/loginadm.html", {"login_error": True})

    # GET
    return render(request, "admin/loginadm.html")

@admin_required
def admin_dashboard(request):
    admin_id = request.session.get("admin_id")
    admin_user = AdminUser.objects.filter(id=admin_id).first()

    usuarios = Usuario.objects.all()
    produtos = Produto.objects.all()
    pedidos = Pedido.objects.select_related('usuario').prefetch_related('itens__produto').order_by('-data_efetuado')

    receita_total = sum(p.total() for p in pedidos) if pedidos else 0
    usuarios_ativos = usuarios.count()
    produtos_cadastrados = produtos.count()
    hoje = now().date()
    pedidos_hoje = pedidos.filter(data_efetuado__date=hoje).count()

    for p in pedidos:
        p.total_valor = p.total()

    context = {
        'admin_username': admin_user.username if admin_user else 'Admin',
        'dash_receita_total': receita_total,
        'dash_usuarios_ativos': usuarios_ativos,
        'dash_produtos_cadastrados': produtos_cadastrados,
        'dash_pedidos_hoje': pedidos_hoje,
        'ultimas_transacoes': pedidos[:5],
    }
    return render(request, 'admin/adm.html', context)


def admin_logout(request):
    request.session.pop("admin_id", None)
    return redirect("admin_login")


@admin_required
def admin_planos(request):
    planos = Plano.objects.annotate(
        assinantes_count=Count('usuario')  # reverse de Usuario.plano
    )

    context = {
        "admin_username": _get_admin_username(request),
        "planos": planos,
    }
    return render(request, "admin/planos_list.html", context)


@admin_required
def admin_criar_plano(request):
    if request.method == 'POST':
        nome = (request.POST.get('nome') or '').strip()
        slug = (request.POST.get('slug') or '').strip().lower()
        descricao = (request.POST.get('descricao') or '').strip()
        preco_raw = (request.POST.get('preco_mensal') or '').strip()
        limite_raw = (request.POST.get('limite_anuncios') or '').strip()
        ativo = bool(request.POST.get('ativo'))
        is_default = bool(request.POST.get('is_default'))

        if not nome or not slug:
            messages.error(request, 'Nome e slug são obrigatórios para o plano.')
            return redirect('admin_dashboard')

        try:
            preco = Decimal(preco_raw.replace(',', '.')) if preco_raw else Decimal('0.00')
        except Exception:
            messages.error(request, 'Preço mensal inválido.')
            return redirect('admin_dashboard')

        limite = None
        if limite_raw:
            try:
                limite = int(limite_raw)
            except Exception:
                messages.error(request, 'Limite de anúncios inválido.')
                return redirect('admin_dashboard')

        # Se marcar como default, força regras do plano gratuito
        if is_default:
            Plano.objects.update(is_default=False)
            preco = Decimal('0.00')
            limite = 5

        Plano.objects.create(
            nome=nome,
            slug=slug,
            descricao=descricao or None,
            preco_mensal=preco,
            limite_anuncios=limite,
            ativo=ativo,
            is_default=is_default,
        )

        messages.success(request, 'Plano criado com sucesso.')
        return redirect('admin_dashboard')

    # GET → mostrar formulário vazio
    context = {
        'admin_username': _get_admin_username(request),
        'plano': None,
    }
    return render(request, 'admin/planos_form.html', context)


@admin_required
def admin_editar_plano(request, plano_id):
    plano = get_object_or_404(Plano, id=plano_id)

    if request.method == 'POST':
        nome = (request.POST.get('nome') or '').strip()
        slug = (request.POST.get('slug') or '').strip().lower()
        descricao = (request.POST.get('descricao') or '').strip()
        preco_raw = (request.POST.get('preco_mensal') or '').strip()
        limite_raw = (request.POST.get('limite_anuncios') or '').strip()
        ativo = bool(request.POST.get('ativo'))
        is_default = bool(request.POST.get('is_default'))

        if not nome or not slug:
            messages.error(request, 'Nome e slug são obrigatórios para o plano.')
            return redirect('admin_dashboard')

        try:
            preco = Decimal(preco_raw.replace(',', '.')) if preco_raw else Decimal('0.00')
        except Exception:
            messages.error(request, 'Preço mensal inválido.')
            return redirect('admin_dashboard')

        limite = None
        if limite_raw:
            try:
                limite = int(limite_raw)
            except Exception:
                messages.error(request, 'Limite de anúncios inválido.')
                return redirect('admin_dashboard')

        plano.nome = nome
        plano.slug = slug
        plano.descricao = descricao or None
        plano.ativo = ativo

        if plano.is_default:
            # Se já é o plano padrão, mantém regras de gratuito
            plano.preco_mensal = Decimal('0.00')
            plano.limite_anuncios = 5
            plano.is_default = True
        else:
            if is_default:
                # Tornar esse o novo default gratuito
                Plano.objects.exclude(id=plano.id).update(is_default=False)
                plano.is_default = True
                plano.preco_mensal = Decimal('0.00')
                plano.limite_anuncios = 5
            else:
                plano.is_default = False
                plano.preco_mensal = preco
                plano.limite_anuncios = limite

        plano.save()
        messages.success(request, 'Plano atualizado com sucesso.')
        return redirect('admin_dashboard')

    # GET → mostrar formulário preenchido
    context = {
        'admin_username': _get_admin_username(request),
        'plano': plano,
    }
    return render(request, 'admin/planos_form.html', context)


@admin_required
def admin_excluir_plano(request, plano_id):
    plano = get_object_or_404(Plano, id=plano_id)

    if plano.is_default:
        messages.error(request, 'Você não pode excluir o plano gratuito padrão.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        plano.delete()
        messages.success(request, 'Plano excluído com sucesso.')
        return redirect('admin_dashboard')

    # GET → tela de confirmação
    context = {
        'admin_username': _get_admin_username(request),
        'plano': plano,
    }
    return render(request, 'admin/planos_confirm_delete.html', context)


@admin_required
def admin_toggle_plano_ativo(request, plano_id):
    """
    Ativar / desativar plano.
    - Se desativar um plano (não padrão), todos os usuários desse plano
      são movidos para o plano padrão gratuito.
    """
    if request.method != "POST":
        return redirect("admin_planos")

    plano = get_object_or_404(Plano, id=plano_id)

    # Não permitir desativar o plano padrão
    if plano.is_default and plano.ativo:
        messages.error(request, "Você não pode desativar o plano gratuito padrão.")
        return redirect("admin_planos")

    # Se for desativar (estava ativo -> vai para inativo)
    if plano.ativo:
        # procura o plano padrão (ativo), pode ser sempre o Free Pigeon Basic
        plano_default = (
            Plano.objects.filter(is_default=True, ativo=True)
            .exclude(id=plano.id)
            .first()
        )

        if not plano_default:
            messages.error(
                request,
                "Nenhum outro plano padrão ativo encontrado para mover os usuários."
            )
            return redirect("admin_planos")

        # move usuários para o plano padrão
        qtd = Usuario.objects.filter(plano=plano).update(plano=plano_default)

        plano.ativo = False
        plano.save()

        messages.info(
            request,
            f"Plano '{plano.nome}' desativado. {qtd} usuário(s) movidos para '{plano_default.nome}'."
        )
    else:
        # Ativando o plano novamente
        plano.ativo = True
        plano.save()
        messages.success(request, f"Plano '{plano.nome}' foi ativado.")

    return redirect("admin_planos")


@admin_required
def admin_categorias(request):
    categorias = Categoria.objects.annotate(
        produtos_count=Count('produto')  # Produto tem FK categoria → nome do modelo minúsculo
    )

    context = {
        "admin_username": _get_admin_username(request),
        "categorias": categorias,
    }
    return render(request, "admin/categorias_list.html", context)


@admin_required
def admin_criar_categoria(request):
    if request.method == 'POST':
        nome = (request.POST.get('nome') or '').strip()
        imagem = request.FILES.get('imagem')

        if not nome:
            messages.error(request, 'O nome da categoria é obrigatório.')
            return redirect('admin_categorias')

        Categoria.objects.create(
            nome=nome,
            imagem=imagem
        )

        messages.success(request, 'Categoria criada com sucesso.')
        return redirect('admin_categorias')

    # GET → exibe formulário vazio
    context = {
        "admin_username": _get_admin_username(request),
        "categoria": None,
    }
    return render(request, "admin/categorias_form.html", context)


@admin_required
def admin_editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if request.method == 'POST':
        nome = (request.POST.get('nome') or '').strip()
        imagem = request.FILES.get('imagem')

        if not nome:
            messages.error(request, 'O nome da categoria é obrigatório.')
            return redirect('admin_categorias')

        categoria.nome = nome
        if imagem:
            categoria.imagem = imagem
        categoria.save()

        messages.success(request, 'Categoria atualizada com sucesso.')
        return redirect('admin_categorias')

    # GET → exibe formulário preenchido
    context = {
        "admin_username": _get_admin_username(request),
        "categoria": categoria,
    }
    return render(request, "admin/categorias_form.html", context)


@admin_required
def admin_excluir_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoria excluída com sucesso.')
        return redirect('admin_categorias')

    # GET → tela de confirmação
    context = {
        "admin_username": _get_admin_username(request),
        "categoria": categoria,
    }
    return render(request, "admin/categorias_confirm_delete.html", context)

@admin_required
def admin_usuarios(request):
    """
    Lista usuários com filtro de status (ativo/inativo/todos) e busca por nome/email.
    """
    q = (request.GET.get("q") or "").strip()
    status = request.GET.get("status") or "todos"  # 'ativo', 'inativo', 'todos'

    usuarios_qs = Usuario.objects.select_related("loja", "plano")

    if q:
        usuarios_qs = usuarios_qs.filter(
            Q(nome__icontains=q) |
            Q(email__icontains=q)
        )

    if status == "ativo":
        usuarios_qs = usuarios_qs.filter(ativo=True)
    elif status == "inativo":
        usuarios_qs = usuarios_qs.filter(ativo=False)

    usuarios_qs = usuarios_qs.order_by("nome")

    context = {
        "admin_username": _get_admin_username(request),
        "usuarios": usuarios_qs,
        "filtro_q": q,
        "filtro_status": status,
    }
    return render(request, "admin/usuarios_list.html", context)


@admin_required
def admin_toggle_usuario_ativo(request, usuario_id):
    """
    Alterna o status ativo/inativo de um usuário.
    """
    if request.method != "POST":
        return redirect("admin_usuarios")

    usuario = get_object_or_404(Usuario, id=usuario_id)
    usuario.ativo = not usuario.ativo
    usuario.save()

    if usuario.ativo:
        messages.success(request, f"O usuário '{usuario.nome}' foi ativado.")
    else:
        messages.info(request, f"O usuário '{usuario.nome}' foi desativado.")

    # mantém filtros atuais na volta, se quiser dar upgrade depois com querystring
    return redirect("admin_usuarios")


@admin_required
def admin_usuario_detalhe(request, usuario_id):
    """
    Mostra todos os dados possíveis de um usuário:
    - dados básicos
    - plano
    - loja
    - endereços
    - produtos criados por ele (como vendedor e via loja dele)
    - pedidos feitos por ele
    """
    usuario = get_object_or_404(
        Usuario.objects.select_related("plano", "loja"),
        id=usuario_id
    )

    # Endereços
    enderecos = usuario.enderecos.all().order_by("-principal", "id")

    # Produtos criados pelo usuário
    produtos = Produto.objects.filter(
        Q(vendedor=usuario) |
        Q(loja=usuario.loja)
    ).select_related("categoria", "loja")

    # Pedidos do usuário
    pedidos = (
        Pedido.objects
        .filter(usuario=usuario)
        .prefetch_related("itens__produto")
        .order_by("-data_efetuado")
    )

    # enriquecer pedidos com total e resumo
    for p in pedidos:
        p.total_valor = p.total()
        itens = list(p.itens.all())
        if itens:
            nomes = [f"{item.produto.nome} (x{item.quantidade})" for item in itens]
            if len(nomes) > 2:
                p.produtos_resumo = ", ".join(nomes[:2]) + f" + {len(nomes) - 2} itens"
            else:
                p.produtos_resumo = ", ".join(nomes)
        else:
            p.produtos_resumo = "-"

    context = {
        "admin_username": _get_admin_username(request),
        "usuario_alvo": usuario,
        "enderecos": enderecos,
        "produtos": produtos,
        "pedidos": pedidos,
    }
    return render(request, "admin/usuario_detalhe.html", context)

@admin_required
def admin_toggle_usuario_ativo(request, usuario_id):
    if request.method != "POST":
        return redirect("admin_usuarios")

    usuario = get_object_or_404(Usuario, id=usuario_id)
    usuario.ativo = not usuario.ativo
    usuario.save()

    if usuario.ativo:
        messages.success(request, f"O usuário '{usuario.nome}' foi ativado.")
    else:
        messages.info(request, f"O usuário '{usuario.nome}' foi desativado.")

    return redirect("admin_usuarios")


@admin_required
def admin_produtos(request):
    """
    Lista todos os produtos com filtro de status e busca.
    """
    q = (request.GET.get("q") or "").strip()
    status = request.GET.get("status") or "todos"  # 'ativo', 'inativo', 'todos'

    produtos_qs = Produto.objects.select_related("categoria", "loja", "vendedor")

    if q:
        produtos_qs = produtos_qs.filter(
            Q(nome__icontains=q) |
            Q(vendedor__nome__icontains=q) |
            Q(loja__nome__icontains=q)
        )

    if status == "ativo":
        produtos_qs = produtos_qs.filter(ativo=True)
    elif status == "inativo":
        produtos_qs = produtos_qs.filter(ativo=False)

    produtos_qs = produtos_qs.order_by("-id")

    context = {
        "admin_username": _get_admin_username(request),
        "produtos": produtos_qs,
        "filtro_q": q,
        "filtro_status": status,
    }
    return render(request, "admin/produtos_list.html", context)


@admin_required
def admin_toggle_produto_ativo(request, produto_id):
    """
    Alterna o campo 'ativo' do produto (Ativo <-> Inativo).
    Apenas via POST.
    """
    if request.method != "POST":
        return redirect('admin_produtos')

    produto = get_object_or_404(Produto, id=produto_id)
    produto.ativo = not produto.ativo
    produto.save()

    if produto.ativo:
        messages.success(request, f"O produto '{produto.nome}' foi ativado.")
    else:
        messages.info(request, f"O produto '{produto.nome}' foi desativado.")

    return redirect('admin_produtos')


@admin_required
def admin_produto_detalhe(request, produto_id):
    """
    Detalhes de um produto:
    - dados básicos
    - categoria
    - vendedor/loja
    - atributos
    - pedidos em que aparece + resumo de vendas
    """
    produto = get_object_or_404(
        Produto.objects.select_related("categoria", "loja", "vendedor"),
        id=produto_id
    )

    # Atributos dinâmicos
    atributos = produto.atributos.select_related("atributo").all()

    # Pedidos em que este produto aparece
    itens_pedido = (
        PedidoProduto.objects
        .select_related("pedido", "pedido__usuario")
        .filter(produto=produto)
        .order_by("-pedido__data_efetuado")
    )

    # Resumo de vendas desse produto
    resumo = itens_pedido.aggregate(
        total_quantidade=Sum("quantidade"),
        total_faturado=Sum(F("quantidade") * F("preco_unitario")),
    )

    total_quantidade = resumo["total_quantidade"] or 0
    total_faturado = resumo["total_faturado"] or 0

    context = {
        "admin_username": _get_admin_username(request),
        "produto": produto,
        "atributos": atributos,
        "itens_pedido": itens_pedido,
        "total_quantidade_vendida": total_quantidade,
        "total_faturado_produto": total_faturado,
    }
    return render(request, "admin/produto_detalhe.html", context)

@admin_required
def admin_transacoes(request):
    # Carrega pedidos com usuário e itens/produtos
    pedidos = (
        Pedido.objects
        .select_related('usuario')
        .prefetch_related('itens__produto')
        .order_by('-data_efetuado')
    )

    # Total de transações (quantidade)
    total_transacoes = pedidos.count()

    # Total em dinheiro (somando Pedido.total())
    total_valor = Decimal('0.00')
    for p in pedidos:
        total_valor += p.total()

    # Enriquecer cada pedido com total_valor e um resumo de produtos
    for p in pedidos:
        p.total_valor = p.total()

        itens = list(p.itens.all())
        if itens:
            nomes = [f"{item.produto.nome} (x{item.quantidade})" for item in itens]
            if len(nomes) > 2:
                p.produtos_resumo = ", ".join(nomes[:2]) + f" + {len(nomes) - 2} itens"
            else:
                p.produtos_resumo = ", ".join(nomes)
        else:
            p.produtos_resumo = "-"

    context = {
        "admin_username": _get_admin_username(request),
        "pedidos": pedidos,
        "total_transacoes": total_transacoes,
        "total_valor": total_valor,
    }
    return render(request, "admin/transacoes_list.html", context)