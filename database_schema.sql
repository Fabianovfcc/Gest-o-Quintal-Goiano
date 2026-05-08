-- Esquema inicial de Banco de Dados para o Sistema de CMV
-- Foco: Quintal Goiano

CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT, -- Proteínas, Carboidratos, Laticínios, Vegetais, Embalagens, Bebidas
    unidade TEXT, -- kg, g, un, L, ml
    custo_compra REAL DEFAULT 0,
    fator_rendimento REAL DEFAULT 1.0, -- Rendimento pós-preparo (ex: 0.7 para 70%)
    estoque_minimo REAL DEFAULT 0,
    estoque_critico REAL DEFAULT 0,
    estoque_alerta REAL DEFAULT 0,
    estoque_ideal REAL DEFAULT 0,
    estoque_atual REAL DEFAULT 0,
    status_cadastro TEXT DEFAULT 'PENDENTE' -- PENDENTE ou COMPLETO
);

CREATE TABLE IF NOT EXISTS pratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    preco_venda REAL DEFAULT 0,
    categoria TEXT -- Marmita, Petisco, Bebida
);

CREATE TABLE IF NOT EXISTS fichas_tecnicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prato_id INTEGER,
    insumo_id INTEGER,
    quantidade REAL, -- Quantidade usada no prato (na unidade do insumo)
    FOREIGN KEY (prato_id) REFERENCES pratos(id),
    FOREIGN KEY (insumo_id) REFERENCES insumos(id)
);

CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data DATE NOT NULL,
    plataforma TEXT, -- 99Food, iFood, Local
    pedido_id TEXT,
    total_bruto REAL,
    comissao_plataforma REAL,
    taxa_pagamento REAL,
    repasse_liquido REAL,
    status_preparo TEXT, -- No prazo, Atrasado
    tempo_preparo_min INTEGER
);

CREATE TABLE IF NOT EXISTS itens_venda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER,
    prato_id INTEGER,
    quantidade INTEGER,
    valor_unitario REAL,
    FOREIGN KEY (venda_id) REFERENCES vendas(id),
    FOREIGN KEY (prato_id) REFERENCES pratos(id)
);
