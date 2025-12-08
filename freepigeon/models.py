from django.db import models
from decimal import Decimal
from django.contrib.auth.hashers import make_password, check_password
from django.db.models.signals import post_migrate
from django.dispatch import receiver


# =========================
# TABELA: Loja
# =========================
class Loja(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome

# =========================
# TABELA: Plano
# =========================
class Plano(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)  # algo tipo 'start', 'pro', 'turbo'
    descricao = models.CharField(max_length=255, blank=True, null=True)
    preco_mensal = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    limite_anuncios = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número máximo de anúncios ativos. Deixe vazio para ilimitado."
    )
    ativo = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False,
        help_text="Plano padrão para novos usuários / login Google."
    )

    def __str__(self):
        return self.nome


# =========================
# TABELA: Usuario
# =========================
class Usuario(models.Model):
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    senha = models.CharField(max_length=255)
    loja = models.ForeignKey('Loja', on_delete=models.SET_NULL, null=True, blank=True)
    plano = models.ForeignKey('Plano', on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


# =========================
# TABELA: Endereco
# =========================
class Endereco(models.Model):
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        related_name='enderecos',
        null=True,
        blank=True
    )
    apelido = models.CharField(
        max_length=30, blank=True, null=True
    )  # Casa, Trabalho, etc.
    complemento = models.CharField(max_length=255, blank=True, null=True)
    rua = models.CharField(max_length=255)
    numero = models.IntegerField()
    bairro = models.CharField(max_length=255)
    cidade = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    cep = models.CharField(max_length=10)
    principal = models.BooleanField(default=False)

    def __str__(self):
        base = f"{self.rua}, {self.numero} - {self.cidade}"
        if self.apelido:
            return f"{self.apelido} ({base})"
        return base


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

    loja = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True)
    vendedor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='produtos',
        null=True,
        blank=True
    )

    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)

    ativo = models.BooleanField(default=True)

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


# =========================
# TABELA: AdminUser (Admin do painel)
# =========================
class AdminUser(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    def verify_password(self, raw_password):
        return check_password(raw_password, self.password)


# =========================
# SIGNALS: criar admin padrão + plano padrão
# =========================

@receiver(post_migrate)
def criar_admin_padrao(sender, **kwargs):
    """
    Cria automaticamente um administrador padrão:
    usuário: admin
    senha: admin
    """
    # Troque 'freepigeon' pelo nome do SEU app, se for outro
    if sender.name != "freepigeon":
        return

    if not AdminUser.objects.filter(username='admin').exists():
        AdminUser.objects.create(
            username='admin',
            password=make_password('admin')
        )
        print("✔ Admin padrão criado: admin / admin")


@receiver(post_migrate)
def garantir_plano_basico(sender, **kwargs):
    """
    Garante que sempre exista um plano básico gratuito padrão:
    - nome: Free Pigeon Basic
    - slug: free-basic
    - preco_mensal: 0
    - limite_anuncios: 5
    - is_default: True
    """
    if sender.name != "freepigeon":
        return

    # Aqui usamos diretamente a classe Plano, que já está definida acima neste arquivo
    plano_default = Plano.objects.filter(is_default=True).first()

    if not plano_default:
        Plano.objects.create(
            nome="Free Pigeon Basic",
            slug="free-basic",
            descricao="Plano gratuito padrão. Até 5 anúncios e sem loja.",
            preco_mensal=0,
            limite_anuncios=5,
            ativo=True,
            is_default=True,
        )
        print("✔ Plano padrão criado: Free Pigeon Basic (gratuito, 5 anúncios)")
    else:
        # Garante regras do plano default
        changed = False
        if plano_default.preco_mensal != 0:
            plano_default.preco_mensal = 0
            changed = True
        if plano_default.limite_anuncios != 5:
            plano_default.limite_anuncios = 5
            changed = True
        if not plano_default.is_default:
            plano_default.is_default = True
            changed = True

        if changed:
            plano_default.save()
            print("✔ Plano padrão ajustado para grátis com limite de 5 anúncios.")