"""
tools/add_routes_sprint2.py — POP_11
Adiciona bloco de rotas Sprint 2 ao final do app.py (antes do bloco MAIN).
"""
import os

ROUTES = '''

# ═════════════════════════════════════════════════════════════
# SPRINT 2 — ROTAS DE AUTOMAÇÃO
# ═════════════════════════════════════════════════════════════

import sys
_BE = os.path.join(os.path.dirname(__file__))
if _BE not in sys.path:
    sys.path.insert(0, _BE)
from motor_baixa   import processar_pedido_multiplos, registrar_desperdicio_insumo, \
                          registrar_desperdicio_prato, estornar_desperdicio
from motor_compras import gerar_lista_compras, comparativo_fornecedores
from parser_ocr    import preprocessar_imagem, extrair_texto_ocr, parse_linhas_nota, \
                          normalizar_preco_por_unidade_insumo, aplicar_custo_automatico, \
                          tentar_match_automatico


# ─── Pedidos: baixa por venda ────────────────────────────────
@app.route("/api/pedidos/processar-multiplos", methods=["POST"])
def processar_pedidos():
    data = request.get_json() or {}
    conn = get_connection()
    try:
        itens    = data.get("itens", [])
        venda_id = data.get("venda_id", 0)
        if not itens:
            return jsonify({"ok": True, "insumos_baixados": [],
                            "alertas": [], "custo_total": 0})
        res = processar_pedido_multiplos(conn, itens, venda_id)
        return jsonify(res)
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        conn.close()


# ─── Desperdício por insumo ──────────────────────────────────
@app.route("/api/desperdicio/por-insumo", methods=["POST"])
def desperdicio_insumo():
    d = request.get_json() or {}
    conn = get_connection()
    try:
        res = registrar_desperdicio_insumo(
            conn,
            insumo_id   = d.get("insumo_id"),
            quantidade  = float(d.get("quantidade", 0)),
            motivo      = d.get("motivo", "nao_informado"),
            data        = d.get("data"),
            responsavel = d.get("responsavel"),
        )
        return jsonify(res)
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        conn.close()


# ─── Desperdício por prato ───────────────────────────────────
@app.route("/api/desperdicio/por-prato", methods=["POST"])
def desperdicio_prato():
    d = request.get_json() or {}
    conn = get_connection()
    try:
        res = registrar_desperdicio_prato(
            conn,
            prato_id          = d.get("prato_id"),
            quantidade_porcoes= float(d.get("quantidade_porcoes", 0)),
            motivo            = d.get("motivo", "nao_informado"),
            data              = d.get("data"),
            responsavel       = d.get("responsavel"),
        )
        return jsonify(res)
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        conn.close()


# ─── Estorno de desperdício ──────────────────────────────────
@app.route("/api/desperdicio/<int:perda_id>", methods=["DELETE"])
def estornar_perda(perda_id):
    conn = get_connection()
    try:
        res = estornar_desperdicio(conn, perda_id)
        return jsonify(res)
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        conn.close()


# ─── Histórico de desperdícios ───────────────────────────────
@app.route("/api/desperdicio/historico")
def historico_desperdicio():
    inicio    = request.args.get("inicio")
    fim       = request.args.get("fim")
    insumo_id = request.args.get("insumo_id")
    conn = get_connection()
    try:
        sql = """
            SELECT p.*, i.nome AS insumo_nome, pr.nome AS prato_nome
            FROM perdas p
            LEFT JOIN insumos i  ON i.id  = p.insumo_id
            LEFT JOIN pratos  pr ON pr.id = CAST(
                json_extract(p.observacao,'$.prato_id') AS INTEGER)
            WHERE 1=1
        """
        params = []
        if inicio:
            sql += " AND p.data_perda >= ?"; params.append(inicio)
        if fim:
            sql += " AND p.data_perda <= ?"; params.append(fim)
        if insumo_id:
            sql += " AND p.insumo_id = ?"; params.append(insumo_id)
        sql += " ORDER BY p.criado_em DESC"
        rows = conn.execute(sql, params).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


# ─── OCR de foto de nota ─────────────────────────────────────
@app.route("/api/ocr/nota", methods=["POST"])
def ocr_nota():
    if "arquivo" not in request.files:
        return jsonify({"ok": False, "erro": "Campo 'arquivo' ausente."}), 400
    arq          = request.files["arquivo"]
    forn_nome    = request.form.get("fornecedor_nome", "")
    tmp_dir      = os.path.join(os.path.dirname(__file__), "..", ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path     = os.path.join(tmp_dir, arq.filename or "nota.jpg")
    arq.save(tmp_path)

    try:
        proc  = preprocessar_imagem(tmp_path)
        texto = extrair_texto_ocr(proc)
        if not texto or len(texto.strip()) < 20:
            return jsonify({
                "ok": False, "erro": "ocr_indisponivel",
                "sugestao": "usar_xml_ou_manual",
                "detalhe": "Tesseract não instalado ou imagem ilegível."
            }), 422

        itens = parse_linhas_nota(texto)
        conn  = get_connection()
        try:
            for item in itens:
                match = tentar_match_automatico(conn, item["descricao_nf"])
                if match:
                    item.update(match)
        finally:
            conn.close()

        nao_identificados = [i for i in itens if not i.get("insumo_id")]
        return jsonify({
            "ok": True, "itens": itens,
            "nao_identificados": nao_identificados,
            "fornecedor_detectado": forn_nome or None,
            "total": len(itens),
        })
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500


# ─── Lista de compras ─────────────────────────────────────────
@app.route("/api/lista-compras/hoje")
def lista_compras_hoje():
    conn = get_connection()
    try:
        from datetime import date
        hoje = date.today().isoformat()
        # Buscar lista já gerada hoje
        rows = conn.execute("""
            SELECT lc.*, i.nome AS insumo_nome, i.unidade,
                   f.nome AS fornecedor_nome, f.id AS fornecedor_id
            FROM lista_compras lc
            JOIN insumos i ON i.id = lc.insumo_id
            LEFT JOIN fornecedores f ON f.id = lc.fornecedor_sugerido_id
            WHERE lc.data_lista = ?
            ORDER BY lc.dias_restantes ASC
        """, (hoje,)).fetchall()

        if not rows:
            # Gerar automaticamente se não existe
            res = gerar_lista_compras(conn, hoje)
            return jsonify({**res, "gerado_agora": True})

        itens = [dict(r) for r in rows]
        total = sum(i.get("preco_estimado", 0) for i in itens if i.get("status") == "pendente")
        return jsonify({
            "data_lista": hoje, "total_itens": len(itens),
            "custo_total_estimado": round(total, 2),
            "itens": itens, "gerado_agora": False,
        })
    finally:
        conn.close()


@app.route("/api/lista-compras/gerar")
def gerar_lista_hoje():
    conn = get_connection()
    try:
        from datetime import date
        res = gerar_lista_compras(conn, date.today().isoformat())
        return jsonify(res)
    finally:
        conn.close()


@app.route("/api/lista-compras/<int:item_id>/status", methods=["PUT"])
def atualizar_status_lista(item_id):
    d      = request.get_json() or {}
    status = d.get("status", "pendente")
    if status not in ("pendente", "comprado", "ignorado"):
        return jsonify({"ok": False, "erro": "Status inválido."}), 400
    conn = get_connection()
    try:
        conn.execute("UPDATE lista_compras SET status=? WHERE id=?", (status, item_id))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


# ─── Comparativo de fornecedores ─────────────────────────────
@app.route("/api/insumos/<int:insumo_id>/comparativo-fornecedores")
def comp_fornecedores(insumo_id):
    conn = get_connection()
    try:
        return jsonify(comparativo_fornecedores(conn, insumo_id))
    finally:
        conn.close()


# ─── Fornecedores ────────────────────────────────────────────
@app.route("/api/fornecedores")
def listar_fornecedores():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM fornecedores WHERE ativo=1 ORDER BY nome").fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/fornecedores", methods=["POST"])
def criar_fornecedor():
    d    = request.get_json() or {}
    nome = (d.get("nome") or "").strip()
    if not nome:
        return jsonify({"ok": False, "erro": "Nome obrigatório."}), 400
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO fornecedores (nome, cnpj, tipo) VALUES (?,?,?)",
            (nome, d.get("cnpj",""), d.get("tipo","supermercado"))
        )
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid, "nome": nome})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 409
    finally:
        conn.close()


@app.route("/api/fornecedores/<int:fid>", methods=["PUT"])
def atualizar_fornecedor(fid):
    d    = request.get_json() or {}
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE fornecedores SET nome=?, cnpj=?, tipo=?, ativo=? WHERE id=?
        """, (d.get("nome"), d.get("cnpj",""), d.get("tipo","supermercado"),
              int(d.get("ativo", 1)), fid))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


# ─── KPIs da rotina diária ───────────────────────────────────
@app.route("/api/rotina/kpis")
def rotina_kpis():
    conn = get_connection()
    try:
        hoje = request.args.get("data") or "date('now','localtime')"
        if hoje == "date('now','localtime')":
            data_sql = "date('now','localtime')"
        else:
            data_sql = f"'{hoje}'"

        pedidos = conn.execute(
            f"SELECT COUNT(*) FROM vendas WHERE date(data_venda)={data_sql}"
        ).fetchone()[0]
        faturamento = conn.execute(
            f"SELECT COALESCE(SUM(faturamento_bruto),0) FROM vendas WHERE date(data_venda)={data_sql}"
        ).fetchone()[0]
        custo_saida = conn.execute(
            f"""SELECT COALESCE(SUM(ABS(custo_total)),0) FROM movimentacoes
                WHERE tipo LIKE 'saida_%'
                  AND date(criado_em) = {data_sql}"""
        ).fetchone()[0]
        desperdicio = conn.execute(
            f"""SELECT COALESCE(SUM(custo_estimado),0) FROM perdas
                WHERE date(data_perda) = {data_sql}"""
        ).fetchone()[0]
        criticos = conn.execute(
            """SELECT COUNT(*) FROM insumos
               WHERE estoque_minimo > 0 AND estoque_atual < estoque_minimo"""
        ).fetchone()[0]

        cmv_pct = round(custo_saida / faturamento * 100, 1) if faturamento > 0 else None
        return jsonify({
            "pedidos_hoje":       pedidos,
            "faturamento_hoje":   round(faturamento, 2),
            "custo_saida_hoje":   round(custo_saida, 2),
            "desperdicio_hoje":   round(desperdicio, 2),
            "cmv_hoje":           cmv_pct,
            "insumos_criticos":   criticos,
        })
    finally:
        conn.close()


@app.route("/api/rotina/perdas-hoje")
def perdas_hoje():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT p.*, i.nome AS insumo_nome
            FROM perdas p
            LEFT JOIN insumos i ON i.id = p.insumo_id
            WHERE date(p.data_perda) = date('now','localtime')
            ORDER BY p.criado_em DESC
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

'''

app_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app.py')
with open(app_path, encoding='utf-8') as f:
    content = f.read()

MAIN_MARKER = '''# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":'''

if MAIN_MARKER not in content:
    print('ERRO: marcador MAIN nao encontrado em app.py')
    exit(1)

# Verificar se rotas já existentes
if '/api/pedidos/processar-multiplos' in content:
    print('INFO: Rotas Sprint 2 ja existem em app.py — abortando.')
    exit(0)

new_content = content.replace(MAIN_MARKER, ROUTES + '\n' + MAIN_MARKER)
with open(app_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print(f'OK: {len(ROUTES.splitlines())} linhas de rotas Sprint 2 adicionadas ao app.py')
