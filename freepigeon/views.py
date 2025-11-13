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

import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Usuario, Carrinho, CarrinhoProduto, Pedido, PedidoProduto, Endereco

# Configurar Stripe
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

#@login_required  # Comentar por enquanto para testar
def checkout_page(request):
    """Renderiza a página de checkout"""
    
    usuario_id = request.session.get('usuario_id')
    usuario_nome = request.session.get('usuario_nome')  # ← ADICIONAR
    
    if usuario_id:
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            carrinho, created = Carrinho.objects.get_or_create(usuario=usuario)
            itens = carrinho.itens.all()
            total = carrinho.total()
            endereco = usuario.endereco
            
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
    else:
        print("✗ Usuário não está logado")
        return redirect('login')
    
    context = {
        'itens': itens,
        'total': total,
        'endereco': endereco,
        'stripe_public_key': settings.STRIPE_TEST_PUBLIC_KEY,
        'usuario_nome': usuario_nome,  # ← ADICIONAR AQUI
    }
    
    return render(request, 'checkout.html', context)


#@login_required
@require_POST
def create_checkout_session(request):
    """Cria uma Checkout Session no Stripe"""
    try:
        # Buscar usuário da sessão
        usuario_id = request.session.get('usuario_id')
        
        if not usuario_id:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        usuario = Usuario.objects.get(id=usuario_id)
        
        # Pegar dados do endereço do formulário
        cep = request.POST.get('cep')
        rua = request.POST.get('rua')
        numero = request.POST.get('numero')
        bairro = request.POST.get('bairro')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        complemento = request.POST.get('complemento', '')
        
        # Salvar ou atualizar endereço do usuário
        if usuario.endereco:
            endereco = usuario.endereco
            endereco.cep = cep
            endereco.rua = rua
            endereco.numero = numero
            endereco.bairro = bairro
            endereco.cidade = cidade
            endereco.estado = estado
            endereco.complemento = complemento
            endereco.save()
        else:
            endereco = Endereco.objects.create(
                cep=cep,
                rua=rua,
                numero=numero,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                complemento=complemento
            )
            usuario.endereco = endereco
            usuario.save()
        
        # Buscar carrinho e itens
        carrinho = Carrinho.objects.get(usuario=usuario)
        itens = carrinho.itens.all()
        
        if not itens:
            return JsonResponse({'error': 'Carrinho vazio'}, status=400)
        
        # Criar line_items para o Stripe
        line_items = []
        for item in itens:
            preco_centavos = int(float(item.produto.preco_final()) * 100)
            
            # Preparar product_data
            product_data = {
                'name': item.produto.nome,
            }
            
            # APENAS adicionar descrição se ela existir e não for vazia
            if item.produto.descricao and item.produto.descricao.strip():
                product_data['description'] = item.produto.descricao[:500]
            
            # Adicionar imagem se existir
            if item.produto.imagem:
                try:
                    image_url = request.build_absolute_uri(item.produto.imagem.url)
                    product_data['images'] = [image_url]
                except:
                    pass
            
            line_items.append({
                'price_data': {
                    'currency': 'brl',
                    'product_data': product_data,  # ← Usar o dict preparado
                    'unit_amount': preco_centavos,
                },
                'quantity': item.quantidade,
            })
        
        # URLs de retorno
        domain_url = request.build_absolute_uri('/')[:-1]
        success_url = domain_url + '/pagamento/sucesso/?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = domain_url + '/checkout/'
        
        # Criar Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(usuario.id),
            customer_email=usuario.email,
            metadata={
                'usuario_id': usuario.id,
                'cep': cep,
                'rua': rua,
                'numero': numero,
                'bairro': bairro,
                'cidade': cidade,
                'estado': estado,
                'complemento': complemento,
            },
        )
        
        return JsonResponse({'sessionId': checkout_session.id})
        
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuário não encontrado'}, status=404)
    except Exception as e:
        print(f"Erro ao criar checkout session: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

def payment_success(request):
    """Página de sucesso após pagamento"""
    session_id = request.GET.get('session_id')
    
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
                
                # Criar pedido
                pedido = Pedido.objects.create(
                    usuario=usuario,
                    endereco=usuario.endereco,
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
                }
                return render(request, 'payment_success.html', context)
            else:
                context = {
                    'success': False,
                    'error': 'Pagamento ainda não foi concluído'
                }
                return render(request, 'payment_success.html', context)
            
        except Exception as e:
            context = {
                'success': False,
                'error': str(e)
            }
            return render(request, 'payment_success.html', context)
    
    return redirect('home')

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Processa webhooks do Stripe"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.DJSTRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        usuario_id = session.get('metadata', {}).get('usuario_id')
        
        print(f"✓ Checkout concluído para usuário ID {usuario_id}")
        print(f"  Session ID: {session['id']}")
        print(f"  Payment Status: {session['payment_status']}")
    
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"✓ Pagamento {payment_intent['id']} bem-sucedido!")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        print(f"✗ Pagamento {payment_intent['id']} falhou!")
    
    return HttpResponse(status=200)
