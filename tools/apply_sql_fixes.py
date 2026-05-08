"""
tools/apply_sql_fixes.py
Aplica correcoes SQL diretas no banco existente.
Execute apos atualizar database.py e seed.py.
Execute: python tools/apply_sql_fixes.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cmv.db')

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

print("Aplicando correcoes SQL no banco existente...")

conn.execute("UPDATE insumos SET unidade = 'un' WHERE nome = 'Ovo'")
print("[OK] Ovo: unidade corrigida para 'un'")

conn.execute("""
    UPDATE fichas_tecnicas
    SET quantidade = 1, observacao = '1 ovo para empanamento'
    WHERE insumo_id = (SELECT id FROM insumos WHERE nome = 'Ovo')
      AND quantidade < 0.5
""")
conn.execute("""
    UPDATE fichas_tecnicas
    SET quantidade = 2, observacao = '2 ovos para empanamento'
    WHERE insumo_id = (SELECT id FROM insumos WHERE nome = 'Ovo')
      AND quantidade >= 0.5 AND quantidade < 1
""")
print("[OK] Fichas tecnicas: quantidades de ovo corrigidas para inteiros")

conn.commit()
conn.close()
print("\n[OK] Correcoes aplicadas. Rode verify_link.py para confirmar.")
