import sys, os
sys.path.insert(0, 'backend')
#os.chdir('backend') # don't change dir, keep it the same as how we usually run app
import app as a

print(f"Rotas únicas: {len(set(r.rule for r in a.app.url_map.iter_rules()))}")

with a.app.test_client() as c:
    # Deve retornar 401 sem API Key
    r = c.get('/api/insumos')
    print(f"  {'OK' if r.status_code == 401 else 'ERRO'}  GET /api/insumos sem auth -> {r.status_code} (esperado 401)")

    # Status público deve funcionar
    r = c.get('/api/status')
    print(f"  {'OK' if r.status_code == 200 else 'ERRO'}  GET /api/status -> {r.status_code} (esperado 200)")

    # Login com senha errada deve retornar 401
    r = c.post('/api/auth/login', json={"senha": "errada"})
    print(f"  {'OK' if r.status_code == 401 else 'ERRO'}  POST /api/auth/login senha errada -> {r.status_code} (esperado 401)")

    # Headers de segurança presentes
    r = c.get('/api/status')
    has_headers = 'X-Content-Type-Options' in r.headers
    print(f"  {'OK' if has_headers else 'ERRO'}  Headers de segurança presentes")
