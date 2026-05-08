"""
backend/parser_ocr.py — POP_09
Extração de itens de notas fiscais (foto ou texto) e normalização de preços.
Fluxo: imagem → OCR → parse_linhas → normalizar → aplicar_custo_automatico
"""
import re
import os
import sqlite3
from datetime import date

# ──────────────────────────────────────────────────────────────
# Pré-processamento de imagem
# ──────────────────────────────────────────────────────────────

def preprocessar_imagem(caminho):
    """Melhora contraste/nitidez da imagem para OCR mais preciso."""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError:
        return caminho  # sem Pillow, usa original

    img = Image.open(caminho).convert('L')  # escala de cinza
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = img.filter(ImageFilter.SHARPEN)
    # garantir largura mínima de 1200px
    if img.width < 1200:
        ratio = 1200 / img.width
        img = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)

    tmp_dir = os.path.join(os.path.dirname(__file__), '..', '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    dest = os.path.join(tmp_dir, 'ocr_proc_' + os.path.basename(caminho) + '.png')
    img.save(dest)
    return dest


def extrair_texto_ocr(caminho_processado, lang='por'):
    """Extrai texto via Tesseract. Retorna None se indisponível."""
    try:
        import pytesseract
        return pytesseract.image_to_string(caminho_processado, lang=lang)
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# Parser de linhas de nota fiscal
# ──────────────────────────────────────────────────────────────

# Padrão: captura descrição, quantidade, unidade e valor total/unitário
_PATTERNS = [
    # "2,000 KG FILÉ FRANGO SEARA R$ 57,80"  ou  "2.000 KG ... 57,80"
    re.compile(
        r'(?P<qtd>[\d]+[,.][\d]+|[\d]+)\s*'
        r'(?P<un>KG|GR|G|UN|PCT|CX|LT|ML|SC|FD|MACO)\s+'
        r'(?P<desc>[A-Z][A-Z0-9 \/\-\.]+?)\s+'
        r'(?:R\$\s*)?(?P<val>[\d]+[,.][\d]{2})',
        re.IGNORECASE
    ),
    # "FILÉ FRANGO 2KG 57,80"
    re.compile(
        r'(?P<desc>[A-Z][A-Z0-9 \/\-\.]{3,}?)\s+'
        r'(?P<qtd>[\d]+[,.]?[\d]*)\s*'
        r'(?P<un>KG|GR|G|UN|PCT|CX|LT|ML|SC|FD)\s+'
        r'(?:R\$\s*)?(?P<val>[\d]+[,.][\d]{2})',
        re.IGNORECASE
    ),
]

def _parse_num(s):
    """Converte string numérica brasileira para float."""
    return float(s.replace('.', '').replace(',', '.'))

def parse_linhas_nota(texto):
    """
    Extrai lista de itens de uma nota fiscal a partir do texto OCR.
    Retorna [{ descricao_nf, quantidade_bruta, unidade_nf, valor_total,
               valor_unit_bruto, insumo_id, match_tipo }]
    """
    if not texto:
        return []

    itens = []
    for linha in texto.upper().splitlines():
        linha = linha.strip()
        if len(linha) < 10:
            continue
        for pat in _PATTERNS:
            m = pat.search(linha)
            if m:
                qtd = _parse_num(m.group('qtd'))
                val = _parse_num(m.group('val'))
                unit_bruto = val / qtd if qtd > 0 else val
                itens.append({
                    'descricao_nf':    m.group('desc').strip().title(),
                    'quantidade_bruta': qtd,
                    'unidade_nf':      m.group('un').upper(),
                    'valor_total':     round(val, 2),
                    'valor_unit_bruto': round(unit_bruto, 4),
                    'insumo_id':       None,
                    'match_tipo':      'nenhum',
                })
                break
    return itens


# ──────────────────────────────────────────────────────────────
# Normalização de preço por unidade do insumo (CORAÇÃO da automação)
# ──────────────────────────────────────────────────────────────

# Mapa: (unidade_NF, unidade_insumo) → lambda(valor_unit_bruto, qtd_nf, val_total)
_CONV = {
    ('KG',  'kg'):  lambda u, q, v: (u,           q),       # 1:1
    ('GR',  'kg'):  lambda u, q, v: (u * 1000,     q/1000), # gr→kg
    ('G',   'kg'):  lambda u, q, v: (u * 1000,     q/1000),
    ('UN',  'un'):  lambda u, q, v: (u,             q),
    ('CX',  'un'):  lambda u, q, v: (v / q,         q),      # preço unitário = total/cx
    ('PCT', 'kg'):  lambda u, q, v: (v / q,         q),      # preço/kg = total/kg
    ('PCT', 'un'):  lambda u, q, v: (v / q,         q),
    ('LT',  'l'):   lambda u, q, v: (u,             q),
    ('ML',  'l'):   lambda u, q, v: (u * 1000,      q/1000),
    ('SC',  'kg'):  lambda u, q, v: (v / q,         q),      # saco
    ('FD',  'un'):  lambda u, q, v: (v / q,         q),      # fardo
    ('MACO','maço'): lambda u, q, v: (u,            q),
}

def normalizar_preco_por_unidade_insumo(valor_unit_bruto, unidade_nf,
                                         quantidade_nf, valor_total,
                                         insumo_unidade):
    """
    Converte o preço da NF para o preço por unidade do insumo.
    Retorna { preco_unitario_normalizado, quantidade_em_unidade_insumo, conversao_aplicada }
    """
    key = (unidade_nf.upper(), insumo_unidade.lower())
    if key in _CONV:
        fn = _CONV[key]
        preco, qtd_conv = fn(valor_unit_bruto, quantidade_nf, valor_total)
        return {
            'preco_unitario_normalizado':   round(preco, 4),
            'quantidade_em_unidade_insumo': round(qtd_conv, 4),
            'conversao_aplicada':           f'{unidade_nf}→{insumo_unidade}',
        }
    # fallback: assumir 1:1
    return {
        'preco_unitario_normalizado':   round(valor_unit_bruto, 4),
        'quantidade_em_unidade_insumo': round(quantidade_nf, 4),
        'conversao_aplicada':           f'{unidade_nf}→{insumo_unidade} (fallback 1:1)',
    }


# ──────────────────────────────────────────────────────────────
# Aplicação automática de custo após confirmação
# ──────────────────────────────────────────────────────────────

def aplicar_custo_automatico(conn, insumo_id, preco_normalizado,
                              quantidade_estoque, fornecedor_id,
                              compra_id, data, descricao_nf=None):
    """
    Atualiza custo_compra, estoque, movimentacoes, precos_fornecedores e mapa_insumos.
    Chamar APENAS após confirmação do usuário.
    """
    data = data or date.today().isoformat()

    # 1. Atualizar insumo
    conn.execute("""
        UPDATE insumos
        SET custo_compra    = ?,
            estoque_atual   = estoque_atual + ?,
            status_cadastro = 'COMPLETO',
            atualizado_em   = datetime('now','localtime')
        WHERE id = ?
    """, (preco_normalizado, quantidade_estoque, insumo_id))

    # 2. Movimentação de entrada
    custo_total = round(preco_normalizado * quantidade_estoque, 4)
    conn.execute("""
        INSERT INTO movimentacoes
          (insumo_id, tipo, quantidade, custo_unitario, custo_total,
           referencia_id, referencia_tipo, observacao)
        VALUES (?, 'entrada_compra', ?, ?, ?, ?, 'compra', ?)
    """, (insumo_id, quantidade_estoque, preco_normalizado, custo_total,
          compra_id, descricao_nf or ''))

    # 3. Histórico de preço por fornecedor
    if fornecedor_id:
        conn.execute("""
            INSERT INTO precos_fornecedores
              (insumo_id, fornecedor_id, preco_unitario, quantidade_nota, data_compra, compra_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (insumo_id, fornecedor_id, preco_normalizado, quantidade_estoque, data, compra_id))

    # 4. Atualizar mapa_insumos (aprendizado de vínculo)
    if descricao_nf:
        conn.execute("""
            INSERT OR REPLACE INTO mapa_insumos (descricao_nf, insumo_id)
            VALUES (?, ?)
        """, (descricao_nf.upper().strip(), insumo_id))

    conn.commit()
    return {'ok': True, 'insumo_id': insumo_id, 'custo_novo': preco_normalizado,
            'estoque_adicionado': quantidade_estoque}


# ──────────────────────────────────────────────────────────────
# Match automático via mapa_insumos
# ──────────────────────────────────────────────────────────────

def tentar_match_automatico(conn, descricao_nf):
    """Busca vínculo já aprendido no mapa_insumos."""
    r = conn.execute("""
        SELECT mi.insumo_id, i.nome, i.unidade
        FROM mapa_insumos mi
        JOIN insumos i ON i.id = mi.insumo_id
        WHERE UPPER(mi.descricao_nf) = UPPER(?)
    """, (descricao_nf.strip(),)).fetchone()
    if r:
        return {'insumo_id': r['insumo_id'], 'nome': r['nome'],
                'unidade': r['unidade'], 'match_tipo': 'exato'}

    # Busca parcial (LIKE)
    r2 = conn.execute("""
        SELECT mi.insumo_id, i.nome, i.unidade
        FROM mapa_insumos mi
        JOIN insumos i ON i.id = mi.insumo_id
        WHERE UPPER(?) LIKE '%' || UPPER(SUBSTR(mi.descricao_nf,1,10)) || '%'
        LIMIT 1
    """, (descricao_nf.strip(),)).fetchone()
    if r2:
        return {'insumo_id': r2['insumo_id'], 'nome': r2['nome'],
                'unidade': r2['unidade'], 'match_tipo': 'parcial'}

    return None
