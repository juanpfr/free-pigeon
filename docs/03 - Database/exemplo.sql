-- =========================================
-- BANCO DE DADOS: Free Pigeon (E-Market)
-- =========================================

-- =========================
-- TABELA: endereco
-- =========================
CREATE TABLE endereco (
    id_endereco SERIAL PRIMARY KEY,
    complemento VARCHAR(255),
    rua VARCHAR(255) NOT NULL,
    numero INT NOT NULL,
    bairro VARCHAR(255) NOT NULL,
    cidade VARCHAR(255) NOT NULL,
    estado VARCHAR(255) NOT NULL,
    cep VARCHAR(10) NOT NULL
);

-- =========================
-- TABELA: carrinho
-- =========================
CREATE TABLE carrinho (
    id_carrinho SERIAL PRIMARY KEY,
    id_usuario INT,
    data_adicao DATE NOT NULL DEFAULT CURRENT_DATE
);

-- =========================
-- TABELA: usuario
-- =========================
CREATE TABLE usuario (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    id_loja INT,
    id_endereco INT,
    id_carrinho INT,
    FOREIGN KEY (id_loja) REFERENCES loja(id_loja),
    FOREIGN KEY (id_endereco) REFERENCES endereco(id_endereco),
    FOREIGN KEY (id_carrinho) REFERENCES carrinho(id_carrinho)
);

-- =========================
-- TABELA: loja
-- =========================
CREATE TABLE loja (
    id_loja SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

-- =========================
-- TABELA: categoria
-- =========================
CREATE TABLE categoria (
    id_categoria SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL
);

-- =========================
-- TABELA: produto
-- =========================
CREATE TABLE produto (
    id_produto SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cor VARCHAR(255),
    peso NUMERIC(10,2) NOT NULL,
    valor NUMERIC(10,2) NOT NULL,
    desconto NUMERIC(5,2),
    tamanho VARCHAR(50),
    avaliacao_media NUMERIC(2,1) DEFAULT 0,
    q_estoque INT NOT NULL,
    id_loja INT NOT NULL,
    id_categoria INT NOT NULL,
    FOREIGN KEY (id_loja) REFERENCES loja(id_loja),
    FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)
);

-- =========================
-- TABELA: pedido
-- =========================
CREATE TABLE pedido (
    id_pedido SERIAL PRIMARY KEY,
    data_efetuado DATE NOT NULL DEFAULT CURRENT_DATE,
    valor_total NUMERIC(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    id_usuario INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

-- =========================
-- TABELA: pedido_produto
-- (liga pedidos e produtos)
-- =========================
CREATE TABLE pedido_produto (
    id_pedido INT NOT NULL,
    id_produto INT NOT NULL,
    quantidade INT NOT NULL DEFAULT 1,
    preco_unitario NUMERIC(10,2) NOT NULL,
    desconto_aplicado NUMERIC(5,2) DEFAULT 0,
    PRIMARY KEY (id_pedido, id_produto),
    FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido),
    FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
);

-- =========================
-- TABELA: pagamento
-- =========================
CREATE TABLE pagamento (
    id_pagamento SERIAL PRIMARY KEY,
    metodo VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    valor_pago NUMERIC(10,2) NOT NULL,
    parcela INT DEFAULT 1,
    data_pagamento DATE NOT NULL,
    id_pedido INT NOT NULL,
    FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido)
);

-- =========================
-- TABELA: avaliacao
-- =========================
CREATE TABLE avaliacao (
    id_avaliacao SERIAL PRIMARY KEY,
    id_produto INT NOT NULL,
    id_usuario INT NOT NULL,
    nota INT CHECK (nota BETWEEN 0 AND 5),
    comentario VARCHAR(200),
    FOREIGN KEY (id_produto) REFERENCES produto(id_produto),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

-- =========================
-- TABELA: carrinho_produto
-- =========================
CREATE TABLE carrinho_produto (
    id_carrinho INT NOT NULL,
    id_produto INT NOT NULL,
    quantidade INT DEFAULT 1,
    PRIMARY KEY (id_carrinho, id_produto),
    FOREIGN KEY (id_carrinho) REFERENCES carrinho(id_carrinho),
    FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
);

-- =========================
-- TABELA: loja_produto
-- =========================
CREATE TABLE loja_produto (
    id_loja INT NOT NULL,
    id_produto INT NOT NULL,
    PRIMARY KEY (id_loja, id_produto),
    FOREIGN KEY (id_loja) REFERENCES loja(id_loja),
    FOREIGN KEY (id_produto) REFERENCES produto(id_produto)
);
