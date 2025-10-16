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
# TABELA: Carrinho
# =========================
class Carrinho(models.Model):
    data_adicao = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Carrinho #{self.id}"


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
    telefone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, unique=True)
    senha = models.CharField(max_length=255)
    loja = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True)
    endereco = models.ForeignKey(Endereco, on_delete=models.SET_NULL, null=True, blank=True)
    carrinho = models.OneToOneField(Carrinho, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome


# =========================
# TABELA: Categoria
# =========================
class Categoria(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


# =========================
# TABELA: Produto
# =========================
class Produto(models.Model):
    nome = models.CharField(max_length=255)
    cor = models.CharField(max_length=255, null=True, blank=True)
    peso = models.DecimalField(max_digits=10, decimal_places=2)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tamanho = models.CharField(max_length=50, null=True, blank=True)
    avaliacao_media = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    q_estoque = models.IntegerField()
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


# =========================
# TABELA: Pedido
# =========================
class Pedido(models.Model):
    data_efetuado = models.DateField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return f"Pedido #{self.id} - {self.status}"


# =========================
# TABELA: PedidoProduto
# =========================
class PedidoProduto(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    desconto_aplicado = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ('pedido', 'produto')

    def __str__(self):
        return f"{self.produto.nome} (x{self.quantidade})"


# =========================
# TABELA: Pagamento
# =========================
class Pagamento(models.Model):
    metodo = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2)
    parcela = models.IntegerField(default=1)
    data_pagamento = models.DateField()
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)

    def __str__(self):
        return f"Pagamento #{self.id} - {self.metodo}"


# =========================
# TABELA: Avaliacao
# =========================
class Avaliacao(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    nota = models.IntegerField()
    comentario = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.usuario.nome} avaliou {self.produto.nome} ({self.nota}/5)"


# =========================
# TABELA: CarrinhoProduto
# =========================
class CarrinhoProduto(models.Model):
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)

    class Meta:
        unique_together = ('carrinho', 'produto')

    def __str__(self):
        return f"{self.produto.nome} (x{self.quantidade})"


# =========================
# TABELA: LojaProduto
# =========================
class LojaProduto(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('loja', 'produto')

    def __str__(self):
        return f"{self.loja.nome} - {self.produto.nome}"
