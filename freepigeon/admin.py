from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Usuario)
admin.site.register(Produto)
admin.site.register(Categoria)
admin.site.register(Loja)
admin.site.register(Pedido)
admin.site.register(Carrinho)
admin.site.register(CarrinhoProduto)
admin.site.register(Endereco)
admin.site.register(PedidoProduto)