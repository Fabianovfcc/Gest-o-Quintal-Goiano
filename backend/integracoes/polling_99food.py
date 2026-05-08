"""
backend/integracoes/polling_99food.py
Polling automático de pedidos da 99Food a cada 5 minutos.
Roda em thread separada quando o Flask sobe.
Ativado via POLLING_ENABLED=true no .env
"""
import os, sys, time, threading, requests
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection
from motor_baixa import processar_pedido_multiplos

API_URL  = os.getenv('FOOD99_API_URL', '')
API_KEY  = os.getenv('FOOD99_API_KEY', '')
STORE_ID = os.getenv('FOOD99_STORE_ID', '')
INTERVAL = int(os.getenv('POLLING_INTERVAL_SECONDS', 300))
ENABLED  = os.getenv('POLLING_ENABLED', 'false').lower() == 'true'

_ultimo_ts = {'valor': None}
_lock = threading.Lock()


def _headers():
    return {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}


def buscar_pedidos_novos() -> list:
    """Busca pedidos confirmados desde o último polling."""
    if not all([API_URL, API_KEY, STORE_ID]):
        return []
    params = {'store_id': STORE_ID, 'status': 'confirmed'}
    if _ultimo_ts['valor']:
        params['after'] = _ultimo_ts['valor']
    try:
        r = requests.get(f'{API_URL}/orders', headers=_headers(),
                         params=params, timeout=10)
        r.raise_for_status()
        return r.json().get('orders', [])
    except requests.RequestException as e:
        print(f"[99Food] Erro ao buscar pedidos: {e}")
        return []


def mapear_itens(pedido: dict, conn) -> list:
    """
    Mapeia itens do pedido para prato_id do sistema.
    NOTA: Adaptar os campos 'product_name' e 'quantity'
    conforme a estrutura real da API da 99Food após obter credenciais.
    """
    itens_mapeados = []
    nao_encontrados = []

    for item in pedido.get('items', []):
        nome     = item.get('product_name', '').strip()
        qtd      = int(item.get('quantity', 1))
        prato    = conn.execute(
            "SELECT id FROM pratos WHERE nome LIKE ? AND ativo = 1",
            (f'%{nome[:25]}%',)
        ).fetchone()
        if prato:
            itens_mapeados.append({'prato_id': prato['id'], 'quantidade': qtd})
        else:
            nao_encontrados.append(nome)

    if nao_encontrados:
        print(f"[99Food] Pratos não mapeados: {nao_encontrados}")

    return itens_mapeados


def processar_pedido(pedido: dict):
    """Processa 1 pedido: baixa de estoque + registro de venda."""
    pedido_id = pedido.get('id', 'sem-id')
    conn      = get_connection()

    try:
        itens = mapear_itens(pedido, conn)
        if not itens:
            print(f"[99Food] Pedido {pedido_id}: nenhum item mapeado")
            return

        hoje = datetime.now().strftime('%Y-%m-%d')
        venda = conn.execute(
            "SELECT id FROM vendas WHERE data = ? AND plataforma = '99Food'", (hoje,)
        ).fetchone()

        if not venda:
            conn.execute(
                "INSERT INTO vendas (data, plataforma, pedidos, faturamento_bruto) VALUES (?, '99Food', 0, 0)",
                (hoje,)
            )
            conn.commit()
            venda = conn.execute(
                "SELECT id FROM vendas WHERE data = ? AND plataforma = '99Food'", (hoje,)
            ).fetchone()

        resultado = processar_pedido_multiplos(conn, itens, venda_id=venda['id'])
        conn.execute("UPDATE vendas SET pedidos = pedidos + 1 WHERE id = ?", (venda['id'],))
        conn.commit()

        alertas = resultado.get('alertas_criticos', [])
        print(f"[99Food] Pedido {pedido_id}: OK | alertas: {len(alertas)}")
        for a in alertas:
            print(f"  ⚠ ESTOQUE CRÍTICO: {a.get('nome')} ({a.get('estoque_atual', 0):.3f})")

    except Exception as e:
        conn.rollback()
        print(f"[99Food] Erro pedido {pedido_id}: {e}")
    finally:
        conn.close()


def _loop():
    print(f"[99Food] Polling ativo — intervalo {INTERVAL}s")
    while True:
        try:
            with _lock:
                pedidos = buscar_pedidos_novos()
            if pedidos:
                print(f"[99Food] {len(pedidos)} pedido(s) novo(s)")
                for p in pedidos:
                    processar_pedido(p)
                _ultimo_ts['valor'] = datetime.now().isoformat()
        except Exception as e:
            print(f"[99Food] Erro no loop: {e}")
        time.sleep(INTERVAL)


def iniciar_polling():
    """Inicia polling em thread daemon. Chamar no startup do Flask."""
    if not ENABLED:
        print("[99Food] Polling desabilitado (POLLING_ENABLED=false no .env)")
        return
    if not all([API_URL, API_KEY, STORE_ID]):
        print("[99Food] Credenciais incompletas — polling não iniciado")
        print("  Configurar FOOD99_API_URL, FOOD99_API_KEY, FOOD99_STORE_ID no .env")
        return
    t = threading.Thread(target=_loop, daemon=True, name='polling-99food')
    t.start()
