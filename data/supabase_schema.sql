-- Schema PostgreSQL completo para o Supabase
-- Executar no SQL Editor do Supabase Dashboard (uma única vez)

CREATE TABLE IF NOT EXISTS categorias (
    id        SERIAL PRIMARY KEY,
    nome      TEXT NOT NULL UNIQUE,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS insumos (
    id               SERIAL PRIMARY KEY,
    nome             TEXT NOT NULL,
    categoria_id     INTEGER REFERENCES categorias(id),
    unidade          TEXT DEFAULT 'kg',
    custo_compra     NUMERIC(12,4) DEFAULT 0,
    fator_rendimento NUMERIC(5,4)  DEFAULT 1.0,
    estoque_atual    NUMERIC(12,4) DEFAULT 0,
    estoque_minimo   NUMERIC(12,4) DEFAULT 0,
    estoque_critico  NUMERIC(12,4) DEFAULT 0,
    estoque_alerta   NUMERIC(12,4) DEFAULT 0,
    estoque_ideal    NUMERIC(12,4) DEFAULT 0,
    status_cadastro  TEXT DEFAULT 'PENDENTE',
    atualizado_em    TIMESTAMP DEFAULT NOW(),
    criado_em        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pratos (
    id          SERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    descricao   TEXT,
    preco_venda NUMERIC(10,2) DEFAULT 0,
    categoria   TEXT DEFAULT 'Prato Principal',
    ativo       INTEGER DEFAULT 1,
    criado_em   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fichas_tecnicas (
    id         SERIAL PRIMARY KEY,
    prato_id   INTEGER NOT NULL REFERENCES pratos(id) ON DELETE CASCADE,
    insumo_id  INTEGER NOT NULL REFERENCES insumos(id),
    quantidade NUMERIC(12,4) NOT NULL,
    observacao TEXT,
    criado_em  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fornecedores (
    id        SERIAL PRIMARY KEY,
    nome      TEXT NOT NULL UNIQUE,
    cnpj      TEXT,
    tipo      TEXT DEFAULT 'supermercado',
    ativo     INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compras (
    id          SERIAL PRIMARY KEY,
    fornecedor  TEXT,
    numero_nf   TEXT,
    data_compra TEXT,
    valor_total NUMERIC(12,2) DEFAULT 0,
    tipo_nota   TEXT DEFAULT 'XML',
    criado_em   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS itens_compra (
    id           SERIAL PRIMARY KEY,
    compra_id    INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
    insumo_id    INTEGER REFERENCES insumos(id),
    descricao_nf TEXT,
    quantidade   NUMERIC(12,4),
    valor_unit   NUMERIC(12,4),
    valor_total  NUMERIC(12,2),
    criado_em    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mapa_insumos (
    descricao_nf TEXT PRIMARY KEY,
    insumo_id    INTEGER NOT NULL REFERENCES insumos(id),
    criado_em    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendas (
    id                   SERIAL PRIMARY KEY,
    data                 TEXT NOT NULL,
    dia_semana           TEXT,
    plataforma           TEXT DEFAULT '99Food',
    pedidos              INTEGER DEFAULT 0,
    faturamento_bruto    NUMERIC(12,2) DEFAULT 0,
    ticket_medio         NUMERIC(10,2) DEFAULT 0,
    comissao_plataforma  NUMERIC(10,2) DEFAULT 0,
    taxa_pagamento       NUMERIC(10,2) DEFAULT 0,
    receita_total_plat   NUMERIC(12,2) DEFAULT 0,
    pedidos_atrasados    INTEGER DEFAULT 0,
    tempo_medio_preparo  NUMERIC(6,2) DEFAULT 0,
    novos_clientes       INTEGER DEFAULT 0,
    clientes_recorrentes INTEGER DEFAULT 0,
    criado_em            TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS itens_venda (
    id             SERIAL PRIMARY KEY,
    venda_id       INTEGER NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
    prato_id       INTEGER NOT NULL REFERENCES pratos(id),
    quantidade     INTEGER NOT NULL DEFAULT 1,
    valor_unitario NUMERIC(10,2) DEFAULT 0,
    criado_em      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventario (
    id              SERIAL PRIMARY KEY,
    insumo_id       INTEGER NOT NULL REFERENCES insumos(id),
    quantidade_real NUMERIC(12,4) NOT NULL,
    data_contagem   TEXT NOT NULL,
    observacao      TEXT,
    criado_em       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS movimentacoes (
    id              SERIAL PRIMARY KEY,
    insumo_id       INTEGER NOT NULL REFERENCES insumos(id),
    tipo            TEXT NOT NULL,
    quantidade      NUMERIC(12,4) NOT NULL,
    custo_unitario  NUMERIC(12,4) DEFAULT 0,
    custo_total     NUMERIC(12,4) DEFAULT 0,
    referencia_id   INTEGER,
    referencia_tipo TEXT,
    observacao      TEXT,
    criado_em       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS perdas (
    id             SERIAL PRIMARY KEY,
    data_perda     TEXT NOT NULL,
    insumo_id      INTEGER REFERENCES insumos(id),
    prato_id       INTEGER REFERENCES pratos(id),
    quantidade     NUMERIC(12,4) NOT NULL,
    motivo         TEXT NOT NULL DEFAULT 'sobra_producao',
    custo_estimado NUMERIC(12,4) DEFAULT 0,
    observacao     TEXT,
    registrado_por TEXT,
    criado_em      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS metas_desperdicio (
    id         SERIAL PRIMARY KEY,
    insumo_id  INTEGER REFERENCES insumos(id),
    pct_maximo NUMERIC(5,2) DEFAULT 15.0,
    ativo      INTEGER DEFAULT 1,
    criado_em  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS precos_fornecedores (
    id              SERIAL PRIMARY KEY,
    insumo_id       INTEGER NOT NULL REFERENCES insumos(id),
    fornecedor_id   INTEGER NOT NULL REFERENCES fornecedores(id),
    preco_unitario  NUMERIC(12,4) NOT NULL,
    quantidade_nota NUMERIC(12,4),
    data_compra     TEXT NOT NULL,
    compra_id       INTEGER REFERENCES compras(id),
    criado_em       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lista_compras (
    id                     SERIAL PRIMARY KEY,
    data_lista             TEXT NOT NULL,
    insumo_id              INTEGER NOT NULL REFERENCES insumos(id),
    quantidade_sugerida    NUMERIC(12,4) NOT NULL,
    unidade                TEXT,
    dias_restantes         NUMERIC(6,2),
    fornecedor_sugerido_id INTEGER REFERENCES fornecedores(id),
    preco_estimado         NUMERIC(12,2) DEFAULT 0,
    motivo                 TEXT,
    status                 TEXT DEFAULT 'pendente',
    criado_em              TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS configuracoes (
    chave         TEXT PRIMARY KEY,
    valor         TEXT NOT NULL,
    descricao     TEXT,
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Seeds obrigatórios
INSERT INTO configuracoes VALUES
  ('dias_estoque_minimo','2','Alertar quando faltar menos de X dias',NOW()),
  ('dias_media_consumo','7','Consumo médio dos últimos X dias',NOW()),
  ('dias_alvo_compra','3','Dias de estoque que a lista visa atingir',NOW()),
  ('taxa_99food','10.5','Comissão 99Food em %',NOW()),
  ('taxa_ifood','16.0','Comissão iFood em %',NOW()),
  ('ocr_provider','tesseract','tesseract ou google_vision',NOW()),
  ('google_vision_key','','Chave API Google Vision',NOW())
ON CONFLICT (chave) DO NOTHING;

INSERT INTO fornecedores (nome, tipo) VALUES
  ('Atacadão','supermercado'),
  ('Assaí','supermercado'),
  ('Tático','supermercado'),
  ('Fornecedor Genérico','outro')
ON CONFLICT (nome) DO NOTHING;
