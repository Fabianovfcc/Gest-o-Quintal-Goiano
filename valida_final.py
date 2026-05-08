import sys, os
sys.path.insert(0, 'backend')

os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('CMV_API_KEY', 'testkey123')
os.environ.setdefault('CMV_JWT_SECRET', 'testsecret123')
os.environ.setdefault('CMV_ADMIN_PASSWORD', 'senha123')
os.environ.setdefault('CMV_ALLOWED_ORIGINS', 'http://localhost:5000')

import app as a

K = {'X-API-Key': 'testkey123'}

with a.app.test_client() as c:
    tests = [
        ('GET',  '/api/insumos',            {},           401),
        ('GET',  '/api/status',             {},           200),
        ('POST', '/api/auth/login',         {'json': {"senha": "errada"}}, 401),
        ('POST', '/api/auth/login',         {'json': {"senha": "senha123"}}, 200),
        ('GET',  '/api/insumos',            {'headers': K}, 200),
        ('GET',  '/api/pratos',             {'headers': K}, 200),
        ('GET',  '/api/configuracoes',      {'headers': K}, 200),
        ('GET',  '/api/fornecedores',       {'headers': K}, 200),
        ('GET',  '/api/inventario',         {'headers': K}, 200),
        ('GET',  '/api/lista-compras/hoje', {'headers': K}, 200),
        ('GET',  '/api/desperdicio/hoje',   {'headers': K}, 200),
        ('GET',  '/api/dashboard/kpis',     {'headers': K}, 200),
        ('GET',  '/api/rotina/kpis',        {'headers': K}, 200),
        ('GET',  '/api/relatorio/pdf',      {'headers': K}, 200),
        ('GET',  '/api/vendas/recentes',    {'headers': K}, 200),
    ]
    all_ok = True
    for method, url, kwargs, expected in tests:
        r = c.open(url, method=method, **kwargs)
        ok = r.status_code == expected
        if not ok:
            all_ok = False
        print(f"  {'OK' if ok else 'ERRO'}  {method} {url} -> {r.status_code} (esperado {expected})")

    r = c.get('/api/status')
    has_h = 'X-Content-Type-Options' in r.headers
    print(f"  {'OK' if has_h else 'ERRO'}  Headers de segurança")
    print(f"\\n{'15/15 PRONTO PARA DEPLOY' if all_ok and has_h else 'Corrigir itens com ERRO'}")
