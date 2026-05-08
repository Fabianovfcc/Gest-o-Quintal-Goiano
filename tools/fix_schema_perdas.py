"""
tools/fix_schema_perdas.py
Recria a tabela perdas com schema correto sem perder dados.
Execute: python tools/fix_schema_perdas.py
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'cmv.db')
if not os.path.exists(DB):
    print(f"Erro: Banco de dados não encontrado em {DB}")
    exit(1)

conn = sqlite3.connect(DB)

print("Corrigindo schema da tabela perdas...")

try:
    conn.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE IF NOT EXISTS perdas_nova (
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

        INSERT INTO perdas_nova (id, data_perda, insumo_id, quantidade, motivo, custo_estimado, observacao, registrado_por, criado_em)
            SELECT id, data_perda, insumo_id, quantidade, motivo, custo_estimado,
                   observacao, registrado_por, criado_em
            FROM perdas;

        DROP TABLE perdas;
        ALTER TABLE perdas_nova RENAME TO perdas;

        PRAGMA foreign_keys = ON;
    """)
    conn.commit()
    print("Sucesso ao migrar a tabela perdas.")
except Exception as e:
    conn.rollback()
    print(f"Erro na migração: {e}")
    exit(1)

cols = conn.execute("PRAGMA table_info(perdas)").fetchall()
print("Schema corrigido:")
for c in cols:
    null_str = "NULLABLE" if c[3] == 0 else "NOT NULL"
    print(f"  {c[1]:20} {c[2]:10} {null_str}")

registros = conn.execute("SELECT COUNT(*) FROM perdas").fetchone()[0]
print(f"\nRegistros preservados: {registros}")
conn.close()
print("Concluido.")
