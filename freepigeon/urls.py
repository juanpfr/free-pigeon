from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),

    # autenticação
    path('cadastro/', views.cadastrar_usuario, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/', views.auth_view, name='auth'),

    # 🔹 login com Google (pós-login / ponte)
    path('google/login/redirect/', views.google_login_redirect, name='google_login_redirect'),

    # 🔹 URLs do social_django (onde o botão chama 'social:begin')
    path('oauth/', include('social_django.urls', namespace='social')),

    # perfil do usuário
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/alterar-senha/', views.alterar_senha, name='alterar_senha'),

    path('perfil/enderecos/', views.enderecos, name='enderecos'),
    path('perfil/enderecos/<int:endereco_id>/editar/', views.editar_endereco, name='editar_endereco'),
    path('perfil/enderecos/<int:endereco_id>/excluir/', views.excluir_endereco, name='excluir_endereco'),
    path('perfil/enderecos/<int:endereco_id>/principal/', views.definir_endereco_principal, name='definir_endereco_principal'),

    path('vender/', views.vender, name='vender'),
    path('anuncios/', views.anuncios, name='anuncios'),
    path('resumo/', views.resumo, name='resumo'),
    path('loja/criar/', views.criar_loja, name='criar_loja'),
    path('produto/novo/', views.cadastrar_produto, name='cadastrar_produto'),

    # produtos e categorias
    path('produto/<int:produto_id>/', views.produto_view, name='produto'),
    path('categoria/<int:categoria_id>/', views.categoria_view, name='categoria'),
    path('buscar/', views.buscar_produtos, name='buscar'),

    # carrinho
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('carrinho/adicionar/<int:produto_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('carrinho/remover/<int:produto_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),

    # checkout / pedidos
    path('checkout/', views.checkout_page, name='checkout'),  # ← MUDOU (era checkout_view)
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),

    # stripe - Checkout Session
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),  # ← NOVO
    path('pagamento/sucesso/', views.payment_success, name='payment_success'),  # ← NOVO
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('stripe/', include('djstripe.urls', namespace='djstripe')),
]
