# POP 01 — Correção do Banco de Dados

## Objetivo
Adicionar a tabela `itens_venda` que estava ausente em `database.py`.

## Arquivo alvo
`backend/database.py` → função `criar_tabelas()` → bloco `cursor.executescript()`

## Posição de inserção
Após o bloco de criação da tabela `itens_compra`, antes do fechamento do script.

## SQL a inserir
CREATE TABLE IF NOT EXISTS itens_venda (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id       INTEGER NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
    prato_id       INTEGER NOT NULL REFERENCES pratos(id),
    quantidade     INTEGER NOT NULL DEFAULT 1,
    valor_unitario REAL    NOT NULL DEFAULT 0,
    criado_em      TEXT    DEFAULT (datetime('now','localtime'))
);

## Teste de validação
python -c "from backend.database import criar_tabelas; criar_tabelas()"
Depois: verificar com verify_link.py

## Caso de borda
CREATE TABLE IF NOT EXISTS garante que dados existentes não são afetados.
