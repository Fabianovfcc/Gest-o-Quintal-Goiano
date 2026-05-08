"""
tools/verify_link.py
Verifica se todos os pré-requisitos do Sprint 1 estão ativos.
Execute: python tools/verify_link.py
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cmv.db')
REQUIRED_TABLES = [
    'categorias', 'insumos', 'pratos', 'fichas_tecnicas',
    'vendas', 'compras', 'itens_compra', 'mapa_insumos', 'inventario'
]
MISSING_TABLES = ['itens_venda']

print("=" * 50)
print("VERIFICACAO DE LINK - Sprint 1 CMV Quintal Goiano")
print("=" * 50)

if not os.path.exists(DB_PATH):
    print(f"[ERRO] BANCO NAO ENCONTRADO: {DB_PATH}")
    sys.exit(1)
print(f"[OK] Banco encontrado: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
tabelas_existentes = {r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()}

for t in REQUIRED_TABLES:
    if t in tabelas_existentes:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"[OK] Tabela '{t}': {count} registros")
    else:
        print(f"[ERRO] Tabela '{t}' AUSENTE")

print("\n--- BUGS CONFIRMADOS ---")
for t in MISSING_TABLES:
    if t not in tabelas_existentes:
        print(f"[WARN] Tabela '{t}' ausente - Bug B1 confirmado (corrigir em Fase A)")
    else:
        print(f"[OK] Tabela '{t}' ja existe")

ovo = conn.execute("SELECT unidade FROM insumos WHERE nome = 'Ovo'").fetchone()
if ovo:
    if ovo[0] == 'dz':
        print("[WARN] Ovo em unidade 'dz' - Bug B8 confirmado (corrigir em Fase A)")
    else:
        print(f"[OK] Ovo em unidade '{ovo[0]}'")

pendentes = conn.execute(
    "SELECT COUNT(*) FROM insumos WHERE status_cadastro = 'PENDENTE'"
).fetchone()[0]
print(f"\n[INFO] Insumos PENDENTES (sem custo): {pendentes}/53")
print(f"[INFO] CMV disponivel: {'NAO' if pendentes > 0 else 'SIM'}")

conn.close()
print("\n[OK] Verificacao concluida. Prosseguir para Fase A.")
