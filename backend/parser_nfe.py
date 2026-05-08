"""
parser_nfe.py - Motor de leitura de Nota Fiscal Eletrônica (XML) e PDF
Sistema de CMV - Quintal Goiano
"""
import xml.etree.ElementTree as ET
import os
import re

# Namespace padrão da NF-e brasileira
NF_NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}


def parse_xml_nfe(caminho_arquivo: str) -> dict:
    """
    Lê um arquivo XML de NF-e e retorna os dados estruturados.
    Retorna dict com: fornecedor, numero_nf, data_emissao, valor_total, itens[]
    """
    try:
        tree = ET.parse(caminho_arquivo)
        root = tree.getroot()

        # Suporta XML com ou sem declaração de namespace
        ns = NF_NS if root.tag.startswith('{') else {}

        def find(node, path):
            if ns:
                path_ns = '/'.join(f'nfe:{p}' for p in path.split('/'))
                return node.find(path_ns, NF_NS)
            return node.find(path)

        def findtext(node, path, default=''):
            el = find(node, path)
            return el.text.strip() if el is not None and el.text else default

        # --- Dados do emitente (fornecedor) ---
        emit = find(root, './/emit') or find(root, './/{http://www.portalfiscal.inf.br/nfe}emit')
        fornecedor = 'Não identificado'
        cnpj_forn = ''
        if emit is not None:
            fornecedor = (
                findtext(emit, 'xFant') or
                findtext(emit, 'xNome') or
                'Não identificado'
            )
            cnpj_forn = findtext(emit, 'CNPJ')

        # --- Dados da NF ---
        ide = find(root, './/ide') or find(root, './/{http://www.portalfiscal.inf.br/nfe}ide')
        numero_nf = ''
        data_emissao = ''
        if ide is not None:
            numero_nf = findtext(ide, 'nNF')
            data_raw = findtext(ide, 'dhEmi') or findtext(ide, 'dEmi')
            data_emissao = data_raw[:10] if data_raw else ''

        # --- Total da NF ---
        total_el = find(root, './/ICMSTot') or find(root, './/{http://www.portalfiscal.inf.br/nfe}ICMSTot')
        valor_total = 0.0
        if total_el is not None:
            try:
                valor_total = float(findtext(total_el, 'vNF') or 0)
            except ValueError:
                valor_total = 0.0

        # --- Itens da NF ---
        itens = []
        det_list = root.findall('.//det', NF_NS) or root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')

        for det in det_list:
            prod = (
                det.find('nfe:prod', NF_NS) or
                det.find('{http://www.portalfiscal.inf.br/nfe}prod') or
                det.find('prod')
            )
            if prod is None:
                continue

            def pt(tag):
                el = (
                    prod.find(f'nfe:{tag}', NF_NS) or
                    prod.find(f'{{http://www.portalfiscal.inf.br/nfe}}{tag}') or
                    prod.find(tag)
                )
                return el.text.strip() if el is not None and el.text else ''

            try:
                quantidade = float(pt('qCom') or 0)
                valor_unit = float(pt('vUnCom') or 0)
                valor_total_item = float(pt('vProd') or 0)
            except ValueError:
                quantidade = 0.0
                valor_unit = 0.0
                valor_total_item = 0.0

            descricao = pt('xProd')
            unidade = pt('uCom')
            ncm = pt('NCM')

            itens.append({
                'descricao_nf': descricao,
                'unidade_nf': unidade,
                'ncm': ncm,
                'quantidade': round(quantidade, 4),
                'valor_unit': round(valor_unit, 4),
                'valor_total': round(valor_total_item, 2),
                'insumo_id': None,       # A ser vinculado via mapeamento
                'insumo_nome': None,     # A ser preenchido após match
            })

        return {
            'ok': True,
            'fornecedor': fornecedor,
            'cnpj': cnpj_forn,
            'numero_nf': numero_nf,
            'data_emissao': data_emissao,
            'valor_total': round(valor_total, 2),
            'itens': itens,
            'total_itens': len(itens),
        }

    except ET.ParseError as e:
        return {'ok': False, 'erro': f'XML inválido: {str(e)}'}
    except Exception as e:
        return {'ok': False, 'erro': f'Erro ao processar NF-e: {str(e)}'}


def tentar_match_automatico(descricao_nf: str, insumos: list) -> dict | None:
    """
    Tenta encontrar um insumo cadastrado que corresponda à descrição da NF.
    Usa correspondência por palavras-chave (case insensitive).
    Retorna o insumo com maior pontuação ou None.
    """
    descricao_lower = descricao_nf.lower()

    # Remove números e caracteres especiais para comparação mais limpa
    descricao_limpa = re.sub(r'[0-9\(\)\.\,\-\_\/]', ' ', descricao_lower)
    palavras_nf = set(w for w in descricao_limpa.split() if len(w) > 2)

    melhor = None
    melhor_score = 0

    for insumo in insumos:
        nome_lower = insumo['nome'].lower()
        nome_limpo = re.sub(r'[0-9\(\)\.\,\-\_\/]', ' ', nome_lower)
        palavras_insumo = set(w for w in nome_limpo.split() if len(w) > 2)

        if not palavras_insumo:
            continue

        intersecao = palavras_nf & palavras_insumo
        score = len(intersecao) / max(len(palavras_insumo), 1)

        if score > melhor_score and score >= 0.5:
            melhor_score = score
            melhor = {**insumo, 'score': round(score, 2)}

    return melhor
