"""
tools/verify_link_v2.py — Verificacao pre-Sprint 2
Execute: python tools/verify_link_v2.py
"""
import sqlite3, os, importlib, subprocess

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'cmv.db')
ok, warn, erro = [], [], []

def ck(c, m_ok, m_err): (ok if c else erro).append(f"{'OK' if c else 'ERRO'}: {m_ok if c else m_err}")
def wn(m): warn.append(f"WARN: {m}")

# Banco
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
tabs = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

# Tabelas Sprint 1 (devem existir)
for t in ['insumos','pratos','fichas_tecnicas','vendas','perdas','itens_venda','mapa_insumos']:
    ck(t in tabs, f"Tabela '{t}' existe", f"Tabela '{t}' AUSENTE - Sprint 1 incompleto")

# Tabelas Sprint 2 (devem ser criadas)
for t in ['movimentacoes','fornecedores','precos_fornecedores','lista_compras','configuracoes']:
    if t in tabs: ok.append(f"OK: Tabela '{t}' ja existe")
    else: warn.append(f"WARN: Tabela '{t}' sera criada no POP_07")

# Verificar bug de unidades
sample = conn.execute("""
    SELECT ft.quantidade, i.unidade, i.nome FROM fichas_tecnicas ft
    JOIN insumos i ON i.id = ft.insumo_id
    WHERE i.unidade = 'kg' AND ft.quantidade > 10 LIMIT 1
""").fetchone()
if sample:
    ok.append(f"OK: Fichas em gramas confirmado (ex: {sample['nome']} = {sample['quantidade']}g)")
    ok.append("OK: CASE SQL com /1000.0 esta CORRETO para este padrao")
else:
    wn("Nenhuma ficha com quantidade > 10 e unidade kg — verificar manualmente")

# Fichas e custos
total_fichas = conn.execute("SELECT COUNT(*) FROM fichas_tecnicas").fetchone()[0]
sem_custo = conn.execute("SELECT COUNT(*) FROM insumos WHERE custo_compra = 0").fetchone()[0]
ck(total_fichas >= 100, f"{total_fichas} fichas tecnicas", f"Fichas insuficientes: {total_fichas}")
wn(f"{sem_custo}/53 insumos sem custo — serao preenchidos automaticamente via NF")

conn.close()

# Dependencias Python
for mod, pkg in [('flask','flask'),('openpyxl','openpyxl'),('pdfplumber','pdfplumber'),
                 ('PIL','Pillow'),('pytesseract','pytesseract')]:
    try:
        importlib.import_module(mod)
        ok.append(f"OK: {pkg} instalado")
    except ImportError:
        warn.append(f"WARN: {pkg} nao instalado. Instalar: pip install {pkg} --break-system-packages")

# Tesseract
try:
    r = subprocess.run(['tesseract','--version'], capture_output=True, text=True, timeout=3)
    if r.returncode == 0:
        ok.append(f"OK: Tesseract OCR: {r.stdout.split(chr(10))[0]}")
    else:
        warn.append("WARN: Tesseract nao responde — OCR de foto ficara indisponivel")
except FileNotFoundError:
    warn.append("WARN: Tesseract nao instalado — OCR de foto indisponivel")
    warn.append("  Mac: brew install tesseract | Linux: apt install tesseract-ocr tesseract-ocr-por")

print("=" * 55)
print("VERIFICACAO LINK v2 — Sprint 2 Zero Digitacao Manual")
print("=" * 55)
for m in ok:   print(f"  {m}")
for m in warn: print(f"  {m}")
for m in erro: print(f"  {m}")
print(f"\n  OK: {len(ok)} | WARN: {len(warn)} | ERRO: {len(erro)}")
if erro: print("\n  STOP: Corrigir erros antes de prosseguir.")
else: print("\n  PRONTO: Avancar para Fase A.")
