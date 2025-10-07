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

