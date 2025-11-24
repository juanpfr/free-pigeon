# 🦅 Free Pigeon – Marketplace Digital Integrado

Plataforma completa de e-commerce multi-vendedor desenvolvida com **Django + PostgreSQL + Vue.js**.

## 📘 Documentação
Toda a documentação técnica e funcional está na pasta [`docs/`](./docs).

Acesse:
- [Introdução](./docs/01%20-%20Introducao)
- [Documentação Técnica (DER, Casos de Uso, Instalação)](./docs/02%20-%20Documentacao_Tecnica)
- [Database](./docs/03%20-%20Database)
- [API & Funcionalidades](./docs/04%20-%20API%20&%20Funcionalidades)
- [Apresentação Final](./docs/05%20-%20Apresentacao)

---

## 🚀 Tecnologias
- **Backend:** Django
- **Frontend:** HTML5, CSS3, JavaScript
- **Banco de Dados:** PostgreSQL
- **Integrações:** CorreiosAPI, GoogleAuth, Stripe

---

## ⚙️ Instalação Rápida
```bash
# Clone o repositório
git clone https://github.com/juanpfr/free-pigeon/

# Acesse a pasta do projeto
cd free-pigeon

# Crie o ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # (Windows)
source venv/bin/activate # (Linux/Mac)

# Caso ocorra algum erro no comando acima, tente este comando para permitir ambientes virtuais:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Instale as dependências
pip install -r requirements.txt

# Atualizar/Criar .env na raiz do projeto(free-pigeon), com base nas informações e no mesmo local do arquivo: .env.example

# Criar o Banco de dados no PostgreSQL (Se não tiver sido criado)
        # Dentro do pgAdmin4
        CREATE DATABASE freepigeon_db;

# Criar migrações no PostgreSQL
python manage.py makemigrations

# Executar migrações no PostgreSQL
python manage.py migrate

# Execute o projeto
python manage.py runserver
```

---


## 📄 Desenvolvido por: Equipe Free Pigeon

- **Kleber** → [Kleberapenas](https://github.com/Kleberapenas)  
- **Alisson** → [AlissonGaldino22](https://github.com/AlissonGaldino22)  
- **Caique** → [kiqrr](https://github.com/kiqrr)  
- **Bruno** → [br7trindade](https://github.com/br7trindade)  
- **Juan** → [juanpfr](https://github.com/juanpfr)  

---
