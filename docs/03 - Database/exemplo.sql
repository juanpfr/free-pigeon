-- =========================
-- TABELA: Endereco
-- =========================
CREATE TABLE endereco (
    id SERIAL PRIMARY KEY,
    complemento VARCHAR(255),
    rua VARCHAR(255) NOT NULL,
    numero INTEGER NOT NULL,
    bairro VARCHAR(255) NOT NULL,
    cidade VARCHAR(255) NOT NULL,
    estado VARCHAR(255) NOT NULL,
    cep VARCHAR(10) NOT NULL
);

-- =========================
-- TABELA: Loja
-- =========================
CREATE TABLE loja (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL
);

-- =========================
-- TABELA: Usuario
-- =========================
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    loja_id INTEGER REFERENCES loja(id) ON DELETE SET NULL,
    endereco_id INTEGER REFERENCES endereco(id) ON DELETE SET NULL
);

-- =========================
-- TABELA: Categoria
-- =========================
CREATE TABLE categoria (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    imagem VARCHAR(100)
);

-- =========================
-- TABELA: Produto
-- =========================
CREATE TABLE produto (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    valor DECIMAL(10,2) NOT NULL,
    desconto DECIMAL(5,2),
    q_estoque INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categoria(id) ON DELETE CASCADE,
    loja_id INTEGER NOT NULL REFERENCES loja(id) ON DELETE CASCADE,
    imagem VARCHAR(100)
);

-- =========================
-- TABELAS DE ATRIBUTOS DINÂMICOS
-- =========================
CREATE TABLE atributo (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL
);

CREATE TABLE produto_atributo (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER NOT NULL REFERENCES produto(id) ON DELETE CASCADE,
    atributo_id INTEGER NOT NULL REFERENCES atributo(id) ON DELETE CASCADE,
    valor VARCHAR(255) NOT NULL,
    UNIQUE (produto_id, atributo_id)
);

-- =========================
-- TABELA: Carrinho
-- =========================
CREATE TABLE carrinho (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE REFERENCES usuario(id) ON DELETE CASCADE,
    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE carrinho_produto (
    id SERIAL PRIMARY KEY,
    carrinho_id INTEGER NOT NULL REFERENCES carrinho(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produto(id) ON DELETE CASCADE,
    quantidade INTEGER NOT NULL DEFAULT 1,
    UNIQUE (carrinho_id, produto_id)
);

-- =========================
-- TABELA: Pedido
-- =========================
CREATE TABLE pedido (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    endereco_id INTEGER REFERENCES endereco(id) ON DELETE SET NULL,
    data_efetuado TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'Pendente'
);

CREATE TABLE pedido_produto (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produto(id) ON DELETE CASCADE,
    quantidade INTEGER NOT NULL DEFAULT 1,
    preco_unitario DECIMAL(10,2) NOT NULL
);
