"""
tools/verify_link_sprint3.py
Verifica credenciais e dependências do Sprint 3.
Execute: python tools/verify_link_sprint3.py
"""
import os, importlib, subprocess

ok_l, warn_l, err_l = [], [], []
def ok(m):   ok_l.append(f"OK:   {m}")
def warn(m): warn_l.append(f"WARN: {m}")
def erro(m): err_l.append(f"ERRO: {m}")

# .env
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    ok(".env encontrado")
    content = open(env_path).read()
    env_vars = {l.split('=',1)[0]: l.split('=',1)[1].strip() for l in content.split('\n') if '=' in l}
    env_mode = env_vars.get('ENVIRONMENT', 'development')
    
    for var, obrig in [
        ('SUPABASE_URL', True), ('SUPABASE_KEY', True),
        ('SUPABASE_DB_URL', True), ('FOOD99_API_KEY', False),
        ('FOOD99_STORE_ID', False), ('IFOOD_CLIENT_ID', False),
    ]:
        val = env_vars.get(var, '')
        preenchido = bool(val and 'SEU_' not in val and val != '')
        if preenchido:
            ok(f"{var} configurado")
        elif obrig and env_mode == 'production':
            erro(f"{var} ausente ou vazio — obrigatório para produção")
        elif obrig:
            warn(f"{var} não configurado — necessário para produção (Supabase)")
        else:
            warn(f"{var} não configurado — integração automática indisponível")
else:
    erro(".env não encontrado — criar na raiz do projeto")

# Dependências Python
for mod, pkg in [
    ('psycopg2',  'psycopg2-binary'),
    ('reportlab', 'reportlab'),
    ('dotenv',    'python-dotenv'),
    ('schedule',  'schedule'),
    ('requests',  'requests'),
    ('PIL',       'Pillow'),
]:
    try:
        importlib.import_module(mod)
        ok(f"{pkg} instalado")
    except ImportError:
        warn(f"{pkg} não instalado — pip install {pkg} --break-system-packages")

# Tesseract
try:
    r = subprocess.run(['tesseract','--version'],
                       capture_output=True, text=True, timeout=3)
    ok(f"Tesseract: {r.stdout.split(chr(10))[0]}")
except Exception:
    warn("Tesseract não instalado — OCR de foto desabilitado")

# Supabase conexão
try:
    from dotenv import load_dotenv
    load_dotenv(env_path)
    db_url = os.getenv('SUPABASE_DB_URL', '')
    env_mode = os.getenv('ENVIRONMENT', 'development')
    if env_mode == 'production' and db_url and 'supabase' in db_url and 'SEU_' not in db_url:
        import psycopg2
        conn = psycopg2.connect(db_url, connect_timeout=5)
        conn.close()
        ok("Supabase: conexão PostgreSQL OK")
    elif env_mode == 'production':
        erro("Supabase: DB_URL não configurada ou inválida para produção")
    else:
        warn("Supabase: pulando teste de conexão (modo development)")
except Exception as e:
    erro(f"Supabase: falha na conexão — {e}")

print("=" * 55)
print("VERIFY LINK — Sprint 3")
print("=" * 55)
for m in ok_l:   print(f"  {m}")
for m in warn_l: print(f"  {m}")
for m in err_l:  print(f"  {m}")
print(f"\n  OK: {len(ok_l)} | WARN: {len(warn_l)} | ERRO: {len(err_l)}")
if err_l:
    print("\n  STOP: Configurar variáveis obrigatórias no .env antes de avançar.")
else:
    print("\n  PRONTO: Avançar para Bloco A.")
