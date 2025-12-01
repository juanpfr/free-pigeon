# ⚙️ Manual de Instalação – Free Pigeon

## Pré-requisitos
- Python 3.10 até 3.12
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

