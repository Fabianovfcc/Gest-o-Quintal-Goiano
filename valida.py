import sys, os
sys.path.insert(0, 'backend')
import app as a

rules = sorted(set(r.rule for r in a.app.url_map.iter_rules()))
print(f"Total rotas únicas: {len(rules)}")  # Esperado: 46

with a.app.test_client() as c:
    testes = [
        ('GET',  '/api/status'),
        ('GET',  '/api/configuracoes'),
        ('PUT',  '/api/configuracoes'),
        ('GET',  '/api/insumos'),
        ('GET',  '/api/pratos'),
        ('GET',  '/api/lista-compras/hoje'),
        ('GET',  '/api/desperdicio/hoje'),
        ('POST', '/api/desperdicio'),
        ('GET',  '/api/vendas/recentes'),
        ('GET',  '/api/dashboard/kpis'),
        ('GET',  '/api/rotina/kpis'),
        ('GET',  '/api/inventario'),
        ('GET',  '/api/relatorio/pdf'),
    ]
    for method, url in testes:
        r = c.get(url) if method == 'GET' else c.open(url, method=method, json={})
        status = 'OK' if r.status_code < 500 else 'ERRO'
        print(f"  {status}  {method} {url} -> {r.status_code}")
