"""
tools/validate_correcoes.py
Valida as duas correções pós-Sprint 2.
Execute: python tools/validate_correcoes.py
"""
import sqlite3, sys, os

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'cmv.db')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

ok_l, err_l = [], []
def ck(c, m_ok, m_err):
    (ok_l if c else err_l).append(f"{'OK' if c else 'ERRO'}: {m_ok if c else m_err}")

# ─── CORREÇÃO 1: Schema da tabela perdas ───────────────────────
print("Verificando BUG-01: schema de perdas...")
if not os.path.exists(DB):
    print(f"Erro: Banco não encontrado em {DB}")
    exit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cols_list = conn.execute("PRAGMA table_info(perdas)").fetchall()
cols = {c[1]: c for c in cols_list}

ck('insumo_id' in cols and cols['insumo_id'][3] == 0,
   "perdas.insumo_id é nullable",
   "perdas.insumo_id ainda NOT NULL — executar fix_schema_perdas.py")
ck('prato_id' in cols,
   "perdas.prato_id existe",
   "perdas.prato_id não existe — executar fix_schema_perdas.py")

# Testar desperdicio por prato
from motor_baixa import registrar_desperdicio_prato
# Usar banco real mas com rollback
conn.execute("BEGIN")
try:
    # Garantir que existam dados mínimos para o teste
    # Arroz agulhinha (id=1 tipicamente) e Feijão tropeiro (id=2)
    conn.execute("UPDATE insumos SET custo_compra=4.50, estoque_atual=5.0 WHERE nome LIKE '%Arroz%'")
    conn.execute("UPDATE insumos SET custo_compra=8.00, estoque_atual=2.0 WHERE nome LIKE '%Feijão%'")
    
    prato = conn.execute("SELECT id FROM pratos WHERE nome LIKE '%Marmita%Simples%'").fetchone()
    if not prato:
        # Fallback para qualquer prato se não achar marmita
        prato = conn.execute("SELECT id FROM pratos LIMIT 1").fetchone()

    if prato:
        r = registrar_desperdicio_prato(conn, prato['id'], 1, 'sobra_producao', '2026-05-03')
        ck(r.get('ok'), f"registrar_desperdicio_prato() OK (custo R${r.get('custo_total',0):.2f})",
           f"Falhou: {r.get('erro')}")
    else:
        err_l.append("ERRO: Nenhum prato encontrado para teste de desperdício.")
except Exception as e:
    err_l.append(f"ERRO: registrar_desperdicio_prato() exception: {e}")
finally:
    conn.rollback()

# ─── CORREÇÃO 2: nfe/confirmar integra aplicar_custo_automatico ─
print("Verificando BUG-02: nfe/confirmar...")
try:
    import app
    import inspect
    src = inspect.getsource(app.confirmar_nfe)
    ck('aplicar_custo_automatico' in src,
       "nfe/confirmar chama aplicar_custo_automatico()",
       "nfe/confirmar NÃO chama aplicar_custo_automatico() — BUG-02 não corrigido")
    ck('normalizar_preco_por_unidade_insumo' in src,
       "nfe/confirmar chama normalizar_preco_por_unidade_insumo()",
       "nfe/confirmar NÃO normaliza preço — BUG-02 não corrigido")
except Exception as e:
    err_l.append(f"ERRO ao inspecionar nfe/confirmar: {e}")

conn.close()

# ─── Relatório final ────────────────────────────────────────────
print("\n" + "=" * 55)
print("VALIDAÇÃO — Correções Pós-Sprint 2")
print("=" * 55)
for m in ok_l:  print(f"  {m}")
for m in err_l: print(f"  {m}")
print(f"\n  OK: {len(ok_l)} | ERRO: {len(err_l)}")
if not err_l:
    print("\n  APROVADO — Correções aplicadas. Pronto para Sprint 3.")
else:
    print(f"\n  REPROVADO — {len(err_l)} problema(s) a corrigir.")
