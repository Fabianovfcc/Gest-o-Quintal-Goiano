"""
backend/motor_baixa.py — POP_08
Motor de baixa automática de estoque por venda e desperdício.
Regra central: fichas técnicas armazenam quantidades em GRAMAS para insumos em kg.
  baixa_em_kg = gramas_da_ficha / 1000
"""
import sqlite3
import json
from datetime import date
from sql_compat import q


# ──────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────

def _cfg(conn, chave, padrao):
    """Busca configuração do banco (retorna padrao se ausente)."""
    r = conn.execute(q("SELECT valor FROM configuracoes WHERE chave=?"), (chave,)).fetchone()
    return r[0] if r else padrao


def _converter_baixa(quantidade_ficha, unidade_insumo):
    """
    Converte a quantidade da ficha técnica para a unidade do insumo.
    Fichas em kg armazenam GRAMAS → dividir por 1000.
    Fichas em l  armazenam ml    → dividir por 1000.
    Demais (un, maço, g, ml, dz) já estão na unidade correta.
    """
    if unidade_insumo == 'kg':
        return quantidade_ficha / 1000.0
    if unidade_insumo == 'l':
        return quantidade_ficha / 1000.0
    return quantidade_ficha  # g, ml, un, maço, dz


def _custo_baixa(custo_compra, fator_rendimento, baixa_real):
    """Custo proporcional de uma baixa de estoque."""
    if custo_compra <= 0 or fator_rendimento <= 0:
        return 0.0
    return (custo_compra / fator_rendimento) * baixa_real


# ──────────────────────────────────────────────────────────────
# Processamento de pedidos (saída por venda)
# ──────────────────────────────────────────────────────────────

def processar_pedido(conn, prato_id, quantidade_pedida, venda_id):
    """
    Baixa todos os ingredientes de um prato × quantidade_pedida.
    Retorna dict com insumos_baixados e lista de alertas de estoque crítico.
    """
    fichas = conn.execute(q("""
        SELECT ft.id, ft.quantidade, ft.insumo_id,
               i.nome, i.unidade, i.custo_compra, i.fator_rendimento,
               i.estoque_atual, i.estoque_minimo
        FROM fichas_tecnicas ft
        JOIN insumos i ON i.id = ft.insumo_id
        WHERE ft.prato_id = ?
    """), (prato_id,)).fetchall()

    if not fichas:
        return {'ok': False, 'erro': f'Prato {prato_id} sem ficha técnica.'}

    insumos_baixados = []
    alertas = []

    for ft in fichas:
        gramas = ft['quantidade'] * quantidade_pedida
        baixa_real = _converter_baixa(gramas, ft['unidade'])
        custo_tot  = _custo_baixa(ft['custo_compra'], ft['fator_rendimento'], baixa_real)
        novo_est   = (ft['estoque_atual'] or 0) - baixa_real

        conn.execute(
            q("UPDATE insumos SET estoque_atual=?, atualizado_em=datetime('now','localtime') WHERE id=?"),
            (novo_est, ft['insumo_id'])
        )
        conn.execute(q("""
            INSERT INTO movimentacoes
              (insumo_id, tipo, quantidade, custo_unitario, custo_total,
               referencia_id, referencia_tipo)
            VALUES (?, 'saida_venda', ?, ?, ?, ?, 'venda')
        """), (ft['insumo_id'], -baixa_real, ft['custo_compra'], -custo_tot, venda_id))

        insumos_baixados.append({
            'insumo_id':  ft['insumo_id'],
            'nome':       ft['nome'],
            'unidade':    ft['unidade'],
            'baixa_real': round(baixa_real, 6),
            'custo':      round(custo_tot, 4),
            'novo_estoque': round(novo_est, 4),
        })

        minimo = ft['estoque_minimo'] or 0
        if minimo > 0 and novo_est < minimo:
            alertas.append({'insumo': ft['nome'], 'estoque': round(novo_est, 4),
                            'minimo': minimo, 'unidade': ft['unidade']})

    conn.commit()
    custo_total = sum(i['custo'] for i in insumos_baixados)
    return {'ok': True, 'insumos_baixados': insumos_baixados,
            'alertas': alertas, 'custo_total': round(custo_total, 4)}


def processar_pedido_multiplos(conn, itens, venda_id):
    """
    itens: [{prato_id, quantidade}]
    Retorna resultado consolidado de todos os pratos do pedido.
    """
    todos_baixados = []
    todos_alertas  = []
    custo_total    = 0.0

    for item in itens:
        res = processar_pedido(conn, item['prato_id'], item.get('quantidade', 1), venda_id)
        if res.get('ok'):
            todos_baixados.extend(res.get('insumos_baixados', []))
            todos_alertas.extend(res.get('alertas', []))
            custo_total += res.get('custo_total', 0)
        else:
            todos_alertas.append({'erro': res.get('erro'), 'prato_id': item['prato_id']})

    return {'ok': True, 'insumos_baixados': todos_baixados,
            'alertas': todos_alertas, 'custo_total': round(custo_total, 4)}


# ──────────────────────────────────────────────────────────────
# Registro de desperdício por insumo
# ──────────────────────────────────────────────────────────────

def registrar_desperdicio_insumo(conn, insumo_id, quantidade, motivo,
                                 data=None, responsavel=None):
    """
    Registra perda direta de um insumo (quantidade já na unidade do insumo).
    """
    data = data or date.today().isoformat()
    ins = conn.execute(
        q("SELECT nome, unidade, custo_compra, fator_rendimento, estoque_atual FROM insumos WHERE id=?"),
        (insumo_id,)
    ).fetchone()
    if not ins:
        return {'ok': False, 'erro': f'Insumo {insumo_id} não encontrado.'}

    custo_est  = _custo_baixa(ins['custo_compra'], ins['fator_rendimento'], quantidade)
    novo_est   = (ins['estoque_atual'] or 0) - quantidade

    conn.execute(
        q("UPDATE insumos SET estoque_atual=?, atualizado_em=datetime('now','localtime') WHERE id=?"),
        (novo_est, insumo_id)
    )
    conn.execute(q("""
        INSERT INTO perdas (data_perda, insumo_id, quantidade, motivo, custo_estimado, registrado_por)
        VALUES (?, ?, ?, ?, ?, ?)
    """), (data, insumo_id, quantidade, motivo, custo_est, responsavel))
    conn.execute(q("""
        INSERT INTO movimentacoes
          (insumo_id, tipo, quantidade, custo_unitario, custo_total, referencia_tipo, observacao)
        VALUES (?, 'saida_desperdicio', ?, ?, ?, 'perda', ?)
    """), (insumo_id, -quantidade, ins['custo_compra'], -custo_est, motivo))

    conn.commit()
    return {'ok': True, 'insumo_nome': ins['nome'], 'unidade': ins['unidade'],
            'custo_estimado': round(custo_est, 4), 'novo_estoque': round(novo_est, 4)}


# ──────────────────────────────────────────────────────────────
# Registro de desperdício por prato (expande via ficha técnica)
# ──────────────────────────────────────────────────────────────

def registrar_desperdicio_prato(conn, prato_id, quantidade_porcoes,
                                motivo, data=None, responsavel=None):
    """
    Expande a ficha técnica do prato e baixa cada ingrediente proporcionalmente.
    """
    data = data or date.today().isoformat()
    prato = conn.execute(q("SELECT nome FROM pratos WHERE id=?"), (prato_id,)).fetchone()
    if not prato:
        return {'ok': False, 'erro': f'Prato {prato_id} não encontrado.'}

    fichas = conn.execute(q("""
        SELECT ft.quantidade, ft.insumo_id,
               i.nome, i.unidade, i.custo_compra, i.fator_rendimento, i.estoque_atual
        FROM fichas_tecnicas ft
        JOIN insumos i ON i.id = ft.insumo_id
        WHERE ft.prato_id = ?
    """), (prato_id,)).fetchall()

    if not fichas:
        return {'ok': False, 'erro': 'Prato sem ficha técnica.'}

    ingredientes_baixados = []
    custo_total = 0.0

    for ft in fichas:
        gramas     = ft['quantidade'] * quantidade_porcoes
        baixa_real = _converter_baixa(gramas, ft['unidade'])
        custo_ing  = _custo_baixa(ft['custo_compra'], ft['fator_rendimento'], baixa_real)
        novo_est   = (ft['estoque_atual'] or 0) - baixa_real

        conn.execute(
            q("UPDATE insumos SET estoque_atual=?, atualizado_em=datetime('now','localtime') WHERE id=?"),
            (novo_est, ft['insumo_id'])
        )
        conn.execute(q("""
            INSERT INTO movimentacoes
              (insumo_id, tipo, quantidade, custo_unitario, custo_total, referencia_tipo, observacao)
            VALUES (?, 'saida_desperdicio', ?, ?, ?, 'perda', ?)
        """), (ft['insumo_id'], -baixa_real, ft['custo_compra'], -custo_ing,
              f'{motivo} – {prato["nome"]} x{quantidade_porcoes}'))

        custo_total += custo_ing
        ingredientes_baixados.append({
            'insumo_id':   ft['insumo_id'],
            'nome':        ft['nome'],
            'unidade':     ft['unidade'],
            'baixa':       round(baixa_real, 6),
            'custo':       round(custo_ing, 4),
            'novo_estoque':round(novo_est, 4),
        })

    # Registro consolidado na tabela perdas
    conn.execute(q("""
        INSERT INTO perdas (data_perda, prato_id, quantidade, motivo, custo_estimado,
                            observacao, registrado_por)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """), (data, prato_id, quantidade_porcoes, motivo,
          round(custo_total, 4),
          json.dumps({'prato_id': prato_id, 'prato_nome': prato['nome'],
                      'ingredientes': ingredientes_baixados}, ensure_ascii=False),
          responsavel))

    conn.commit()
    return {'ok': True, 'nome_prato': prato['nome'],
            'custo_total': round(custo_total, 4),
            'ingredientes_baixados': ingredientes_baixados}


# ──────────────────────────────────────────────────────────────
# Estorno de desperdício
# ──────────────────────────────────────────────────────────────

def estornar_desperdicio(conn, perda_id):
    """
    Desfaz uma perda: restaura estoque e insere movimentação de ajuste.
    """
    perda = conn.execute(q("SELECT * FROM perdas WHERE id=?"), (perda_id,)).fetchone()
    if not perda:
        return {'ok': False, 'erro': 'Perda não encontrada.'}

    restaurados = []
    # Se perda de prato, checar observacao JSON
    if perda['insumo_id'] is None:
        try:
            obs = json.loads(perda['observacao'])
            for ing in obs.get('ingredientes', []):
                conn.execute(
                    q("UPDATE insumos SET estoque_atual = estoque_atual + ? WHERE id=?"),
                    (ing['baixa'], ing['insumo_id'])
                )
                conn.execute(q("""
                    INSERT INTO movimentacoes (insumo_id, tipo, quantidade, observacao)
                    VALUES (?, 'ajuste', ?, 'estorno perda #' || ?)
                """), (ing['insumo_id'], ing['baixa'], perda_id))
                restaurados.append({'nome': ing['nome'], 'restaurado': ing['baixa']})
        except Exception:
            pass
    else:
        conn.execute(
            q("UPDATE insumos SET estoque_atual = estoque_atual + ? WHERE id=?"),
            (perda['quantidade'], perda['insumo_id'])
        )
        conn.execute(q("""
            INSERT INTO movimentacoes (insumo_id, tipo, quantidade, observacao)
            VALUES (?, 'ajuste', ?, 'estorno perda #' || ?)
        """), (perda['insumo_id'], perda['quantidade'], perda_id))
        restaurados.append({'nome': perda['insumo_id'], 'restaurado': perda['quantidade']})

    conn.execute(q("DELETE FROM perdas WHERE id=?"), (perda_id,))
    conn.commit()
    return {'ok': True, 'estorno_id': perda_id, 'restaurados': restaurados}
