"""tools/validate_sprint1.py — Checklist final Sprint 1"""
import sqlite3, os, sys
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'cmv.db')
API = 'http://localhost:5000/api'
ok_list, err_list = [], []

def chk(cond, msg_ok, msg_err):
    if cond: ok_list.append(f'[OK] {msg_ok}')
    else: err_list.append(f'[ERRO] {msg_err}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
tabs = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

chk('itens_venda' in tabs, 'Tabela itens_venda existe', 'itens_venda AUSENTE — Bug B1 nao corrigido')
chk('perdas' in tabs, 'Tabela perdas existe', 'perdas AUSENTE')

ovo = conn.execute("SELECT unidade FROM insumos WHERE nome='Ovo'").fetchone()
chk(ovo and ovo['unidade']=='un', "Ovo unidade='un'", "Ovo ainda em unidade errada — Bug B8")

qtds = [r['quantidade'] for r in conn.execute(
    "SELECT ft.quantidade FROM fichas_tecnicas ft JOIN insumos i ON i.id=ft.insumo_id WHERE i.nome='Ovo'").fetchall()]
fracs = [q for q in qtds if q != int(q)]
chk(not fracs, 'Quantidades de ovo sao inteiras', f'Ovo com fracoes: {fracs}')
conn.close()

# HTMLs existem
for h in ['insumos.html','fichas.html','estoque.html','notas.html','dashboard.html']:
    path = os.path.join(os.path.dirname(__file__), '..', h)
    chk(os.path.exists(path), f'{h} existe', f'{h} AUSENTE')

# Sidebar com insumos.html em todos
for h in ['dashboard.html','notas.html','fichas.html','insumos.html','estoque.html']:
    path = os.path.join(os.path.dirname(__file__), '..', h)
    try:
        c = open(path, encoding='utf-8').read()
        chk('href="insumos.html"' in c, f'{h}: link insumos.html presente', f'{h}: link insumos.html AUSENTE')
        chk('Em breve' in c or 'opacity:0.45' in c, f'{h}: links futuros marcados', f'{h}: links futuros sem marcacao')
    except: err_list.append(f'[ERRO] Nao leu {h}')

# Insumos.html tem features
try:
    ins_c = open(os.path.join(os.path.dirname(__file__),'..','insumos.html'),encoding='utf-8').read()
    chk('prog-global' in ins_c, 'insumos.html: barra progresso global', 'insumos.html: sem progresso')
    chk('prog-cats' in ins_c, 'insumos.html: cards por categoria', 'insumos.html: sem cards')
    chk('cell-edit' in ins_c, 'insumos.html: edicao inline', 'insumos.html: sem edicao inline')
    chk('exportar-template' in ins_c, 'insumos.html: botao template', 'insumos.html: sem template')
    chk('confirmarImport' in ins_c, 'insumos.html: confirmar importacao', 'insumos.html: sem confirmar')
except Exception as e: err_list.append(f'[ERRO] insumos.html: {e}')

# fichas.html tem features
try:
    fic_c = open(os.path.join(os.path.dirname(__file__),'..','fichas.html'),encoding='utf-8').read()
    chk('abrirModalNovoPrato' in fic_c, 'fichas.html: modal novo prato', 'fichas.html: sem modal')
    chk('adicionarIngrediente' in fic_c, 'fichas.html: form ingrediente', 'fichas.html: sem form')
    chk('duplicarPrato' in fic_c, 'fichas.html: duplicar', 'fichas.html: sem duplicar')
    chk('inp-obs' in fic_c, 'fichas.html: coluna obs', 'fichas.html: sem obs')
except Exception as e: err_list.append(f'[ERRO] fichas.html: {e}')

# dashboard fallback
try:
    d_c = open(os.path.join(os.path.dirname(__file__),'..','dashboard.html'),encoding='utf-8').read()
    chk('4.403' not in d_c, 'dashboard: sem valores hardcoded', 'dashboard: AINDA tem valores hardcoded')
    chk('API offline' in d_c, 'dashboard: fallback neutro', 'dashboard: sem fallback neutro')
except Exception as e: err_list.append(f'[ERRO] dashboard: {e}')

# API
if HAS_REQUESTS:
    try:
        r = requests.get(f'{API}/status', timeout=3)
        chk(r.status_code==200, 'API respondendo', 'API offline')
        # insumo_id no retorno da ficha
        r2 = requests.get(f'{API}/pratos/1/ficha', timeout=3)
        if r2.status_code==200:
            ings = r2.json().get('ingredientes',[])
            chk(all('insumo_id' in i for i in ings) if ings else True,
                'GET /api/pratos/1/ficha retorna insumo_id', 'GET /api/pratos/1/ficha sem insumo_id')
        # template
        r3 = requests.get(f'{API}/insumos/exportar-template', timeout=5)
        chk(r3.status_code==200, 'GET /api/insumos/exportar-template OK', f'exportar-template status {r3.status_code}')
    except Exception as e:
        err_list.append(f'[ERRO] API inacessivel: {e}')
else:
    err_list.append('[WARN] requests nao instalado — validacao de API pulada')

print('\n'+'='*55)
print('VALIDACAO SPRINT 1 — CMV Quintal Goiano')
print('='*55)
for m in ok_list: print(m)
for m in err_list: print(m)
print(f'\nResultado: {len(ok_list)} OK | {len(err_list)} problemas')
if not err_list:
    print('\n[SUCESSO] Sprint 1 CONCLUIDO.')
else:
    print('\n[ATENCAO] Corrija os problemas acima.')
