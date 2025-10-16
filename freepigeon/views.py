from django.shortcuts import render
from .models import Usuario

def cadastrar_usuario(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cpf = request.POST.get('cpf')
        senha = request.POST.get('senha')

        Usuario.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            cpf=cpf,
            senha=senha
        )

        return render(request, 'cadastro.html', {'mensagem': 'Usuário cadastrado com sucesso!'})

    return render(request, 'cadastro.html')
