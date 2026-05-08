"""Patch kpis route: data_venda -> data"""
import re
p = 'backend/app.py'
c = open(p, encoding='utf-8').read()
old = '''        pedidos = conn.execute(
            f"SELECT COUNT(*) FROM vendas WHERE date(data_venda)={data_sql}"
        ).fetchone()[0]
        faturamento = conn.execute(
            f"SELECT COALESCE(SUM(faturamento_bruto),0) FROM vendas WHERE date(data_venda)={data_sql}"
        ).fetchone()[0]'''
new = '''        pedidos = conn.execute(
            f"SELECT COALESCE(SUM(pedidos),0) FROM vendas WHERE date(data)={data_sql}"
        ).fetchone()[0]
        faturamento = conn.execute(
            f"SELECT COALESCE(SUM(faturamento_bruto),0) FROM vendas WHERE date(data)={data_sql}"
        ).fetchone()[0]'''
if old in c:
    open(p,'w',encoding='utf-8').write(c.replace(old,new,1))
    print('OK patched')
else:
    print('WARN: pattern not found, searching...')
    for i,l in enumerate(c.split('\n'),1):
        if 'data_venda' in l: print(i,l)
