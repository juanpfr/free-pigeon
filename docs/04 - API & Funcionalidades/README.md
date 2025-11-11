
# 🕊️ Free Pigeon - Plataforma Django

Protótipo funcional de e-commerce desenvolvido com **Django + PostgreSQL**, incluindo cadastro, login, carrinho, pedidos e integração de frete com os **Correios**.

---

## 🔗 Rotas e Funcionalidades do Sistema

| Método | Rota | Descrição |
|--------|-------|------------|
| `GET` | `/` | Página inicial (home) com listagem de produtos e categorias |
| `GET` | `/login/` | Página de login do usuário |
| `POST` | `/login/` | Autenticação de usuário (e-mail ou CPF) |
| `GET` | `/cadastro/` | Página de cadastro de novo usuário |
| `POST` | `/cadastro/` | Criação de novo usuário no sistema |
| `GET` | `/categoria/<id>/` | Exibe produtos filtrados por categoria |
| `GET` | `/produto/<id>/` | Página de detalhes de um produto |
| `POST` | `/carrinho/adicionar/<id>/` | Adiciona um produto ao carrinho |
| `GET` | `/carrinho/` | Exibe o carrinho de compras do usuário |
| `POST` | `/checkout/` | Finaliza o pedido |
| `GET` | `/meus-pedidos/` | Lista os pedidos do usuário autenticado |

---

## 🔐 Autenticação e Sessão

O sistema utiliza **sessões do Django (`request.session`)** para autenticação e controle de login.  
Também permite integração com **login via Google OAuth**, para autenticação simplificada.

---

## 🚚 Integração com Correios (API Externa)

Integração planejada com a **API dos Correios** para:
- cálculo automático do frete,
- previsão de entrega,
- rastreamento básico de pedidos.

Essas funcionalidades são implementadas via requisições REST externas, utilizando bibliotecas Python (ex: `requests`).

---

## 🛒 Fluxo de Usuário

1. O cliente acessa `/` e visualiza produtos e categorias.  
2. Adiciona produtos ao carrinho.  
3. Realiza login ou cadastro.  
4. Informa o endereço de entrega.  
5. O sistema consulta o frete nos Correios.  
6. O pedido é registrado e pode ser acompanhado em `/meus-pedidos/`.

---

## 🧩 Extensões Futuras

- Criação de **API REST** com Django REST Framework.  
- Implementação de **JWT** ou **TokenAuth** para consumo por apps externos.  
- Dashboard administrativo completo para vendedores.  

---

## ⚙️ Tecnologias Principais

- **Backend:** Django 5.x  
- **Banco de Dados:** PostgreSQL  
- **Frontend:** HTML + CSS + JavaScript + Templates Django  
- **Integrações:** Google OAuth, Correios API  

---

## 👨‍💻 Autor

Desenvolvido como protótipo funcional para demonstração de e-commerce com Django.  
