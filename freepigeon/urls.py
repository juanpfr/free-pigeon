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

    # planos
    path('planos/', views.planos, name='planos'),
    path('planos/checkout/', views.create_plan_checkout_session, name='planos_checkout'),
    path('planos/sucesso/', views.plan_success, name='planos_sucesso'),


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
    path('anuncios/<int:produto_id>/editar/', views.editar_anuncio, name='editar_anuncio'),
    path('anuncios/<int:produto_id>/excluir/', views.excluir_anuncio, name='excluir_anuncio'),
    path('anuncios/<int:produto_id>/status/', views.toggle_status_anuncio, name='toggle_status_anuncio'),

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
    path('checkout/', views.checkout_view, name='checkout'),
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),

    # stripe - Checkout Session
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),  # ← NOVO
    path('pagamento/sucesso/', views.payment_success, name='payment_success'),  # ← NOVO
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('stripe/', include('djstripe.urls', namespace='djstripe')),

    # Frete
    path('calcular-frete/', views.calcular_frete, name='calcular_frete'),

    # -------------------------
    # ADMIN
    # -------------------------
    path('adm/login', views.admin_login, name='admin_login'),
    path('adm/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('adm/logout/', views.admin_logout, name='admin_logout'),

    # Planos
    path('adm/planos/', views.admin_planos, name='admin_planos'),
    path('adm/planos/criar/', views.admin_criar_plano, name='admin_criar_plano'),
    path('adm/planos/<int:plano_id>/editar/', views.admin_editar_plano, name='admin_editar_plano'),
    path('adm/planos/<int:plano_id>/excluir/', views.admin_excluir_plano, name='admin_excluir_plano'),
    path('adm/planos/<int:plano_id>/toggle/', views.admin_toggle_plano_ativo, name='admin_toggle_plano_ativo'),


    # Categorias
    path('adm/categorias/', views.admin_categorias, name='admin_categorias'),
    path('adm/categorias/criar/', views.admin_criar_categoria, name='admin_criar_categoria'),
    path('adm/categorias/<int:categoria_id>/editar/', views.admin_editar_categoria, name='admin_editar_categoria'),
    path('adm/categorias/<int:categoria_id>/excluir/', views.admin_excluir_categoria, name='admin_excluir_categoria'),


    # Usuários
    path("adm/usuarios/", views.admin_usuarios, name="admin_usuarios"),
    path("adm/usuarios/<int:usuario_id>/toggle/", views.admin_toggle_usuario_ativo, name="admin_toggle_usuario_ativo"),
    path("adm/usuarios/<int:usuario_id>/", views.admin_usuario_detalhe, name="admin_usuario_detalhe"),



    # Produtos
    path('adm/produtos/', views.admin_produtos, name='admin_produtos'),
    path('adm/produtos/<int:produto_id>/toggle/', views.admin_toggle_produto_ativo, name='admin_toggle_produto_ativo'),
    path('adm/produtos/<int:produto_id>/', views.admin_produto_detalhe, name='admin_produto_detalhe'),


    # Transações
    path('adm/transacoes/', views.admin_transacoes, name='admin_transacoes'),
]
