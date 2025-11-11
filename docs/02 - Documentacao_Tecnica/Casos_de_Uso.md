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
1. O cliente navega no catálogo, se cadastra ou faz autenticação e adiciona itens ao carrinho.
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

