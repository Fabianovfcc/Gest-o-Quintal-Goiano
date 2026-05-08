import sqlite3
import os

db_path = os.path.join('data', 'cmv.db')
if not os.path.exists(db_path):
    print(f"Banco de dados não encontrado em {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cols = conn.execute('PRAGMA table_info(perdas)').fetchall()
print('Schema atual de perdas:')
for c in cols:
    nullable = 'NULLABLE' if c[3] == 0 else 'NOT NULL'
    print(f'  {c[1]:20} {c[2]:10} {nullable}')

nomes = [c[1] for c in cols]
insumo_col = next((c for c in cols if c[1] == 'insumo_id'), None)

if insumo_col:
    print(f'\ninsumo_id nullable: {insumo_col[3] == 0}')
else:
    print('\ninsumo_id não encontrado!')

print(f'prato_id existe: {"prato_id" in nomes}')
conn.close()
