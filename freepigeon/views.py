from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.contrib.auth import logout
from .models import Usuario, Categoria, Produto, Carrinho, CarrinhoProduto, Pedido, PedidoProduto, Endereco

# ============================================================
# USUÁRIO / LOGIN / LOGOUT / CADASTRO
# ============================================================

def cadastrar_usuario(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cpf = request.POST.get('cpf')
        senha = request.POST.get('senha')

        # Validações
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'E-mail já cadastrado!')
            return render(request, 'cadastro.html')
        if Usuario.objects.filter(cpf=cpf).exists():
            messages.error(request, 'CPF já cadastrado!')
            return render(request, 'cadastro.html')

        # Cria usuário
        Usuario.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            cpf=cpf,
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


def auth_view(request):
    return render(request, 'auth.html')


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
# CHECKOUT / PEDIDO
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

    if request.method == 'POST':
        endereco_id = request.POST.get('endereco_id')
        endereco = Endereco.objects.filter(id=endereco_id).first() if endereco_id else None

        pedido = Pedido.objects.create(
            usuario=usuario,
            endereco=endereco,
            status='Pendente'
        )

        for item in itens:
            PedidoProduto.objects.create(
                pedido=pedido,
                produto=item.produto,
                quantidade=item.quantidade,
                preco_unitario=item.produto.preco_final()
            )

        carrinho.delete()  # limpa o carrinho

        return redirect('meus_pedidos')

    enderecos = Endereco.objects.filter(usuario=usuario.id) if hasattr(Endereco, 'usuario') else [usuario.endereco] if usuario.endereco else []
    return render(request, 'checkout.html', {
        'itens': itens,
        'total': total,
        'enderecos': enderecos,
        'usuario_nome': usuario.nome
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

# ============================================================
# ViaCEP
# ============================================================

from django.shortcuts import render
from .utils import buscar_cep

def busca_cep_view(request):
    endereco = None
    erro = None

    if request.method == "POST":
        cep = request.POST.get("cep")
        endereco = buscar_cep(cep)
        if not endereco:
            erro = "CEP não encontrado ou inválido."

    return render(request, "cep/busca_cep.html", {"endereco": endereco, "erro": erro})
