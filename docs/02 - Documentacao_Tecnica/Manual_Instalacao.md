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

