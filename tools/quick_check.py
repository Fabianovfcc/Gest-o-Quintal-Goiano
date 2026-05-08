import os, sqlite3
try: import requests; HAS_REQ=True
except: HAS_REQ=False
DB='data/cmv.db'; API='http://localhost:5000/api'
ok,err=[],[]
conn=sqlite3.connect(DB)
tabs={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
for t in ['movimentacoes','fornecedores','precos_fornecedores','lista_compras','configuracoes']:
    (ok if t in tabs else err).append(f'tab:{t}')
cfg=conn.execute('SELECT COUNT(*) FROM configuracoes').fetchone()[0]
forn=conn.execute('SELECT COUNT(*) FROM fornecedores').fetchone()[0]
conn.close()
ok.append(f'cfg:{cfg}'); ok.append(f'forn:{forn}')
for h in ['rotina.html','insumos.html','fichas.html']:
    (ok if os.path.exists(h) else err).append(h)
if HAS_REQ:
    for path in ['/api/rotina/kpis','/api/lista-compras/hoje','/api/fornecedores',
                 '/api/desperdicio/historico']:
        try:
            r=requests.get(API.replace('/api','')+path,timeout=3)
            (ok if r.status_code!=404 else err).append(f'GET {path}:{r.status_code}')
        except Exception as e:
            err.append(f'GET {path}:ERR {e}')
print('=== Sprint 2 Quick Check ===')
for m in ok: print(' OK',m)
for m in err: print(' MISS',m)
print(f'\nOK:{len(ok)} MISS:{len(err)}')
