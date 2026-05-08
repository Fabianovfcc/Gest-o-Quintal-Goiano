"""
tools/migrar_para_supabase.py
Migra dados do SQLite local para Supabase PostgreSQL.
Execute APÓS o schema estar criado no Supabase.
Execute: python tools/migrar_para_supabase.py
"""
import sqlite3, os, sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

try:
    import psycopg2
except ImportError:
    print("ERRO: psycopg2-binary não instalado.")
    print("  pip install psycopg2-binary --break-system-packages")
    sys.exit(1)

SQLITE_PATH = str(Path(__file__).parent.parent / 'data' / 'cmv.db')
PG_URL = os.getenv('SUPABASE_DB_URL', '')

if not PG_URL:
    print("ERRO: SUPABASE_DB_URL não configurado no .env")
    sys.exit(1)

sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row

try:
    pg_conn = psycopg2.connect(PG_URL)
    pg_conn.autocommit = False
    print("Conexão Supabase OK")
except Exception as e:
    print(f"ERRO ao conectar no Supabase: {e}")
    sys.exit(1)

# Ordem respeitando FKs
TABELAS = [
    'categorias', 'insumos', 'pratos', 'fichas_tecnicas',
    'fornecedores', 'compras', 'itens_compra', 'mapa_insumos',
    'vendas', 'itens_venda', 'inventario', 'movimentacoes',
    'perdas', 'metas_desperdicio', 'precos_fornecedores',
    'lista_compras', 'configuracoes',
]

cursor_pg = pg_conn.cursor()
print("\nIniciando migração SQLite → Supabase...\n")

for tabela in TABELAS:
    try:
        rows = sqlite_conn.execute(f"SELECT * FROM {tabela}").fetchall()
    except Exception:
        print(f"  {tabela}: não existe no SQLite — pulando")
        continue

    if not rows:
        print(f"  {tabela}: vazia — pulando")
        continue

    cols = list(rows[0].keys())
    placeholders = ','.join(['%s'] * len(cols))
    cols_str = ','.join(cols)
    count = 0

    for row in rows:
        valores = tuple(row[c] for c in cols)
        try:
            cursor_pg.execute(
                f"INSERT INTO {tabela} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                valores
            )
            count += 1
        except Exception as e:
            print(f"  WARN {tabela}: {e}")

    print(f"  {tabela}: {count}/{len(rows)} registros migrados")

# Sincronizar sequences
for tabela in TABELAS:
    try:
        cursor_pg.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{tabela}', 'id'),
                COALESCE(MAX(id), 1)
            ) FROM {tabela}
        """)
    except Exception:
        pass

pg_conn.commit()
sqlite_conn.close()
pg_conn.close()
print("\nMigração concluída com sucesso.")
print("Verifique no Supabase Dashboard → Table Editor.")
