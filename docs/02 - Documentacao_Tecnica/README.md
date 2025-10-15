# 📑 Casos de Uso Detalhados

## Caso de Uso 1 – Cadastro de Produto
**Ator:** Vendedor  
**Pré-condição:** O usuário deve estar autenticado como vendedor.  
**Fluxo principal:**
1. O vendedor acessa o painel de controle.
2. Seleciona “Cadastrar Produto”.
3. Informa os dados (nome, categoria, valor, estoque, etc.).
4. O sistema valida as informações e salva o produto.
**Pós-condição:** O produto aparece na listagem pública e no catálogo da loja.

## Caso de Uso 2 – Compra de Produto
**Ator:** Cliente  
**Fluxo principal:**
1. O cliente navega no catálogo e adiciona itens ao carrinho.
2. Realiza o checkout e escolhe o método de pagamento.
3. O sistema confirma o pagamento e gera o pedido.
**Pós-condição:** O pedido é registrado e o estoque atualizado.

## Caso de Uso 3 – Avaliar Produto
**Ator:** Cliente autenticado  
**Fluxo principal:**
1. O cliente acessa o histórico de pedidos.
2. Seleciona um produto comprado.
3. Dá uma nota de 0 a 5 e, opcionalmente, um comentário.
**Pós-condição:** O produto tem sua média de avaliação atualizada.

# 🗂️ Estrutura Inicial do Projeto Django

```
free-pigeon/
│
├── manage.py
├── .env.example
├── requirements.txt
├── docs/
│
├── freepigeon/                # Configurações principais do Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── users/                 # Gerenciamento de usuários e perfis
│   ├── stores/                # Lojas e vendedores
│   ├── products/              # Produtos e categorias
│   ├── orders/                # Pedidos e carrinhos
│   ├── payments/              # Pagamentos e integrações
│   └── reviews/               # Avaliações e feedbacks
└── static/
```

---

### 🧰 Tecnologias Utilizadas
- **Backend:** Django, Django REST Framework, Celery, Redis  
- **Banco de Dados:** PostgreSQL  
- **Frontend:** Vue.js, Tailwind CSS  
- **Integrações:** Stripe, AWS S3 (django-storages, boto3)

# ⚙️ Manual de Instalação – Free Pigeon

## Pré-requisitos
- Python 3.10+
- PostgreSQL
- Redis
- Virtualenv

## 1️⃣ Clonar o repositório
```bash
git clone https://github.com/juanpfr/free-pigeon.git
cd free-pigeon
```

## 2️⃣ Criar e ativar o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

## 3️⃣ Instalar dependências
```bash
pip install -r requirements.txt
```

## 4️⃣ Configurar o banco de dados
Crie o banco no PostgreSQL e atualize o arquivo `.env`:

```
DB_NAME=freepigeon
DB_USER=freepigeon_admin
DB_PASSWORD=coloque_sua_senha_aqui
DB_HOST=localhost
DB_PORT=5432
```

## 5️⃣ Rodar as migrações e iniciar o servidor
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Acesse o projeto em: [http://localhost:8000](http://localhost:8000)

