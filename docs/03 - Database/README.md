# 🕊️ Free Pigeon — Banco de Dados E-Market

Este projeto define o esquema de banco de dados relacional para a aplicação **Free Pigeon**, um sistema de e-commerce (E-Market) voltado para a compra e venda de produtos em lojas virtuais.  
O banco foi projetado para garantir **organização**, **integridade referencial** e **escalabilidade** entre usuários, lojas, produtos, pedidos e avaliações.

---

## 📘 Visão Geral

O banco de dados é estruturado em torno de **usuários**, **lojas**, **produtos** e **pedidos**, com suporte a funcionalidades de **carrinho de compras**, **pagamentos**, **avaliações** e **endereços**.  
Cada tabela cumpre uma função específica, e todas estão conectadas por **chaves estrangeiras** para manter a consistência dos dados.

---

## 🧩 Diagrama Entidade-Relacionamento (ER)

Abaixo está o diagrama que representa todas as tabelas e seus relacionamentos:

<p align="center">
  <img src="./DER.png" alt="Diagrama ER do Free Pigeon" width="700">
</p>

---

## 🏗️ Estrutura do Banco de Dados

### 1. 🧍‍♂️ Tabela `usuario`
Armazena informações dos usuários (clientes e vendedores).

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_usuario` | SERIAL (PK) | Identificador único. |
| `nome` | VARCHAR(255) | Nome completo. |
| `email` | VARCHAR(255) | E-mail único. |
| `telefone` | VARCHAR(20) | Telefone de contato. |
| `cpf` | VARCHAR(14) | CPF único. |
| `senha` | VARCHAR(255) | Senha criptografada. |
| `id_loja` | INT (FK) | Loja associada (opcional). |
| `id_endereco` | INT (FK) | Endereço principal. |
| `id_carrinho` | INT (FK) | Carrinho ativo. |

---

### 2. 🏠 Tabela `endereco`
Guarda dados de localização de usuários e lojas.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_endereco` | SERIAL (PK) | Identificador. |
| `complemento` | VARCHAR(255) | Detalhes extras. |
| `rua` | VARCHAR(255) | Nome da rua. |
| `numero` | INT | Número da residência. |
| `bairro` | VARCHAR(255) | Bairro. |
| `cidade` | VARCHAR(255) | Cidade. |
| `estado` | VARCHAR(255) | Estado. |
| `cep` | VARCHAR(10) | CEP. |

---

### 3. 🏬 Tabela `loja`
Representa as lojas registradas.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_loja` | SERIAL (PK) | Identificador da loja. |
| `id_usuario` | INT (FK) | Dono da loja. |
| `nome` | VARCHAR(255) | Nome da loja. |

---

### 4. 🏷️ Tabela `categoria`
Categorias de produtos.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_categoria` | SERIAL (PK) | Identificador. |
| `nome` | VARCHAR(255) | Nome da categoria. |

---

### 5. 📦 Tabela `produto`
Informações dos produtos à venda.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_produto` | SERIAL (PK) | Identificador. |
| `nome` | VARCHAR(255) | Nome do produto. |
| `cor` | VARCHAR(255) | Cor (opcional). |
| `peso` | NUMERIC(10,2) | Peso. |
| `valor` | NUMERIC(10,2) | Preço. |
| `desconto` | NUMERIC(5,2) | Percentual de desconto. |
| `tamanho` | VARCHAR(50) | Tamanho (opcional). |
| `avaliacao_media` | NUMERIC(2,1) | Média de avaliações. |
| `q_estoque` | INT | Quantidade em estoque. |
| `id_loja` | INT (FK) | Loja vendedora. |
| `id_categoria` | INT (FK) | Categoria do produto. |

---

### 6. 🧾 Tabela `pedido`
Pedidos realizados pelos usuários.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_pedido` | SERIAL (PK) | Identificador. |
| `data_efetuado` | DATE | Data do pedido. |
| `valor_total` | NUMERIC(10,2) | Valor total. |
| `status` | VARCHAR(50) | Status (Ex: “Em andamento”). |
| `id_usuario` | INT (FK) | Usuário comprador. |

---

### 7. 🔗 Tabela `pedido_produto`
Relaciona produtos e pedidos (itens comprados).

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_pedido` | INT (FK) | Pedido. |
| `id_produto` | INT (FK) | Produto comprado. |
| `quantidade` | INT | Quantidade adquirida. |
| `preco_unitario` | NUMERIC(10,2) | Preço do item no momento da compra. |
| `desconto_aplicado` | NUMERIC(5,2) | Desconto aplicado. |

---

### 8. 💳 Tabela `pagamento`
Detalhes dos pagamentos.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_pagamento` | SERIAL (PK) | Identificador. |
| `metodo` | VARCHAR(50) | Método de pagamento. |
| `status` | VARCHAR(50) | Status do pagamento. |
| `valor_pago` | NUMERIC(10,2) | Valor pago. |
| `parcela` | INT | Número de parcelas. |
| `data_pagamento` | DATE | Data do pagamento. |
| `id_pedido` | INT (FK) | Pedido relacionado. |

---

### 9. ⭐ Tabela `avaliacao`
Avaliações feitas pelos usuários.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_avaliacao` | SERIAL (PK) | Identificador. |
| `id_produto` | INT (FK) | Produto avaliado. |
| `id_usuario` | INT (FK) | Autor da avaliação. |
| `nota` | INT | Nota (0–5). |
| `comentario` | VARCHAR(200) | Comentário. |

---

### 10. 🛒 Tabela `carrinho`
Carrinho de compras ativo.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_carrinho` | SERIAL (PK) | Identificador. |
| `id_usuario` | INT (FK) | Usuário dono do carrinho. |
| `data_adicao` | DATE | Data de criação. |

---

### 11. 🧩 Tabela `carrinho_produto`
Produtos adicionados ao carrinho.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_carrinho` | INT (FK, PK) | Carrinho. |
| `id_produto` | INT (FK, PK) | Produto. |
| `quantidade` | INT | Quantidade. |

---

### 12. 🏪 Tabela `loja_produto`
Relaciona lojas e produtos.

| Campo | Tipo | Descrição |
|-------|------|------------|
| `id_loja` | INT (FK, PK) | Loja. |
| `id_produto` | INT (FK, PK) | Produto. |

---

## 🔗 Relacionamentos Principais

- **Usuário ↔ Loja:** 1:N  
- **Usuário ↔ Pedido:** 1:N  
- **Pedido ↔ Pedido_Produto ↔ Produto:** N:M  
- **Carrinho ↔ Produto:** N:M  
- **Loja ↔ Produto:** N:M  
- **Produto ↔ Avaliação:** 1:N  

---

## ⚙️ Tecnologias Recomendadas

- **Banco de dados:** PostgreSQL  
- **Ferramentas:** DBeaver, PgAdmin  
- **ORMs sugeridos:** Prisma, Sequelize, TypeORM  

---
