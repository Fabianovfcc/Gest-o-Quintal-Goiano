"""
backend/motor_compras.py — POP_10
Geração automática da lista de compras do dia.
Usa consumo médio real de movimentacoes + estoque atual de cada insumo.
"""
import sqlite3
from datetime import date


def _cfg(conn, chave, padrao):
    r = conn.execute("SELECT valor FROM configuracoes WHERE chave=?", (chave,)).fetchone()
    return float(r[0]) if r else padrao


def gerar_lista_compras(conn, data_alvo=None):
    """
    Gera a lista de compras para data_alvo (padrão: hoje).
    Algoritmo:
      1. Para cada insumo com consumo registrado em movimentacoes:
         a. Calcula consumo_diario_medio (últimos X dias)
         b. Calcula dias_restantes = estoque_atual / consumo_diario
         c. Se dias_restantes < dias_estoque_minimo → entra na lista
      2. Sugere fornecedor de menor preço (últimos 30 dias)
      3. INSERT OR REPLACE na lista_compras
    """
    data_alvo = data_alvo or date.today().isoformat()
    dias_min  = _cfg(conn, 'dias_estoque_minimo', 2)
    dias_med  = int(_cfg(conn, 'dias_media_consumo', 7))
    dias_alvo = _cfg(conn, 'dias_alvo_compra', 3)

    # Consumo médio diário por insumo
    consumos = conn.execute("""
        SELECT insumo_id,
               ABS(AVG(quantidade)) AS consumo_diario
        FROM movimentacoes
        WHERE tipo IN ('saida_venda','saida_desperdicio')
          AND criado_em >= date('now','localtime', ? || ' days')
        GROUP BY insumo_id
    """, (f'-{dias_med}',)).fetchall()

    itens_lista   = []
    sem_historico = []
    custo_total   = 0.0

    for c in consumos:
        ins_id  = c['insumo_id']
        c_dia   = c['consumo_diario'] or 0
        if c_dia <= 0:
            continue
 
        ins = conn.execute(
            "SELECT nome, unidade, estoque_atual, estoque_critico, estoque_alerta, estoque_ideal FROM insumos WHERE id=?",
            (ins_id,)
        ).fetchone()
        if not ins:
            continue

        est  = ins['estoque_atual'] or 0
        crit = ins['estoque_critico'] or 0
        alrt = ins['estoque_alerta'] or 0
        idat = ins['estoque_ideal'] or 0
        
        dias_rest = est / c_dia if c_dia > 0 else 9999

        # Gatilho: Se estoque < alerta OU se estoque < critico (sempre alerta > critico idealmente)
        # Se os níveis estiverem zerados, cai no fallback de dias
        if alrt > 0:
            if est >= alrt: continue
            qtd_sug = max(0.0, idat - est)
            motivo = f"Estoque ({est:.1f}) abaixo do nível de ALERTA ({alrt:.1f})"
            if crit > 0 and est < crit:
                motivo = f"CRÍTICO: Estoque ({est:.1f}) abaixo do NÍVEL CRÍTICO ({crit:.1f})!"
        else:
            # Fallback para o modo antigo de dias se os níveis manuais não estiverem configurados
            if dias_rest >= dias_min:
                continue
            qtd_sug = max(0.0, (c_dia * dias_alvo) - est)
            motivo = f"Estoque para {dias_rest:.1f} dia(s) — precisa de {dias_alvo} dias"

        if qtd_sug <= 0:
            qtd_sug = c_dia * dias_alvo

        # Melhor fornecedor (menor preço nos últimos 30 dias)
        forn = conn.execute("""
            SELECT pf.fornecedor_id, f.nome AS forn_nome, pf.preco_unitario
            FROM precos_fornecedores pf
            JOIN fornecedores f ON f.id = pf.fornecedor_id
            WHERE pf.insumo_id = ?
              AND pf.data_compra >= date('now','localtime','-30 days')
            ORDER BY pf.preco_unitario ASC, pf.data_compra DESC
            LIMIT 1
        """, (ins_id,)).fetchone()

        forn_id   = forn['fornecedor_id'] if forn else None
        forn_nome = forn['forn_nome']     if forn else None
        preco_est = round((forn['preco_unitario'] if forn else 0) * qtd_sug, 2)

        urgencia = 'critica' if (crit > 0 and est < crit) else 'alerta'

        # Upsert na lista_compras
        conn.execute("""
            INSERT OR REPLACE INTO lista_compras
              (data_geracao, insumo_id, quantidade, preco_estimado, status, urgencia)
            VALUES (?, ?, ?, ?, 'pendente', ?)
        """, (data_alvo, ins_id, round(qtd_sug, 3), preco_est, urgencia))

        custo_total += preco_est
        itens_lista.append({
            'insumo_id':     ins_id,
            'insumo_nome':   ins['nome'],
            'quantidade':    round(qtd_sug, 3),
            'unidade':       ins['unidade'],
            'preco_estimado': preco_est,
            'dias_restantes': round(dias_rest, 2),
            'urgencia':      urgencia
        })

    # Insumos com estoque mínimo mas sem histórico de consumo (não entram no cálculo automático)
    sem = conn.execute("""
        SELECT i.id, i.nome, i.estoque_alerta, i.estoque_minimo 
        FROM insumos i
        WHERE NOT EXISTS (
            SELECT 1 FROM movimentacoes m
            WHERE m.insumo_id = i.id AND m.tipo LIKE 'saida_%'
        )
        AND (i.estoque_alerta > 0 OR i.estoque_minimo > 0)
    """).fetchall()
    sem_historico = [{'insumo_id': r['id'], 'nome': r['nome']} for r in sem]

    conn.commit()
    return {
        'data_lista':          data_alvo,
        'total_itens':         len(itens_lista),
        'custo_total_estimado':round(custo_total, 2),
        'itens':               itens_lista,
        'sem_historico':       sem_historico,
    }


def comparativo_fornecedores(conn, insumo_id):
    """
    Retorna todos os fornecedores com preço registrado nos últimos 30 dias,
    ordenados por preço unitário (mais barato primeiro).
    """
    rows = conn.execute("""
        SELECT f.nome AS fornecedor, pf.preco_unitario, pf.data_compra, pf.quantidade_nota
        FROM precos_fornecedores pf
        JOIN fornecedores f ON f.id = pf.fornecedor_id
        WHERE pf.insumo_id = ?
          AND pf.data_compra >= date('now','localtime','-30 days')
        ORDER BY pf.data_compra DESC
    """, (insumo_id,)).fetchall()

    # Agrupar por fornecedor, manter o último preço de cada
    seen, lista = set(), []
    for r in rows:
        if r['fornecedor'] not in seen:
            seen.add(r['fornecedor'])
            lista.append(dict(r))

    lista.sort(key=lambda x: x['preco_unitario'])

    if len(lista) >= 2:
        delta = round((lista[-1]['preco_unitario'] / lista[0]['preco_unitario'] - 1) * 100, 1)
    else:
        delta = 0.0

    return {'insumo_id': insumo_id, 'fornecedores': lista,
            'economia_potencial_pct': delta}
