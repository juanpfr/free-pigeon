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

# 🗂️ Estrutura do Projeto

```
ffree-pigeon/
│
├── docs/                                       # Documentação do Projeto
├── freepigeon/                                 # Diretório do app do projeto
├── media/                                      # Diretórios com arquivos de mídia cadastrados no banco de dados
├── produtos/                                   # Produtos cadastrados no banco de dados
├── projeto/                                    # Diretório do projeto Django padrão sem adição de arquivos
├── venv/                                       # Diretório do ambiente virtual (pode ter outro nome) sem adição/modificação de arquivos
├── .env                                        # Arquivo de variáveis de ambiente para conexão com o banco de dados
├── .env.exemple
├── .gitignore
├── manage.py
├── README.md
├── requirements.txt

```

---

### 🧰 Tecnologias Utilizadas
- **Backend:** Django
- **Frontend:** HTML5, CSS3
- **Banco de Dados:** PostgreSQL
- **Integrações:** CorreiosAPI, GoogleAuth

# ⚙️ Manual de Instalação – Free Pigeon

## Pré-requisitos
- Python 3.10+
- PostgreSQL

## 1️⃣ Clonar o repositório
```bash
# Clone o repositório
git clone https://github.com/juanpfr/free-pigeon/

# Acesse a pasta do projeto
cd free-pigeon

# Crie o ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # (Windows)
source venv/bin/activate # (Linux/Mac)

# Caso ocorra algum erro no comando acima, tente este comando para liberar ambientes virtuais:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 2️⃣ Criar e ativar o ambiente virtual
```bash
# Crie o ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # (Windows)
source venv/bin/activate # (Linux/Mac)

# Caso ocorra algum erro no comando acima, tente este comando para liberar ambientes virtuais:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3️⃣ Instalar dependências
```bash
python -m pip install -r requirements.txt
```

## 4️⃣ Configurar o banco de dados
Crie o banco no PostgreSQL e crie/atualize o arquivo `.env`:

```
DB_NAME=freepigeon_db
DB_USER=nome_do_seu_usuario_aqui
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

