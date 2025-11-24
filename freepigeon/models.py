from django.db import models


# =========================
# TABELA: Endereco
# =========================
class Endereco(models.Model):
    complemento = models.CharField(max_length=255, blank=True, null=True)
    rua = models.CharField(max_length=255)
    numero = models.IntegerField()
    bairro = models.CharField(max_length=255)
    cidade = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    cep = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.rua}, {self.numero} - {self.cidade}"


# =========================
# TABELA: Loja
# =========================
class Loja(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


# =========================
# TABELA: Usuario
# =========================
class Usuario(models.Model):
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)  # 🔹 agora opcional
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)  # 🔹 agora opcional
    senha = models.CharField(max_length=255)
    loja = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True)
    endereco = models.ForeignKey(Endereco, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome


# =========================
# TABELA: Categoria
# =========================
class Categoria(models.Model):
    nome = models.CharField(max_length=255)
    imagem = models.ImageField(upload_to='categorias/', blank=True, null=True)

    def __str__(self):
        return self.nome


# =========================
# TABELA: Produto
# =========================
class Produto(models.Model):
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    q_estoque = models.IntegerField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    # 🔹 agora é opcional vincular a uma loja
    loja = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True)

    # 🔹 novo: produto pode ser vinculado diretamente ao usuário vendedor
    vendedor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='produtos',
        null=True,
        blank=True
    )

    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)

    def __str__(self):
        return self.nome

    def preco_final(self):
        if self.desconto:
            return self.valor * (1 - self.desconto / 100)
        return self.valor

# =========================
# TABELAS DE ATRIBUTOS DINÂMICOS
# =========================
class Atributo(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


class ProdutoAtributo(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='atributos')
    atributo = models.ForeignKey(Atributo, on_delete=models.CASCADE)
    valor = models.CharField(max_length=255)

    class Meta:
        unique_together = ('produto', 'atributo')

    def __str__(self):
        return f"{self.produto.nome} - {self.atributo.nome}: {self.valor}"


# =========================
# TABELA: Carrinho
# =========================
class Carrinho(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True, null=True)

    def total(self):
        total = sum(item.subtotal() for item in self.itens.all())
        return total

    def __str__(self):
        return f"Carrinho de {self.usuario.nome}"


class CarrinhoProduto(models.Model):
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('carrinho', 'produto')

    def subtotal(self):
        return self.produto.preco_final() * self.quantidade

    def __str__(self):
        return f"{self.produto.nome} (x{self.quantidade})"


# =========================
# TABELA: Pedido
# =========================
class Pedido(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    endereco = models.ForeignKey(Endereco, on_delete=models.SET_NULL, null=True)
    data_efetuado = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Pendente')

    def total(self):
        return sum(item.subtotal() for item in self.itens.all())

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.nome}"


class PedidoProduto(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.preco_unitario * self.quantidade

    def __str__(self):
        return f"{self.produto.nome} (x{self.quantidade})"
