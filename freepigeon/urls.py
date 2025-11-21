from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),

    # autenticação
    path('cadastro/', views.cadastrar_usuario, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/', views.auth_view, name='auth'),

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
    path("buscar-cep/", views.busca_cep_view, name="buscar_cep"),
]
