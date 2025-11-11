# 🗂️ Estrutura completa do Projeto

```
free-pigeon/
│
├── docs/                                       # Documentação do Projeto
├──── 01 - Introducao/
├──────── README.md
├──── 02 - Documentacao_Tecnica/
├──────── Casos_de_Uso.md
├──────── Estrutura_Projeto.md
├──────── Manual_Instalacao.md
├──────── README.md
├──── 03 - Database/
├──────── DER.png
├──────── Dicionario de Dados.pdf
├──────── exemplo.sql
├──────── README.md
├──── 04 - API & Funcionalidades/
├──────── README.md
├──── 05 - Cronograma/
├──────── README.md
├──── README.md
├── freepigeon/                                 # Diretório do app do projeto
├──── __pycache__/                              # Arquivos Python
├──── migrations/                               # Arquivos Python
├──── static/                                   # Arquivos estáticos
├──────── css/
├──────────────── auth.css
├──────────────── cadastro.css
├──────────────── cart.css
├──────────────── checkout.css
├──────────────── login.css
├──────────────── product.css
├──────────────── style.css
├──────── img/
├──────────────── cart.png
├──────────────── freepigeon.png
├──────────────── menu.png
├──────────────── search.png
├──────── js/
├──────────────── main.js
├──── templates/
├──────────────── partials/
├──────────────── auth.html
├──────────────── base.html
├──────────────── buscar.html
├──────────────── cadastro.html
├──────────────── cart.html
├──────────────── categoria.html
├──────────────── checkout.html
├──────────────── home.html
├──────────────── login.html
├──────────────── meus_pedidos.html
├──────────────── product.html
├──── __init__.py
├──── admin.py
├──── apps.py
├──── auth_backend.py
├──── models.py
├──── tests.py
├──── urls.py
├──── views.py
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

