"""tools/validate_sprint2.py — Checklist final Sprint 2"""
import sqlite3, os, requests
DB=os.path.join(os.path.dirname(__file__),'..','data','cmv.db')
API='http://localhost:5000/api'
ok_l,err_l=[],[]
def ck(c,m_ok,m_err): (ok_l if c else err_l).append(('OK' if c else 'ERRO')+': '+(m_ok if c else m_err))
conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
tabs={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
for t in ['movimentacoes','fornecedores','precos_fornecedores','lista_compras','configuracoes']:
    ck(t in tabs,f"Tabela '{t}' existe",f"Tabela '{t}' AUSENTE")
cfg=conn.execute('SELECT COUNT(*) FROM configuracoes').fetchone()[0]
forn=conn.execute('SELECT COUNT(*) FROM fornecedores').fetchone()[0]
ck(cfg>=7,f'Configuracoes: {cfg}',f'Configuracoes insuficientes: {cfg}')
ck(forn>=3,f'Fornecedores: {forn}',f'Fornecedores seed ausentes: {forn}')
conn.close()
for h in ['rotina.html','insumos.html','fichas.html','notas.html','dashboard.html']:
    ck(os.path.exists(h),f'{h} existe',f'{h} NAO EXISTE')
for h in ['rotina.html','insumos.html','fichas.html']:
    try:
        c=open(h,encoding='utf-8').read()
        ck('rotina.html' in c,f'{h}: link Rotina presente',f'{h}: link Rotina AUSENTE')
    except: err_l.append(f'ERRO: nao leu {h}')
for method,path,body in [
    ('POST','/api/pedidos/processar-multiplos',{'venda_id':0,'itens':[]}),
    ('POST','/api/desperdicio/por-prato',{'prato_id':1,'quantidade_porcoes':0}),
    ('POST','/api/desperdicio/por-insumo',{'insumo_id':1,'quantidade':0}),
    ('GET', '/api/lista-compras/hoje',None),
    ('GET', '/api/lista-compras/gerar',None),
    ('GET', '/api/fornecedores',None),
    ('GET', '/api/rotina/kpis',None),
    ('GET', '/api/rotina/perdas-hoje',None),
    ('GET', '/api/desperdicio/historico',None),
]:
    try:
        fn=requests.post if method=='POST' else requests.get
        r=fn(API.replace('/api','')+path,json=body,timeout=4)
        ck(r.status_code!=404,f'{method} {path}: {r.status_code}',f'{method} {path}: 404 NOT FOUND')
    except Exception as e:
        err_l.append(f'ERRO: {method} {path}: {e}')
for f in ['backend/motor_baixa.py','backend/parser_ocr.py','backend/motor_compras.py']:
    ck(os.path.exists(f),f'{f} existe',f'{f} AUSENTE')
print('='*55)
print('VALIDACAO SPRINT 2 — Zero Digitacao Manual')
print('='*55)
for m in ok_l: print(f'  {m}')
for m in err_l: print(f'  {m}')
print(f'\n  OK: {len(ok_l)} | ERRO: {len(err_l)}')
if not err_l: print('\n  SPRINT 2 CONCLUIDO.')
else: print('\n  Corrigir erros acima.')
