import sys, os
sys.path.insert(0, os.path.abspath('backend'))
os.chdir('backend')

os.environ['ENVIRONMENT'] = 'development'
os.environ['CMV_API_KEY'] = 'testkey123'
os.environ['CMV_JWT_SECRET'] = 'testsecret123'
os.environ['CMV_ADMIN_PASSWORD'] = 'senha123'
os.environ['CMV_ALLOWED_ORIGINS'] = 'http://localhost:5000'

import app as a
print(f"OK App carregou — {len(set(r.rule for r in a.app.url_map.iter_rules()))} rotas")

with a.app.test_client() as c:
    r = c.get('/api/status')
    print(f"  {'OK' if r.status_code == 200 else 'ERRO'}  GET /api/status -> {r.status_code}")
    r = c.get('/api/insumos')
    print(f"  {'OK' if r.status_code == 401 else 'ERRO'}  GET /api/insumos sem auth -> {r.status_code}")
    r = c.post('/api/auth/login', json={"senha": "senha123"})
    print(f"  {'OK' if r.status_code == 200 else 'ERRO'}  POST /api/auth/login -> {r.status_code}")
    print("\nOK Pronto para push" if True else "")
