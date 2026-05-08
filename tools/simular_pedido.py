"""tools/simular_pedido.py — Testa motor de baixa"""
import sqlite3, requests, os
DB = os.path.join(os.path.dirname(__file__),'..','data','cmv.db')
API= 'http://localhost:5000/api'
conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
prato=conn.execute("SELECT id,nome FROM pratos WHERE nome LIKE '%Strogonoff%' LIMIT 1").fetchone()
if not prato:
    prato=conn.execute("SELECT id,nome FROM pratos LIMIT 1").fetchone()
ins=conn.execute("SELECT nome,estoque_atual,unidade FROM insumos WHERE nome LIKE '%frango%' LIMIT 1").fetchone()
if ins: print(f"ANTES: {ins['nome']} = {ins['estoque_atual']} {ins['unidade']}")
conn.close()
print(f"\nProcessando: 1x {prato['nome']} (id={prato['id']})...")
r=requests.post(f'{API}/pedidos/processar-multiplos',json={'venda_id':999,'itens':[{'prato_id':prato['id'],'quantidade':1}]})
d=r.json()
if d.get('ok'):
    print(f"Status: OK | Custo total: R$ {d.get('custo_total',0):.4f}")
    for i in d.get('insumos_baixados',[])[:5]:
        print(f"  {i['nome']}: -{i['baixa_real']} {i['unidade']}")
    if d.get('alertas'): print(f"ALERTAS: {d['alertas']}")
else: print(f"ERRO: {d}")
conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
ins=conn.execute("SELECT nome,estoque_atual,unidade FROM insumos WHERE nome LIKE '%frango%' LIMIT 1").fetchone()
if ins: print(f"\nDEPOIS: {ins['nome']} = {ins['estoque_atual']:.4f} {ins['unidade']}")
print("ESPERADO: reducao de 0.210 kg (210g / 1000)")
conn.close()
