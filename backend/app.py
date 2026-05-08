"""
app.py - API REST principal do sistema de CMV
Sistema de CMV - Quintal Goiano
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from auth import (
    api_key_required, jwt_required,
    gerar_token, verificar_token,
    verificar_senha_admin, aplicar_headers_seguranca,
    ALLOWED_ORIGINS, ENV
)
from db import get_connection, is_postgres, sql_now, sql_today
from sql_compat import q
from database import criar_tabelas
from seed import run as seed_db
from datetime import date
import io

app = Flask(__name__)

# ─── CORS restrito ao domínio configurado ────────────────────────────────────
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per hour", "60 per minute"],
    storage_uri="memory://",
)

# ─── Headers de segurança em toda resposta ───────────────────────────────────
@app.after_request
def security_headers(response):
    return aplicar_headers_seguranca(response)


# ─────────────────────────────────────────────
# INICIALIZAÇÃO E POLLING
# ─────────────────────────────────────────────
def _start_polling():
    """Inicia o polling de plataformas em background de forma segura."""
    try:
        from integracoes.polling_99food import iniciar_polling
        iniciar_polling()
        print("[CMV] Polling 99Food ativado")
    except Exception as e:
        print(f"[CMV] Polling não iniciado: {e}")

@app.before_request
def inicializar():
    """Garante que o banco está criado antes das requisições."""
    criar_tabelas()

# Iniciar polling na carga do app (para Gunicorn)
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    _start_polling()


# ─────────────────────────────────────────────
# ROTA: Status da API
# ─────────────────────────────────────────────
@app.route("/api/status")
def status():
    # Verificar se o polling está ativo (pela thread global)
    try:
        from integracoes.polling_99food import polling_running
        polling_active = polling_running
    except:
        polling_active = False

    return jsonify({
        "status":   "online",
        "db_mode":  "postgresql" if is_postgres() else "sqlite",
        "db_status": "connected",
        "polling_active": polling_active,
        "version":  "3.1"
    })

# ─────────────────────────────────────────────
# AUTENTICAÇÃO
# ─────────────────────────────────────────────
@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """Login com senha do admin. Retorna JWT para uso no frontend."""
    data  = request.json or {}
    senha = data.get("senha", "")

    if not verificar_senha_admin(senha):
        return jsonify({"ok": False, "erro": "Senha incorreta."}), 401

    token = gerar_token()
    resp  = jsonify({"ok": True, "token": token})
    resp.set_cookie(
        "cmv_session", token,
        httponly=True,
        secure=(ENV != "development"),
        samesite="Strict",
        max_age=43200  # 12 horas
    )
    return resp


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    resp = jsonify({"ok": True})
    resp.delete_cookie("cmv_session")
    return resp


@app.route("/api/auth/verificar", methods=["GET"])
def verificar_sessao():
    token = request.cookies.get("cmv_session", "") or \
            request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = verificar_token(token)
    if payload:
        return jsonify({"ok": True, "usuario": payload.get("sub")})
    return jsonify({"ok": False}), 401

@app.route("/api/configuracoes", methods=["GET"])
@api_key_required
def get_configuracoes():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT chave, valor, descricao FROM configuracoes").fetchall()
        return jsonify({r["chave"]: {"valor": r["valor"], "descricao": r["descricao"]} for r in rows})
    finally:
        conn.close()

@app.route("/api/configuracoes", methods=["PUT"])
@api_key_required
def salvar_configuracoes():
    data = request.get_json() or {}
    conn = get_connection()
    try:
        for chave, valor in data.items():
            conn.execute("""
                UPDATE configuracoes 
                SET valor = ?, atualizado_em = datetime('now','localtime')
                WHERE chave = ?
            """, (str(valor), chave))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/relatorio/pdf")
@api_key_required
@limiter.limit("10 per hour")
def gerar_relatorio_pdf_route():
    from relatorio import gerar_pdf_semanal
    filename = f"relatorio_{date.today().isoformat()}.pdf"
    try:
        path = gerar_pdf_semanal(filename)
        return send_file(os.path.abspath(path), as_attachment=True)
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/")
def index():
    import os as _os
    root_dir = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
    return send_file(_os.path.join(root_dir, "login.html"))

@app.route("/<path:filename>")
def serve_html(filename):
    """Serve os arquivos HTML da raiz do projeto."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    allowed = [
        "dashboard.html", "rotina.html", "notas.html", "fichas.html", 
        "insumos.html", "estoque.html", "compras.html", "vendas.html", 
        "desperdicio.html", "configuracoes.html"
    ]
    if filename in allowed:
        return send_from_directory(root_dir, filename)
    return jsonify({"erro": "Not Found"}), 404

@app.route("/api/insumos/<int:insumo_id>", methods=["PUT"])
@api_key_required
def atualizar_insumo(insumo_id):
    """Atualiza custo e estoque de um insumo."""
    data = request.get_json()
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE insumos
            SET custo_compra     = COALESCE(?, custo_compra),
                fator_rendimento = COALESCE(?, fator_rendimento),
                estoque_atual    = COALESCE(?, estoque_atual),
                estoque_minimo   = COALESCE(?, estoque_minimo, estoque_critico),
                estoque_critico  = COALESCE(?, estoque_critico),
                estoque_alerta   = COALESCE(?, estoque_alerta),
                estoque_ideal    = COALESCE(?, estoque_ideal),
                status_cadastro  = 'COMPLETO',
                atualizado_em    = datetime('now','localtime')
            WHERE id = ?
        """, (
            data.get("custo_compra"),
            data.get("fator_rendimento"),
            data.get("estoque_atual"),
            data.get("estoque_minimo") or data.get("estoque_critico"),
            data.get("estoque_critico"),
            data.get("estoque_alerta"),
            data.get("estoque_ideal"),
            insumo_id,
        ))
        conn.commit()
        return jsonify({"ok": True, "mensagem": "Insumo atualizado."})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTA: Pratos / Cardápio
# ─────────────────────────────────────────────
@app.route("/api/pratos")
@api_key_required
def listar_pratos():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT p.*,
                   COUNT(ft.id) AS total_ingredientes,
                   SUM(CASE WHEN i.status_cadastro = 'PENDENTE' THEN 1 ELSE 0 END) AS ingredientes_pendentes
            FROM pratos p
            LEFT JOIN fichas_tecnicas ft ON ft.prato_id = p.id
            LEFT JOIN insumos i ON i.id = ft.insumo_id
            GROUP BY p.id
            ORDER BY p.categoria, p.nome
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/pratos/<int:prato_id>/ficha")
@api_key_required
def ficha_tecnica(prato_id):
    """Retorna a ficha técnica completa de um prato com custo calculado."""
    conn = get_connection()
    try:
        prato = conn.execute(
            "SELECT * FROM pratos WHERE id = ?", (prato_id,)
        ).fetchone()
        if not prato:
            return jsonify({"erro": "Prato não encontrado"}), 404

        itens = conn.execute("""
            SELECT ft.id, ft.insumo_id, ft.quantidade, ft.observacao,
                   i.nome AS insumo, i.unidade, i.custo_compra,
                   i.fator_rendimento, i.status_cadastro,
                   CASE
                       WHEN i.unidade = 'kg'  AND i.custo_compra > 0
                           THEN (i.custo_compra / i.fator_rendimento) * (ft.quantidade / 1000.0)
                       WHEN i.unidade = 'g'   AND i.custo_compra > 0
                           THEN (i.custo_compra / i.fator_rendimento) * ft.quantidade
                       WHEN i.unidade = 'l'   AND i.custo_compra > 0
                           THEN (i.custo_compra / i.fator_rendimento) * (ft.quantidade / 1000.0)
                       WHEN i.unidade = 'ml'  AND i.custo_compra > 0
                           THEN (i.custo_compra / i.fator_rendimento) * ft.quantidade
                       WHEN i.unidade IN ('un','dz','maco','maço') AND i.custo_compra > 0
                           THEN (i.custo_compra / i.fator_rendimento) * ft.quantidade
                       ELSE NULL
                   END AS custo_item
            FROM fichas_tecnicas ft
            JOIN insumos i ON i.id = ft.insumo_id
            WHERE ft.prato_id = ?
        """, (prato_id,)).fetchall()

        itens_list = [dict(i) for i in itens]

        # Custo total do prato
        custo_total = None
        if all(i["custo_item"] is not None for i in itens_list):
            custo_total = round(sum(i["custo_item"] for i in itens_list), 2)

        # CMV %
        cmv_pct = None
        prato_dict = dict(prato)
        if custo_total and prato_dict["preco_venda"] > 0:
            cmv_pct = round((custo_total / prato_dict["preco_venda"]) * 100, 1)

        return jsonify({
            "prato": prato_dict,
            "ingredientes": itens_list,
            "custo_total": custo_total,
            "cmv_pct": cmv_pct,
        })
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTA: CMV por prato (ranking)
# ─────────────────────────────────────────────
@app.route("/api/cmv/ranking")
@api_key_required
def cmv_ranking():
    conn = get_connection()
    try:
        pratos = conn.execute("SELECT id, nome, preco_venda, categoria FROM pratos WHERE ativo=1").fetchall()
        resultado = []
        for p in pratos:
            itens = conn.execute("""
                SELECT
                    CASE
                        WHEN i.unidade = 'kg'  AND i.custo_compra > 0
                            THEN (i.custo_compra / i.fator_rendimento) * (ft.quantidade / 1000.0)
                        WHEN i.unidade = 'g'   AND i.custo_compra > 0
                            THEN (i.custo_compra / i.fator_rendimento) * ft.quantidade
                        WHEN i.unidade = 'l'   AND i.custo_compra > 0
                            THEN (i.custo_compra / i.fator_rendimento) * (ft.quantidade / 1000.0)
                        WHEN i.unidade = 'ml'  AND i.custo_compra > 0
                            THEN (i.custo_compra / i.fator_rendimento) * ft.quantidade
                        WHEN i.unidade IN ('un','dz','maco','maço') AND i.custo_compra > 0
                            THEN (i.custo_compra / i.fator_rendimento) * ft.quantidade
                        ELSE NULL
                    END AS custo_item
                FROM fichas_tecnicas ft
                JOIN insumos i ON i.id = ft.insumo_id
                WHERE ft.prato_id = ?
            """, (p["id"],)).fetchall()

            custos = [i["custo_item"] for i in itens if i["custo_item"] is not None]
            custo_total = round(sum(custos), 2) if custos else None
            cmv_pct = None
            if custo_total and p["preco_venda"] > 0:
                cmv_pct = round((custo_total / p["preco_venda"]) * 100, 1)

            resultado.append({
                "prato_id":    p["id"],
                "nome":        p["nome"],
                "categoria":   p["categoria"],
                "preco_venda": p["preco_venda"],
                "custo_total": custo_total,
                "cmv_pct":     cmv_pct,
                "alerta":      "vermelho" if cmv_pct and cmv_pct > 40
                               else "amarelo" if cmv_pct and cmv_pct > 35
                               else "verde" if cmv_pct
                               else "pendente",
            })
        resultado.sort(key=lambda x: (x["cmv_pct"] or 0), reverse=True)
        return jsonify(resultado)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTA: Seed (para popular o banco rapidamente)
# ─────────────────────────────────────────────
@app.route("/api/seed", methods=["POST"])
@api_key_required
def fazer_seed():
    try:
        seed_db()
        return jsonify({"ok": True, "mensagem": "Banco populado com sucesso!"})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500


# ─────────────────────────────────────────────
# ROTA: Criar novo prato (POST /api/pratos)
# ─────────────────────────────────────────────
@app.route("/api/pratos", methods=["POST"])
@api_key_required
def criar_prato():
    data = request.get_json()
    nome = (data.get("nome") or "").strip()
    if not nome:
        return jsonify({"ok": False, "erro": "Nome do prato é obrigatório."}), 400
    conn = get_connection()
    try:
        cur = conn.execute("""
            INSERT INTO pratos (nome, descricao, preco_venda, categoria, ativo)
            VALUES (?, ?, ?, ?, 1)
        """, (
            nome,
            data.get("descricao", ""),
            float(data.get("preco_venda", 0)),
            data.get("categoria", "Prato Principal"),
        ))
        conn.commit()
        prato = dict(conn.execute(
            "SELECT * FROM pratos WHERE id = ?", (cur.lastrowid,)
        ).fetchone())
        return jsonify({"ok": True, "prato": prato})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTA: Duplicar prato (POST /api/pratos/:id/duplicar)
# ─────────────────────────────────────────────
@app.route("/api/pratos/<int:prato_id>/duplicar", methods=["POST"])
@api_key_required
def duplicar_prato(prato_id):
    conn = get_connection()
    try:
        original = conn.execute("SELECT * FROM pratos WHERE id = ?", (prato_id,)).fetchone()
        if not original:
            return jsonify({"ok": False, "erro": "Prato não encontrado"}), 404
        o = dict(original)
        cur = conn.execute("""
            INSERT INTO pratos (nome, descricao, preco_venda, categoria, ativo)
            VALUES (?, ?, ?, ?, 1)
        """, (f"Cópia de {o['nome']}", o['descricao'], o['preco_venda'], o['categoria']))
        novo_id = cur.lastrowid

        itens = conn.execute(
            "SELECT insumo_id, quantidade, observacao FROM fichas_tecnicas WHERE prato_id = ?",
            (prato_id,)
        ).fetchall()
        for item in itens:
            conn.execute("""
                INSERT INTO fichas_tecnicas (prato_id, insumo_id, quantidade, observacao)
                VALUES (?, ?, ?, ?)
            """, (novo_id, item["insumo_id"], item["quantidade"], item["observacao"]))

        conn.commit()
        novo_prato = dict(conn.execute("SELECT * FROM pratos WHERE id = ?", (novo_id,)).fetchone())
        return jsonify({"ok": True, "prato": novo_prato, "itens_copiados": len(itens)})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTA: Ativar/Desativar prato
# ─────────────────────────────────────────────
@app.route("/api/pratos/<int:prato_id>/toggle-ativo", methods=["POST"])
@api_key_required
def toggle_ativo_prato(prato_id):
    conn = get_connection()
    try:
        p = conn.execute("SELECT ativo FROM pratos WHERE id = ?", (prato_id,)).fetchone()
        if not p:
            return jsonify({"ok": False, "erro": "Prato não encontrado"}), 404
        novo = 0 if p["ativo"] else 1
        conn.execute("UPDATE pratos SET ativo = ? WHERE id = ?", (novo, prato_id))
        conn.commit()
        return jsonify({"ok": True, "ativo": novo})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTAS: Insumos — ATENÇÃO À ORDEM (fixo antes de variável)
# ─────────────────────────────────────────────

# FIXO: exportar-template ANTES de <int:insumo_id>
@app.route("/api/insumos/exportar-template")
@api_key_required
def exportar_template_insumos():
    """Gera XLSX template com todos os insumos para preenchimento de custos."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from flask import send_file

    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT i.id, i.nome, c.nome AS categoria, i.unidade,
                   i.custo_compra, i.fator_rendimento, i.status_cadastro
            FROM insumos i
            LEFT JOIN categorias c ON c.id = i.categoria_id
            ORDER BY c.nome, i.nome
        """).fetchall()
    finally:
        conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Insumos - Template CMV"

    headers = ["ID", "Nome", "Categoria", "Unidade", "Custo (R$/un)", "Rendimento (0-1)", "Status Atual"]
    header_fill = PatternFill("solid", fgColor="1e293b")
    header_font = Font(color="f59e0b", bold=True)

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row_idx, r in enumerate(rows, 2):
        ws.cell(row=row_idx, column=1, value=r["id"])
        ws.cell(row=row_idx, column=2, value=r["nome"])
        ws.cell(row=row_idx, column=3, value=r["categoria"])
        ws.cell(row=row_idx, column=4, value=r["unidade"])
        custo_cell = ws.cell(row=row_idx, column=5, value=r["custo_compra"] or 0)
        custo_cell.number_format = 'R$ #,##0.00'
        ws.cell(row=row_idx, column=6, value=r["fator_rendimento"] or 1.0)
        ws.cell(row=row_idx, column=7, value=r["status_cadastro"])

    # Larguras das colunas
    for col, width in enumerate([8, 35, 22, 10, 16, 18, 14], 1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = width

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="template_insumos_cmv.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# FIXO: importar-custos ANTES de <int:insumo_id>
@app.route("/api/insumos/importar-custos", methods=["POST"])
@api_key_required
def importar_custos_insumos():
    """Recebe XLSX preenchido e retorna preview das alterações."""
    if "arquivo" not in request.files:
        return jsonify({"ok": False, "erro": "Nenhum arquivo enviado."}), 400
    arquivo = request.files["arquivo"]
    if not arquivo.filename.endswith(".xlsx"):
        return jsonify({"ok": False, "erro": "Arquivo deve ser .xlsx"}), 400

    import io
    from openpyxl import load_workbook
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        arquivo.save(tmp.name)
        wb = load_workbook(tmp.name)
    os.unlink(tmp.name)

    ws = wb.active
    preview = []
    erros = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        try:
            ins_id   = int(row[0])
            nome     = str(row[1] or "").strip()
            custo    = float(row[4] or 0)
            rend     = float(row[5] or 1.0)
            preview.append({"id": ins_id, "nome": nome, "custo": custo, "rendimento": rend})
        except (ValueError, TypeError) as e:
            erros.append(f"Linha {row}: {str(e)}")

    return jsonify({"ok": True, "preview": preview, "erros": erros, "total": len(preview)})


# FIXO: confirmar-custos ANTES de <int:insumo_id>
@app.route("/api/insumos/confirmar-custos", methods=["POST"])
@api_key_required
def confirmar_custos_insumos():
    """Aplica as atualizações de custo em lote após confirmação do preview."""
    data = request.get_json()
    atualizacoes = data.get("atualizacoes", [])
    conn = get_connection()
    try:
        count = 0
        for item in atualizacoes:
            custo = float(item.get("custo", 0))
            rend  = float(item.get("rendimento", 1.0))
            status = "COMPLETO" if custo > 0 else "PENDENTE"
            conn.execute("""
                UPDATE insumos
                SET custo_compra = ?, fator_rendimento = ?,
                    status_cadastro = ?, atualizado_em = datetime('now','localtime')
                WHERE id = ?
            """, (custo, rend, status, item["id"]))
            count += 1
        conn.commit()
        return jsonify({"ok": True, "atualizados": count})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        conn.close()


# VARIÁVEL: criar insumo
@app.route("/api/insumos", methods=["POST"])
@api_key_required
def criar_insumo():
    data = request.get_json()
    nome = (data.get("nome") or "").strip()
    if not nome:
        return jsonify({"ok": False, "erro": "Nome do insumo é obrigatório."}), 400
    conn = get_connection()
    try:
        cat = conn.execute(
            "SELECT id FROM categorias WHERE nome = ?", (data.get("categoria", "Outros"),)
        ).fetchone()
        cat_id = cat["id"] if cat else None
        cur = conn.execute("""
            INSERT INTO insumos (nome, categoria_id, unidade, custo_compra, fator_rendimento,
                                 estoque_minimo, estoque_critico, estoque_alerta, estoque_ideal, status_cadastro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome, cat_id,
            data.get("unidade", "kg"),
            float(data.get("custo_compra", 0)),
            float(data.get("fator_rendimento", 1.0)),
            float(data.get("estoque_minimo") or data.get("estoque_critico") or 0),
            float(data.get("estoque_critico", 0)),
            float(data.get("estoque_alerta", 0)),
            float(data.get("estoque_ideal", 0)),
            "COMPLETO" if float(data.get("custo_compra", 0)) > 0 else "PENDENTE",
        ))
        conn.commit()
        ins = dict(conn.execute("SELECT * FROM insumos WHERE id = ?", (cur.lastrowid,)).fetchone())
        return jsonify({"ok": True, "insumo": ins})
    finally:
        conn.close()


# VARIÁVEL: histórico de preços de um insumo — ANTES de DELETE para evitar conflito
@app.route("/api/insumos/<int:insumo_id>/historico")
@api_key_required
def historico_insumo(insumo_id):
    """Retorna histórico de preços pagos por um insumo (via compras registradas)."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT ic.valor_unit, ic.quantidade, ic.valor_total,
                   c.fornecedor, c.data_compra, c.tipo_nota
            FROM itens_compra ic
            JOIN compras c ON c.id = ic.compra_id
            WHERE ic.insumo_id = ?
            ORDER BY c.data_compra DESC
        """, (insumo_id,)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


# VARIÁVEL: deletar insumo (com guard)
@app.route("/api/insumos/<int:insumo_id>", methods=["DELETE"])
@api_key_required
def remover_insumo(insumo_id):
    conn = get_connection()
    try:
        uso = conn.execute(
            "SELECT COUNT(*) as c FROM fichas_tecnicas WHERE insumo_id = ?", (insumo_id,)
        ).fetchone()["c"]
        if uso > 0:
            return jsonify({
                "ok": False,
                "erro": f"Insumo está em uso em {uso} ficha(s) técnica(s). Remova das fichas primeiro."
            }), 409
        conn.execute("DELETE FROM insumos WHERE id = ?", (insumo_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTAS: Notas Fiscais (NF-e)
# ─────────────────────────────────────────────
import tempfile
from werkzeug.utils import secure_filename
from parser_nfe import parse_xml_nfe, tentar_match_automatico

ALLOWED_EXTENSIONS = {'xml'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/api/nfe/preview", methods=["POST"])
@api_key_required
@limiter.limit("30 per hour")
def preview_nfe():
    """
    Recebe um XML de NF-e, faz o parse e retorna os itens para o usuário
    confirmar/vincular os insumos antes de salvar.
    """
    if 'arquivo' not in request.files:
        return jsonify({"ok": False, "erro": "Nenhum arquivo enviado."}), 400

    arquivo = request.files['arquivo']
    if arquivo.filename == '' or not allowed_file(arquivo.filename):
        return jsonify({"ok": False, "erro": "Arquivo inválido. Envie um .xml de NF-e."}), 400

    # Salva temporariamente
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
        arquivo.save(tmp.name)
        resultado = parse_xml_nfe(tmp.name)
    os.unlink(tmp.name)

    if not resultado['ok']:
        return jsonify(resultado), 422

    # Tenta match automático para cada item
    conn = get_connection()
    try:
        insumos = [dict(r) for r in conn.execute(
            "SELECT id, nome, unidade, custo_compra FROM insumos ORDER BY nome"
        ).fetchall()]

        # Verifica mapa já salvo
        for item in resultado['itens']:
            mapa = conn.execute(
                "SELECT insumo_id FROM mapa_insumos WHERE descricao_nf = ?",
                (item['descricao_nf'],)
            ).fetchone()

            if mapa:
                ins = conn.execute(
                    "SELECT id, nome FROM insumos WHERE id = ?", (mapa['insumo_id'],)
                ).fetchone()
                if ins:
                    item['insumo_id'] = ins['id']
                    item['insumo_nome'] = ins['nome']
                    item['match_tipo'] = 'mapa_salvo'
            else:
                match = tentar_match_automatico(item['descricao_nf'], insumos)
                if match:
                    item['insumo_id'] = match['id']
                    item['insumo_nome'] = match['nome']
                    item['match_tipo'] = 'automatico'
                    item['match_score'] = match['score']
                else:
                    item['match_tipo'] = 'nenhum'

        resultado['insumos_disponiveis'] = insumos
        return jsonify(resultado)
    finally:
        conn.close()


@app.route("/api/nfe/confirmar", methods=["POST"])
@api_key_required
def confirmar_nfe():
    """
    Salva a compra confirmada: registra a nota, os itens,
    atualiza o preço médio dos insumos e soma ao estoque.
    """
    data = request.get_json()
    conn = get_connection()
    try:
        # Salva a compra
        cur = conn.execute("""
            INSERT INTO compras (fornecedor, numero_nf, data_compra, valor_total, tipo_nota)
            VALUES (?, ?, ?, ?, 'XML')
        """, (
            data.get('fornecedor'),
            data.get('numero_nf'),
            data.get('data_emissao'),
            data.get('valor_total', 0),
        ))
        compra_id = cur.lastrowid

        for item in data.get('itens', []):
            insumo_id = item.get('insumo_id')
            descricao_nf = item.get('descricao_nf', '')
            quantidade = float(item.get('quantidade', 0))
            valor_unit = float(item.get('valor_unit', 0))
            valor_total = float(item.get('valor_total', 0))

            conn.execute("""
                INSERT INTO itens_compra
                    (compra_id, insumo_id, descricao_nf, quantidade, valor_unit, valor_total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (compra_id, insumo_id, descricao_nf, quantidade, valor_unit, valor_total))

            if insumo_id:
                # 1. Salvar mapeamento para reconhecimento automático nas próximas NFs
                conn.execute("""
                    INSERT INTO mapa_insumos (descricao_nf, insumo_id)
                    VALUES (?, ?)
                    ON CONFLICT(descricao_nf) DO UPDATE SET insumo_id = excluded.insumo_id
                """, (descricao_nf, insumo_id))

                # 2. Normalizar preço da NF para unidade do insumo
                insumo_row = conn.execute(
                    "SELECT unidade FROM insumos WHERE id = ?", (insumo_id,)
                ).fetchone()
                unidade_insumo = insumo_row['unidade'] if insumo_row else 'kg'

                unidade_nf = item.get('unidade_nf', unidade_insumo.upper())
                norm = normalizar_preco_por_unidade_insumo(
                    valor_unit_bruto=valor_unit,
                    unidade_nf=unidade_nf,
                    quantidade_nf=quantidade,
                    valor_total=valor_total,
                    insumo_unidade=unidade_insumo,
                )
                preco_normalizado    = norm['preco_unitario_normalizado']
                quantidade_em_insumo = norm['quantidade_em_unidade_insumo']

                # 3. Buscar id do fornecedor pelo nome (se informado)
                fornecedor_nome = data.get('fornecedor', '')
                fornecedor_row  = conn.execute(
                    "SELECT id FROM fornecedores WHERE nome = ?", (fornecedor_nome,)
                ).fetchone() if fornecedor_nome else None
                fornecedor_id = fornecedor_row['id'] if fornecedor_row else None

                # 4. Aplicar custo automaticamente
                aplicar_custo_automatico(
                    conn=conn,
                    insumo_id=insumo_id,
                    preco_normalizado=preco_normalizado,
                    quantidade_estoque=quantidade_em_insumo,
                    fornecedor_id=fornecedor_id,
                    compra_id=compra_id,
                    data=data.get('data_emissao') or date.today().isoformat(),
                    descricao_nf=descricao_nf,
                )

        conn.commit()

        # Resumo para exibir ao usuário
        insumos_atualizados = [
            i.get('descricao_nf') or i.get('insumo_id')
            for i in data.get('itens', [])
            if i.get('insumo_id')
        ]
        return jsonify({
            'ok': True,
            'compra_id': compra_id,
            'resumo': {
                'insumos_atualizados': len(insumos_atualizados),
                'mensagem': f'{len(insumos_atualizados)} insumos atualizados automaticamente — custo, estoque e histórico de fornecedor registrados.',
            }
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/nfe/historico")
@api_key_required
def historico_nfe():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT c.id, c.fornecedor, c.numero_nf, c.data_compra,
                   c.valor_total, c.tipo_nota, c.importado_em,
                   COUNT(ic.id) AS total_itens
            FROM compras c
            LEFT JOIN itens_compra ic ON ic.compra_id = c.id
            GROUP BY c.id
            ORDER BY c.data_compra DESC, c.importado_em DESC
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTAS: Fichas Técnicas (edição de pratos)
# ─────────────────────────────────────────────
@app.route("/api/pratos/<int:prato_id>", methods=["PUT"])
@api_key_required
def atualizar_prato(prato_id):
    """Atualiza preço de venda e descrição de um prato."""
    data = request.get_json()
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE pratos
            SET preco_venda = COALESCE(?, preco_venda),
                descricao   = COALESCE(?, descricao)
            WHERE id = ?
        """, (data.get('preco_venda'), data.get('descricao'), prato_id))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@app.route("/api/pratos/<int:prato_id>/ficha/<int:item_id>", methods=["PUT"])
@api_key_required
def atualizar_item_ficha(prato_id, item_id):
    """Atualiza a quantidade de um ingrediente na ficha técnica."""
    data = request.get_json()
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE fichas_tecnicas
            SET quantidade = ?, observacao = ?
            WHERE id = ? AND prato_id = ?
        """, (data.get('quantidade'), data.get('observacao'), item_id, prato_id))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@app.route("/api/pratos/<int:prato_id>/ficha", methods=["POST"])
@api_key_required
def adicionar_item_ficha(prato_id):
    """Adiciona um novo ingrediente à ficha técnica de um prato."""
    data = request.get_json()
    conn = get_connection()
    try:
        cur = conn.execute("""
            INSERT INTO fichas_tecnicas (prato_id, insumo_id, quantidade, observacao)
            VALUES (?, ?, ?, ?)
        """, (prato_id, data['insumo_id'], data['quantidade'], data.get('observacao', '')))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})
    finally:
        conn.close()


@app.route("/api/fichas/<int:item_id>", methods=["DELETE"])
@api_key_required
def remover_item_ficha(item_id):
    """Remove um ingrediente da ficha técnica."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM fichas_tecnicas WHERE id = ?", (item_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ROTAS: Inventário físico
# ─────────────────────────────────────────────
@app.route("/api/inventario", methods=["GET"])
@api_key_required
def listar_inventario():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT inv.*, i.nome AS insumo_nome, i.unidade, i.estoque_atual AS estoque_teorico,
                   c.nome AS categoria_nome
            FROM inventario inv
            JOIN insumos i ON i.id = inv.insumo_id
            LEFT JOIN categorias c ON c.id = i.categoria_id
            ORDER BY inv.data_contagem DESC, i.nome
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/inventario", methods=["POST"])
@api_key_required
def salvar_inventario():
    """Salva a contagem física de múltiplos insumos de uma vez."""
    data = request.get_json()
    conn = get_connection()
    try:
        data_contagem = data.get('data_contagem')
        responsavel = data.get('responsavel', '')
        itens = data.get('itens', [])

        for item in itens:
            conn.execute("""
                INSERT INTO inventario (insumo_id, data_contagem, quantidade_real, responsavel, observacao)
                VALUES (?, ?, ?, ?, ?)
            """, (
                item['insumo_id'],
                data_contagem,
                float(item['quantidade_real']),
                responsavel,
                item.get('observacao', ''),
            ))

        conn.commit()
        return jsonify({"ok": True, "itens_salvos": len(itens)})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/inventario/comparativo")
@api_key_required
def comparativo_estoque():
    """
    Compara estoque teórico (calculado pelas vendas) vs. físico (última contagem).
    Retorna diferenças e % de desperdício estimado.
    """
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT
                i.id, i.nome, i.unidade, i.estoque_atual AS teorico,
                c.nome AS categoria,
                inv_last.quantidade_real AS fisico,
                inv_last.data_contagem,
                ROUND(i.estoque_atual - COALESCE(inv_last.quantidade_real, i.estoque_atual), 4) AS diferenca,
                CASE
                    WHEN i.estoque_atual > 0 THEN
                        ROUND(((i.estoque_atual - COALESCE(inv_last.quantidade_real, i.estoque_atual))
                               / i.estoque_atual) * 100, 1)
                    ELSE 0
                END AS pct_diferenca
            FROM insumos i
            LEFT JOIN categorias c ON c.id = i.categoria_id
            LEFT JOIN (
                SELECT insumo_id, quantidade_real, data_contagem,
                       ROW_NUMBER() OVER (PARTITION BY insumo_id ORDER BY data_contagem DESC) AS rn
                FROM inventario
            ) inv_last ON inv_last.insumo_id = i.id AND inv_last.rn = 1
            WHERE i.estoque_atual > 0
            ORDER BY pct_diferenca DESC
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()




# ═════════════════════════════════════════════════════════════
# SPRINT 2 — ROTAS DE AUTOMAÇÃO
# ═════════════════════════════════════════════════════════════

import sys
_BE = os.path.join(os.path.dirname(__file__))
if _BE not in sys.path:
    sys.path.insert(0, _BE)
from motor_baixa   import processar_pedido_multiplos, registrar_desperdicio_insumo,                           registrar_desperdicio_prato, estornar_desperdicio
from motor_compras import gerar_lista_compras, comparativo_fornecedores
from parser_ocr    import preprocessar_imagem, extrair_texto_ocr, parse_linhas_nota,                           normalizar_preco_por_unidade_insumo, aplicar_custo_automatico,                           tentar_match_automatico


# ─── Pedidos: baixa por venda ────────────────────────────────
@app.route("/api/pedidos/processar-multiplos", methods=["POST"])
@api_key_required
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
@api_key_required
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
@api_key_required
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
@api_key_required
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
@api_key_required
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
@api_key_required
@limiter.limit("20 per hour")
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

@app.route("/api/lista-compras/gerar")
@api_key_required
def gerar_lista_hoje():
    conn = get_connection()
    try:
        from datetime import date
        res = gerar_lista_compras(conn, date.today().isoformat())
        return jsonify(res)
    finally:
        conn.close()



# ─── Comparativo de fornecedores ─────────────────────────────
@app.route("/api/insumos/<int:insumo_id>/comparativo-fornecedores")
@api_key_required
def comp_fornecedores(insumo_id):
    conn = get_connection()
    try:
        return jsonify(comparativo_fornecedores(conn, insumo_id))
    finally:
        conn.close()


# ─── Fornecedores ────────────────────────────────────────────
@app.route("/api/fornecedores")
@api_key_required
def listar_fornecedores():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM fornecedores WHERE ativo=1 ORDER BY nome").fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/fornecedores", methods=["POST"])
@api_key_required
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
@api_key_required
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



@app.route("/api/rotina/perdas-hoje")
@api_key_required
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


# ─────────────────────────────────────────────
# VENDAS E DELIVERY
# ─────────────────────────────────────────────
@app.route("/api/vendas/recentes")
@api_key_required
def vendas_recentes():
    conn = get_connection()
    try:
        # SQLite: GROUP_CONCAT(p.nome, ', ') -> PostgreSQL: STRING_AGG(p.nome, ', ')
        rows = conn.execute(q(f"""
            SELECT v.id, v.data_venda, v.origem, v.valor_total,
                   (SELECT GROUP_CONCAT(p.nome, ', ') FROM itens_venda iv JOIN pratos p ON iv.prato_id = p.id WHERE iv.venda_id = v.id) as pratos_resumo
            FROM vendas_pedidos v
            WHERE date(v.data_venda) = date('now','localtime')
            ORDER BY v.data_venda DESC
            LIMIT 10
        """)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@app.route("/api/vendas/lancamento-manual", methods=["POST"])
@api_key_required
def vendas_manual():
    data = request.json
    prato_id = data.get("prato_id")
    quantidade = data.get("quantidade", 1)
    valor_total = data.get("valor_total")

    conn = get_connection()
    try:
        # 1. Registrar a venda
        cursor = conn.cursor()
        cursor.execute(q(f"""
            INSERT INTO vendas_pedidos (data_venda, origem, valor_total, status)
            VALUES ({sql_now()}, 'MANUAL', ?, 'CONCLUIDO')
        """), (valor_total,))
        
        # Obter o ID inserido
        if is_postgres():
            cursor.execute("SELECT LASTVAL()")
        else:
            cursor.execute("SELECT last_insert_rowid()")
        venda_id = cursor.fetchone()[0]

        # 2. Registrar item da venda
        cursor.execute(q(f"""
            INSERT INTO itens_venda (venda_id, prato_id, quantidade, valor_unitario)
            VALUES (?, ?, ?, ?)
        """), (venda_id, prato_id, quantidade, valor_total/quantidade))

        # 3. Abater estoque baseado na ficha técnica
        ingredientes = conn.execute(q("SELECT insumo_id, quantidade FROM fichas_tecnicas WHERE prato_id = ?"), (prato_id,)).fetchall()
        for ing in ingredientes:
            qtd_abater = ing["quantidade"] * quantidade
            conn.execute(q("""
                UPDATE insumos
                SET estoque_atual = estoque_atual - ?
                WHERE id = ?
            """), (qtd_abater, ing["insumo_id"]))

            # Registrar movimentação
            conn.execute(q(f"""
                INSERT INTO movimentacoes_estoque (insumo_id, tipo, quantidade, data_movimentacao, observacao)
                VALUES (?, 'SAIDA', ?, {sql_now()}, ?)
            """), (ing["insumo_id"], qtd_abater, f"Venda Manual #{venda_id}"))

        conn.commit()
        return jsonify({"ok": True, "venda_id": venda_id})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"ok": False, "erro": str(e)})
    finally:
        if conn: conn.close()

# ─────────────────────────────────────────────
# LISTA DE COMPRAS
# ─────────────────────────────────────────────
@app.route("/api/lista-compras/hoje")
@api_key_required
def lista_compras_hoje():
    conn = get_connection()
    try:
        rows = conn.execute(q("""
            SELECT l.id, l.insumo_id, l.quantidade_sugerida as quantidade, l.preco_estimado, l.status, l.motivo as urgencia,
                   i.nome as insumo_nome, i.unidade,
                   f.nome as fornecedor_nome,
                   i.estoque_atual / NULLIF(i.estoque_alerta, 0) as dias_restantes -- Simplificado
            FROM lista_compras l
            JOIN insumos i ON l.insumo_id = i.id
            LEFT JOIN fornecedores f ON f.id = l.fornecedor_sugerido_id
            WHERE date(l.data_lista) = date('now','localtime')
            ORDER BY CASE WHEN l.motivo = 'critica' THEN 0 ELSE 1 END, i.nome
        """)).fetchall()
        
        # Calcular custo total estimado (apenas pendentes)
        custo_total = sum(r["preco_estimado"] for r in rows if r["status"] == 'pendente')
        
        # Insumos sem histórico (opcional para o frontend)
        sem_historico = conn.execute(q("SELECT nome FROM insumos WHERE status_cadastro = 'COMPLETO' LIMIT 5")).fetchall()
        
        return jsonify({
            "itens": [dict(r) for r in rows],
            "custo_total_estimado": custo_total,
            "sem_historico": [dict(r) for r in sem_historico]
        })
    finally:
        conn.close()

@app.route("/api/lista-compras/gerar")
@api_key_required
def gerar_nova_lista():
    conn = get_connection()
    try:
        from motor_compras import gerar_lista_compras
        gerar_lista_compras(conn)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)})
    finally:
        conn.close()

@app.route("/api/lista-compras/<int:id>/status", methods=["PUT"])
@api_key_required
def atualizar_status_compra(id):
    data = request.json
    status = data.get("status")
    if status not in ['pendente', 'comprado', 'ignorado']:
        return jsonify({"ok": False, "erro": "Status inválido"}), 400
        
    conn = get_connection()
    try:
        conn.execute(q("UPDATE lista_compras SET status = ? WHERE id = ?"), (status, id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)})
    finally:
        conn.close()

# ─────────────────────────────────────────────
# ROTINA & KPIs OPERACIONAIS
# ─────────────────────────────────────────────
@app.route("/api/rotina/kpis")
@api_key_required
def rotina_kpis():
    conn = get_connection()
    try:
        # Contar insumos abaixo do nível crítico
        criticos = conn.execute(q("""
            SELECT COUNT(*) as total FROM insumos 
            WHERE estoque_critico > 0 AND estoque_atual < estoque_critico
        """)).fetchone()["total"]
        
        # Total de perdas financeiras hoje
        perdas = conn.execute(q("SELECT SUM(custo_estimado) as total FROM perdas WHERE date(data_perda) = date('now','localtime')")).fetchone()["total"] or 0
        
        return jsonify({
            "insumos_criticos": criticos,
            "perdas_financeiras_hoje": perdas
        })
    finally:
        conn.close()

# ─────────────────────────────────────────────
# DESPERDÍCIO
# ─────────────────────────────────────────────
# DESPERDÍCIO — rotas extras para desperdicio.html
# ─────────────────────────────────────────────
@app.route("/api/desperdicio/hoje")
@api_key_required
def desperdicio_hoje():
    conn = get_connection()
    try:
        rows = conn.execute(q(f"""
            SELECT p.id, p.data_perda, p.quantidade, p.motivo, p.custo_estimado,
                   COALESCE(i.nome, pr.nome) as item_nome,
                   COALESCE(i.unidade, 'un') as unidade
            FROM perdas p
            LEFT JOIN insumos i ON p.insumo_id = i.id
            LEFT JOIN pratos pr ON p.prato_id = pr.id
            WHERE date(p.data_perda) = date('now','localtime')
            ORDER BY p.data_perda DESC
        """)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/desperdicio", methods=["POST"])
@api_key_required
def registrar_desperdicio_simples():
    data = request.json or {}
    tipo       = data.get("tipo", "insumo")
    item_id    = data.get("item_id")
    quantidade = data.get("quantidade")
    motivo     = data.get("motivo", "Outros")
    obs        = data.get("observacao", "")

    if not item_id or not quantidade:
        return jsonify({"ok": False, "erro": "item_id e quantidade são obrigatórios"}), 400

    conn = get_connection()
    try:
        custo_estimado = 0
        if tipo == "insumo":
            ins = conn.execute(q("SELECT custo_compra FROM insumos WHERE id = ?"), (item_id,)).fetchone()
            custo_estimado = (ins["custo_compra"] or 0) * float(quantidade) if ins else 0
            conn.execute(q(f"""
                INSERT INTO perdas (insumo_id, quantidade, motivo, data_perda, custo_estimado, observacao)
                VALUES (?, ?, ?, {sql_now()}, ?, ?)
            """), (item_id, quantidade, motivo, custo_estimado, obs))
            conn.execute(q("UPDATE insumos SET estoque_atual = estoque_atual - ? WHERE id = ?"),
                         (quantidade, item_id))
        else:
            conn.execute(q(f"""
                INSERT INTO perdas (prato_id, quantidade, motivo, data_perda, custo_estimado, observacao)
                VALUES (?, ?, ?, {sql_now()}, 0, ?)
            """), (item_id, quantidade, motivo, obs))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"ok": False, "erro": str(e)})
    finally:
        if conn: conn.close()


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@app.route("/api/dashboard/kpis")
@api_key_required
def dashboard_kpis():
    """KPIs principais do dashboard: receita, pedidos, CMV e insumos pendentes."""
    conn = get_connection()
    try:
        # Receita total da plataforma (últimos 7 dias)
        receita = conn.execute(q("""
            SELECT COALESCE(SUM(receita_total_plat), 0) as total
            FROM vendas
            WHERE data >= date('now', '-7 days')
        """)).fetchone()["total"]

        # Total de pedidos (últimos 7 dias)
        pedidos = conn.execute(q("""
            SELECT COALESCE(SUM(pedidos), 0) as total
            FROM vendas
            WHERE data >= date('now', '-7 days')
        """)).fetchone()["total"]

        # CMV teórico médio dos pratos ativos
        cmv_row = conn.execute(q("""
            SELECT AVG(cmv_teorico) as media
            FROM pratos
            WHERE ativo = 1 AND cmv_teorico IS NOT NULL AND cmv_teorico > 0
        """)).fetchone()
        cmv_teorico = round(cmv_row["media"], 1) if cmv_row and cmv_row["media"] else None

        # Insumos sem custo cadastrado
        pendentes = conn.execute(q("""
            SELECT COUNT(*) as total FROM insumos
            WHERE custo_compra IS NULL OR custo_compra = 0
        """)).fetchone()["total"]

        return jsonify({
            "receita_plataforma": receita,
            "total_pedidos": pedidos,
            "cmv_teorico": cmv_teorico,
            "insumos_pendentes": pendentes
        })
    finally:
        conn.close()


@app.route("/api/dashboard/vendas-diarias")
@api_key_required
def dashboard_vendas_diarias():
    """Vendas dos últimos dias para o gráfico do dashboard."""
    conn = get_connection()
    try:
        rows = conn.execute(q("""
            SELECT data, dia_semana, plataforma,
                   SUM(faturamento_bruto)    as faturamento_bruto,
                   SUM(comissao_plataforma)  as comissao_plataforma,
                   SUM(receita_total_plat)   as receita_total_plat,
                   SUM(pedidos)              as pedidos
            FROM vendas
            WHERE data >= date('now', '-7 days')
            GROUP BY data, plataforma
            ORDER BY data ASC
        """)).fetchall()

        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n[CMV API] Iniciando CMV API - Quintal Goiano...")
    print("[CMV API] Acesse o dashboard em: http://localhost:8080/dashboard.html")
    print("[CMV API] API rodando em:         http://localhost:5000/api/status\n")

    # Iniciar polling de plataformas em background
    try:
        from integracoes.polling_99food import iniciar_polling
        iniciar_polling()
    except Exception as e:
        print(f"[CMV API] Polling não iniciado: {e}")

    app.run(debug=False, port=5000, host="0.0.0.0")
