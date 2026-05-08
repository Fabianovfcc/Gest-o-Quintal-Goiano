import sys, os
sys.path.insert(0, os.path.abspath('backend'))
os.chdir('backend')

os.environ['ENVIRONMENT'] = 'development'
os.environ['CMV_API_KEY'] = 'testkey123'
os.environ['CMV_JWT_SECRET'] = 'testsecret123'
os.environ['CMV_ADMIN_PASSWORD'] = 'senha123'
os.environ['CMV_ALLOWED_ORIGINS'] = 'http://localhost:5000'

import app as a
with a.app.test_client() as c:
    r = c.get('/login.html')
    print(f"  {'OK' if r.status_code == 200 else 'ERRO'}  GET /login.html -> {r.status_code} (esperado 200)")
    r = c.get('/dashboard.html')
    print(f"  {'OK' if r.status_code == 200 else 'ERRO'}  GET /dashboard.html -> {r.status_code} (esperado 200)")
    r = c.get('/')
    print(f"  {'OK' if r.status_code == 200 else 'ERRO'}  GET / -> {r.status_code} (esperado 200)")
