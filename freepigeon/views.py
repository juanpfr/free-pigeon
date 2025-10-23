from django.shortcuts import render, redirect
from .models import Usuario
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.contrib.auth import logout

def cadastrar_usuario(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cpf = request.POST.get('cpf')
        senha = request.POST.get('senha')

        # Verifica se já existe usuário com esse email ou CPF
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'E-mail já cadastrado!')
            return render(request, 'cadastro.html')
        if Usuario.objects.filter(cpf=cpf).exists():
            messages.error(request, 'CPF já cadastrado!')
            return render(request, 'cadastro.html')

        Usuario.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            cpf=cpf,
            senha=make_password(senha)  # ← senha criptografada
        )

        return render(request, 'cadastro.html', {'mensagem': 'Usuário cadastrado com sucesso!'})

    return render(request, 'cadastro.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        senha = request.POST.get('senha')

        # tenta achar usuário por email ou cpf
        try:
            usuario = Usuario.objects.get(email=username)
        except Usuario.DoesNotExist:
            try:
                usuario = Usuario.objects.get(cpf=username)
            except Usuario.DoesNotExist:
                usuario = None

        if usuario and check_password(senha, usuario.senha):
            # Login bem-sucedido — salva na sessão
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nome'] = usuario.nome
            return redirect('home')
        else:
            return render(request, 'login.html', {'mensagem_erro': 'Usuário ou senha inválidos.'})

    return render(request, 'login.html')


def home_view(request):
    usuario_nome = request.session.get('usuario_nome')
    return render(request, 'home.html', {'usuario_nome': usuario_nome})


def logout_view(request):
    logout(request)
    return redirect('login')