"""
database.py - Criação e gerenciamento do banco de dados SQLite
Sistema de CMV - Quintal Goiano
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cmv.db')


def get_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Retorna linhas como dicionários
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


_pg_checked = False
def criar_tabelas():
    """Cria todas as tabelas do sistema caso não existam (apenas SQLite)."""
    global _pg_checked
    from db import is_postgres
    if is_postgres():
        if not _pg_checked:
            print("[OK] Usando Postgres (Supabase) — tabelas gerenciadas pelo Supabase.")
            _pg_checked = True
        return
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        -- Categorias de insumos
        CREATE TABLE IF NOT EXISTS categorias (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT    NOT NULL UNIQUE
        );

        -- Insumos / Ingredientes
        CREATE TABLE IF NOT EXISTS insumos (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            nome              TEXT    NOT NULL,
            categoria_id      INTEGER REFERENCES categorias(id),
            unidade           TEXT    NOT NULL DEFAULT 'kg',
            custo_compra      REAL    DEFAULT 0,
            fator_rendimento  REAL    DEFAULT 1.0,
            estoque_atual     REAL    DEFAULT 0,
            estoque_minimo    REAL    DEFAULT 0, -- Mantido por compatibilidade (= estoque_critico)
            estoque_critico   REAL    DEFAULT 0,
            estoque_alerta    REAL    DEFAULT 0,
            estoque_ideal     REAL    DEFAULT 0,
            status_cadastro   TEXT    DEFAULT 'PENDENTE',
            criado_em         TEXT    DEFAULT (datetime('now','localtime')),
            atualizado_em     TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- Pratos do cardápio
        CREATE TABLE IF NOT EXISTS pratos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nome         TEXT    NOT NULL,
            descricao    TEXT,
            preco_venda  REAL    DEFAULT 0,
            categoria    TEXT,
            ativo        INTEGER DEFAULT 1,
            criado_em    TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- Ficha técnica: relação entre prato e insumos
        CREATE TABLE IF NOT EXISTS fichas_tecnicas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            prato_id    INTEGER NOT NULL REFERENCES pratos(id) ON DELETE CASCADE,
            insumo_id   INTEGER NOT NULL REFERENCES insumos(id),
            quantidade  REAL    NOT NULL,
            observacao  TEXT
        );

        -- Vendas (pedidos por dia / plataforma)
        CREATE TABLE IF NOT EXISTS vendas (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            data                  TEXT    NOT NULL,
            dia_semana            TEXT,
            plataforma            TEXT    NOT NULL DEFAULT '99Food',
            pedidos               INTEGER DEFAULT 0,
            faturamento_bruto     REAL    DEFAULT 0,
            ticket_medio          REAL    DEFAULT 0,
            comissao_plataforma   REAL    DEFAULT 0,
            taxa_pagamento        REAL    DEFAULT 0,
            receita_total_plat    REAL    DEFAULT 0,
            pedidos_atrasados     INTEGER DEFAULT 0,
            tempo_medio_preparo   REAL    DEFAULT 0,
            novos_clientes        INTEGER DEFAULT 0,
            clientes_recorrentes  INTEGER DEFAULT 0,
            importado_em          TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- Compras (notas fiscais)
        CREATE TABLE IF NOT EXISTS compras (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor     TEXT,
            numero_nf      TEXT,
            data_compra    TEXT,
            valor_total    REAL    DEFAULT 0,
            tipo_nota      TEXT    DEFAULT 'XML',  -- XML, PDF, Manual
            arquivo_path   TEXT,
            importado_em   TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- Itens de cada compra (vínculo insumo ← nota fiscal)
        CREATE TABLE IF NOT EXISTS itens_compra (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id    INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
            insumo_id    INTEGER REFERENCES insumos(id),
            descricao_nf TEXT    NOT NULL,
            quantidade   REAL    NOT NULL,
            valor_unit   REAL    NOT NULL,
            valor_total  REAL    NOT NULL
        );

        -- Mapeamento: descrição da nota → insumo (para re-uso)
        CREATE TABLE IF NOT EXISTS mapa_insumos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao_nf  TEXT    NOT NULL UNIQUE,
            insumo_id     INTEGER REFERENCES insumos(id)
        );

        -- Inventário físico (contagem real periódica)
        CREATE TABLE IF NOT EXISTS inventario (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            insumo_id        INTEGER NOT NULL REFERENCES insumos(id),
            data_contagem    TEXT    NOT NULL,
            quantidade_real  REAL    NOT NULL,
            responsavel      TEXT,
            observacao       TEXT,
            criado_em        TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- Vendas (pedidos individuais - NOVO Sprint 3)
        CREATE TABLE IF NOT EXISTS vendas_pedidos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            data_venda   TEXT NOT NULL,
            origem       TEXT DEFAULT '99FOOD', -- 99FOOD, IFOOD, MANUAL
            valor_total  REAL DEFAULT 0,
            status       TEXT DEFAULT 'CONCLUIDO',
            importado_em TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Itens de cada venda (vinculo pedido <-> prato)
        CREATE TABLE IF NOT EXISTS itens_venda (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id       INTEGER NOT NULL REFERENCES vendas_pedidos(id) ON DELETE CASCADE,
            prato_id       INTEGER NOT NULL REFERENCES pratos(id),
            quantidade     INTEGER NOT NULL DEFAULT 1,
            valor_unitario REAL    NOT NULL DEFAULT 0,
            criado_em      TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- Registro de perdas e desperdícios
        CREATE TABLE IF NOT EXISTS perdas (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            data_perda     TEXT    NOT NULL,
            insumo_id      INTEGER REFERENCES insumos(id),
            prato_id       INTEGER REFERENCES pratos(id),
            quantidade     REAL    NOT NULL,
            motivo         TEXT    NOT NULL DEFAULT 'sobra_producao',
            custo_estimado REAL    DEFAULT 0,
            observacao     TEXT,
            registrado_por TEXT,
            criado_em      TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- Metas de desperdício por insumo (NULL = meta global)
        CREATE TABLE IF NOT EXISTS metas_desperdicio (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            insumo_id   INTEGER REFERENCES insumos(id),
            pct_maximo  REAL    NOT NULL DEFAULT 15.0,
            ativo       INTEGER DEFAULT 1,
            criado_em   TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- Sprint 2: Fornecedores
        CREATE TABLE IF NOT EXISTS fornecedores (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nome      TEXT NOT NULL UNIQUE,
            cnpj      TEXT,
            tipo      TEXT DEFAULT 'supermercado',
            ativo     INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Sprint 2: Configuracoes do sistema (chave/valor)
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave         TEXT PRIMARY KEY,
            valor         TEXT NOT NULL,
            descricao     TEXT,
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Sprint 2: Movimentacoes de estoque (auditoria central)
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            insumo_id       INTEGER NOT NULL REFERENCES insumos(id),
            tipo            TEXT NOT NULL,
            quantidade      REAL NOT NULL,
            custo_unitario  REAL DEFAULT 0,
            custo_total     REAL DEFAULT 0,
            referencia_id   INTEGER,
            referencia_tipo TEXT,
            observacao      TEXT,
            criado_em       TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Sprint 2: Historico de precos por fornecedor
        CREATE TABLE IF NOT EXISTS precos_fornecedores (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            insumo_id        INTEGER NOT NULL REFERENCES insumos(id),
            fornecedor_id    INTEGER NOT NULL REFERENCES fornecedores(id),
            preco_unitario   REAL NOT NULL,
            quantidade_nota  REAL,
            data_compra      TEXT NOT NULL,
            compra_id        INTEGER REFERENCES compras(id),
            criado_em        TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Sprint 3: Lista de compras gerada automaticamente
        CREATE TABLE IF NOT EXISTS lista_compras (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            data_geracao     TEXT NOT NULL,
            insumo_id        INTEGER NOT NULL REFERENCES insumos(id),
            quantidade       REAL NOT NULL,
            preco_estimado   REAL DEFAULT 0,
            status           TEXT DEFAULT 'pendente', -- pendente, comprado, ignorado
            urgencia         TEXT DEFAULT 'alerta',   -- alerta, critica
            criado_em        TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    # Seeds: configuracoes padrao
    cursor.executemany(
        "INSERT OR IGNORE INTO configuracoes (chave, valor, descricao) VALUES (?, ?, ?)",
        [
            ('dias_estoque_minimo', '2',          'Gerar alerta quando faltar menos de X dias de estoque'),
            ('dias_media_consumo',  '7',          'Calcular consumo medio com base nos ultimos X dias'),
            ('dias_alvo_compra',    '3',          'Quantidade de dias de estoque que a lista visa atingir'),
            ('taxa_99food',         '10.5',       'Comissao 99Food em %'),
            ('taxa_ifood',          '16.0',       'Comissao iFood em %'),
            ('ocr_provider',        'tesseract',  'Provider OCR: tesseract ou google_vision'),
            ('google_vision_key',   '',           'Chave Google Vision API (vazio = usar tesseract)'),
        ]
    )

    # Seeds: fornecedores base
    cursor.executemany(
        "INSERT OR IGNORE INTO fornecedores (nome, tipo) VALUES (?, ?)",
        [
            ('Atacadão',           'supermercado'),
            ('Assaí',              'supermercado'),
            ('Tático',             'supermercado'),
            ('Fornecedor Genérico','outro'),
        ]
    )

    conn.commit()
    conn.close()
    print("[OK] Tabelas criadas com sucesso (Sprint 1 + Sprint 2).")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    criar_tabelas()
