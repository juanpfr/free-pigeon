# ===============================
# IMPORTS GERAIS
# ===============================
import stripe
import re
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
from django.db.models import Q
from django.contrib.auth.decorators import login_required


# ===============================
# MODELOS
# ===============================
from .models import (
    Usuario, Loja, Categoria, Produto,
    Carrinho, CarrinhoProduto,
    Pedido, PedidoProduto,
    Endereco
)

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
        telefone = so_digitos(request.POST.get('telefone')) or None
        cpf = so_digitos(request.POST.get('cpf')) or None
        senha = request.POST.get('senha')

        # Validações
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'E-mail já cadastrado!')
            return render(request, 'cadastro.html')

        # CPF agora é opcional: só valida se tiver sido preenchido
        if cpf and Usuario.objects.filter(cpf=cpf).exists():
            messages.error(request, 'CPF já cadastrado!')
            return render(request, 'cadastro.html')

        # Cria usuário
        Usuario.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            cpf=cpf,  # pode ser None
            senha=make_password(senha)
        )

        # Redireciona para login
        return redirect('login')

    return render(request, 'cadastro.html')


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
    return redirect('login')


def google_login_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')

    email = request.user.email
    nome = (
        request.user.get_full_name()
        or getattr(request.user, 'first_name', '')
        or (email.split('@')[0] if email else 'Usuário')
    )

    usuario, created = Usuario.objects.get_or_create(
        email=email,
        defaults={
            'nome': nome,
            'telefone': None,
            'cpf': None,
            'senha': make_password(None),
        }
    )

    request.session['usuario_id'] = usuario.id
    request.session['usuario_nome'] = usuario.nome

    return redirect('home')


def auth_view(request):
    return render(request, 'auth.html')


# ============================================================
# PERFIL / ÁREA DO VENDEDOR
# ============================================================

@login_required(login_url='login')
def perfil(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

    # produtos que ele vende como pessoa física (sem loja)
    produtos_pessoais = Produto.objects.filter(vendedor=usuario, loja__isnull=True).count()

    # produtos vinculados à loja (se tiver loja)
    produtos_loja = 0
    if usuario.loja:
        produtos_loja = Produto.objects.filter(loja=usuario.loja).count()

    enderecos = usuario.enderecos.all().order_by('-principal', 'id')

    return render(request, 'perfil.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
        'produtos_pessoais': produtos_pessoais,
        'produtos_loja': produtos_loja,
        'enderecos': enderecos,
    })


@login_required(login_url='login')
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


@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
def definir_endereco_principal(request, endereco_id):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    endereco = get_object_or_404(Endereco, id=endereco_id, usuario=usuario)

    usuario.enderecos.update(principal=False)
    endereco.principal = True
    endereco.save()
    messages.success(request, 'Endereço definido como principal.')
    return redirect('enderecos')


@login_required(login_url='login')
def vender(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    return render(request, 'vender.html', {
        'usuario': usuario,
        'usuario_nome': usuario.nome,
    })


@login_required(login_url='login')
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


@login_required(login_url='login')
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

@login_required(login_url='login')
def criar_loja(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)

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

@login_required(login_url='login')
def cadastrar_produto(request):
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
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

    usuario = Usuario.objects.get(id=usuario_id)
    carrinho, created = Carrinho.objects.get_or_create(usuario=usuario)
    itens = CarrinhoProduto.objects.filter(carrinho=carrinho)
    total = sum(item.subtotal() for item in itens)
    return render(request, 'cart.html', {
        'itens': itens,
        'total': total,
        'usuario_nome': usuario.nome
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
    """Cria uma Checkout Session no Stripe com suporte a PIX e endereços do usuário."""
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
                # Se quiser, pode atualizar com o que veio do form
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
                principal=False if usuario.enderecos.exists() else True,  # se for o primeiro, já marca principal
            )

        # Buscar itens do carrinho
        carrinho = Carrinho.objects.get(usuario=usuario)
        itens = carrinho.itens.all()

        if not itens:
            return JsonResponse({'error': 'Carrinho vazio'}, status=400)

        # Criar line_items
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


@login_required(login_url='login')
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