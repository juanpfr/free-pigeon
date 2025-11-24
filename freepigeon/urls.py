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
