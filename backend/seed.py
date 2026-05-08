"""
seed.py - Popular o banco de dados com dados iniciais reais
Sistema de CMV - Quintal Goiano
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import get_connection, criar_tabelas

# ─────────────────────────────────────────────
# CATEGORIAS DE INSUMOS
# ─────────────────────────────────────────────
CATEGORIAS = [
    "Proteínas",
    "Carboidratos",
    "Laticínios e Frios",
    "Vegetais e Temperos",
    "Embalagens",
    "Bebidas",
    "Outros",
]

# ─────────────────────────────────────────────
# INSUMOS (ingredientes)
# unidade | status: PENDENTE = custo não informado ainda
# ─────────────────────────────────────────────
INSUMOS = [
    # Proteínas
    ("Costelinha suína",              "Proteínas",           "kg",  0, 0.70, "PENDENTE"),
    ("Filé de frango",                "Proteínas",           "kg",  0, 0.72, "PENDENTE"),
    ("Filé bovino",                   "Proteínas",           "kg",  0, 0.75, "PENDENTE"),
    ("Picanha",                       "Proteínas",           "kg",  0, 0.80, "PENDENTE"),
    ("Coxa de frango",                "Proteínas",           "un",  0, 1.00, "PENDENTE"),
    ("Sobrecoxa de frango",           "Proteínas",           "un",  0, 1.00, "PENDENTE"),
    ("Costela bovina desfiada",       "Proteínas",           "kg",  0, 0.65, "PENDENTE"),
    ("Rabada bovina desfiada",        "Proteínas",           "kg",  0, 0.60, "PENDENTE"),
    ("Bife acebolado",                "Proteínas",           "kg",  0, 0.75, "PENDENTE"),
    # Carboidratos e Acompanhamentos
    ("Arroz agulhinha",               "Carboidratos",        "kg",  0, 0.90, "PENDENTE"),
    ("Feijão tropeiro",               "Carboidratos",        "kg",  0, 0.90, "PENDENTE"),
    ("Mandioca",                      "Carboidratos",        "kg",  0, 0.80, "PENDENTE"),
    ("Batata frita palito",           "Carboidratos",        "kg",  0, 0.75, "PENDENTE"),
    ("Farinha de mandioca",           "Carboidratos",        "kg",  0, 1.00, "PENDENTE"),
    ("Angu de milho verde",           "Carboidratos",        "kg",  0, 0.95, "PENDENTE"),
    ("Pururuca artesanal",            "Carboidratos",        "un",  0, 1.00, "PENDENTE"),
    # Laticínios e Frios
    ("Queijo mussarela",              "Laticínios e Frios",  "kg",  0, 1.00, "PENDENTE"),
    ("Queijo coalho",                 "Laticínios e Frios",  "kg",  0, 1.00, "PENDENTE"),
    ("Queijo provolone",              "Laticínios e Frios",  "kg",  0, 1.00, "PENDENTE"),
    ("Creme de leite",                "Laticínios e Frios",  "un",  0, 1.00, "PENDENTE"),
    ("Manteiga",                      "Laticínios e Frios",  "kg",  0, 1.00, "PENDENTE"),
    ("Bacon",                         "Laticínios e Frios",  "kg",  0, 1.00, "PENDENTE"),
    ("Linguiça calabresa",            "Laticínios e Frios",  "kg",  0, 1.00, "PENDENTE"),
    ("Torresmo",                      "Laticínios e Frios",  "kg",  0, 1.00, "PENDENTE"),
    # Vegetais e Temperos
    ("Tomate",                        "Vegetais e Temperos", "kg",  0, 0.85, "PENDENTE"),
    ("Cebola",                        "Vegetais e Temperos", "kg",  0, 0.90, "PENDENTE"),
    ("Alho",                          "Vegetais e Temperos", "kg",  0, 0.90, "PENDENTE"),
    ("Pimentão",                      "Vegetais e Temperos", "kg",  0, 0.85, "PENDENTE"),
    ("Salsinha",                      "Vegetais e Temperos", "maço",0, 0.90, "PENDENTE"),
    ("Agrião",                        "Vegetais e Temperos", "maço",0, 0.85, "PENDENTE"),
    ("Jiló",                          "Vegetais e Temperos", "kg",  0, 0.85, "PENDENTE"),
    ("Pimenta bode",                  "Vegetais e Temperos", "un",  0, 1.00, "PENDENTE"),
    ("Pequi em conserva",             "Vegetais e Temperos", "kg",  0, 1.00, "PENDENTE"),
    ("Molho de tomate",               "Vegetais e Temperos", "kg",  0, 1.00, "PENDENTE"),
    ("Páprica defumada",              "Vegetais e Temperos", "kg",  0, 1.00, "PENDENTE"),
    ("Farinha de trigo",              "Vegetais e Temperos", "kg",  0, 1.00, "PENDENTE"),
    ("Farinha de rosca/panko",        "Vegetais e Temperos", "kg",  0, 1.00, "PENDENTE"),
    ("Ovo",                           "Vegetais e Temperos", "un",  0, 1.00, "PENDENTE"),  # B8: corrigido de 'dz' para 'un'
    # Embalagens
    ("Marmitex tamanho 4",            "Embalagens",          "un",  0, 1.00, "PENDENTE"),
    ("Marmitex tamanho 1",            "Embalagens",          "un",  0, 1.00, "PENDENTE"),
    ("Pote para vinagrete",           "Embalagens",          "un",  0, 1.00, "PENDENTE"),
    ("Embalagem para batata",         "Embalagens",          "un",  0, 1.00, "PENDENTE"),
    ("Caixa para bolinhos",           "Embalagens",          "un",  0, 1.00, "PENDENTE"),
    ("Sacola delivery",               "Embalagens",          "un",  0, 1.00, "PENDENTE"),
    ("Talher descartável",            "Embalagens",          "un",  0, 1.00, "PENDENTE"),
    # Bebidas
    ("Coca-Cola Lata 350ml",          "Bebidas",             "un",  0, 1.00, "PENDENTE"),
    ("Coca-Cola Zero 2L",             "Bebidas",             "un",  0, 1.00, "PENDENTE"),
    ("Coca-Cola Zero Lata 350ml",     "Bebidas",             "un",  0, 1.00, "PENDENTE"),
    ("Guaraná Antarctica Lata 350ml", "Bebidas",             "un",  0, 1.00, "PENDENTE"),
    ("Guaraná Antarctica 2L",         "Bebidas",             "un",  0, 1.00, "PENDENTE"),
    ("Guaraná Antarctica Zero 350ml", "Bebidas",             "un",  0, 1.00, "PENDENTE"),
    ("Pepsi 350ml",                   "Bebidas",             "un",  0, 1.00, "PENDENTE"),
    ("Guaraná Mineiro Lata 350ml",    "Bebidas",             "un",  0, 1.00, "PENDENTE"),
]

# ─────────────────────────────────────────────
# PRATOS DO CARDÁPIO
# ─────────────────────────────────────────────
PRATOS = [
    ("Marmita Goiana Simples",              "Marmita com 460-480g total. Arroz, feijão tropeiro, pururuca, mandioca, vinagrete e proteína à escolha.", 0, "Marmita"),
    ("Marmita Goiana Especial",             "Marmita com 520-550g total. Arroz, feijão tropeiro, pururuca, mandioca, vinagrete e proteína à escolha (porção maior).", 0, "Marmita"),
    ("Strogonoff de Frango do Quintal",     "Filé de frango selado, flambado, com molho cremoso. Acompanha arroz, batata frita e vinagrete.", 0, "Prato Principal"),
    ("Strogonoff de Carne",                 "Filé bovino selado e flambado, com páprica defumada. Acompanha arroz e batata frita.", 0, "Prato Principal"),
    ("Parmegiana do Quintal",               "Filé bovino empanado artesanalmente, molho de tomate raiz e mussarela gratinada. Com arroz, batata e vinagrete.", 0, "Prato Principal"),
    ("Costelinha do Quintal",               "Costelinha suína cozida lentamente e selada. Com mandioca, feijão tropeiro e arroz.", 0, "Prato Principal"),
    ("Frango com Pequi do Quintal",         "Coxa e sobrecoxa em cocção lenta com pequi em conserva e pimenta bode. Com arroz e angu cremoso.", 0, "Prato Principal"),
    ("Picanha do Quintal",                  "80-100g de picanha, com arroz, batata frita e vinagrete.", 0, "Prato Principal"),
    ("Feijão Tropeiro",                     "Feijão tropeiro com bacon, farinha, torresmo e calabresa.", 0, "Acompanhamento"),
    ("Batata Frita Palito",                 "Porção de batata frita palito sequinha.", 0, "Petisco"),
    ("Bolinho Caipira Raiz",                "~8 unidades (350g). Jiló, bacon e mussarela gratinada. Com molho especial da casa.", 38.0, "Petisco"),
    ("Explosão de Costela",                 "~8 unidades (350g). Costela bovina desfiada com coração de queijo derretido. Com molho especial.", 32.0, "Petisco"),
    ("Bolinhos do Cerrado - Rabada",        "~8 unidades (350g). Rabada desfiada com queijo coalho e agrião. Com molho artesanal.", 32.0, "Petisco"),
    ("Palitinho Goiano",                    "Provolone fatiado, empanado artesanalmente e frito. Com molho da casa.", 32.0, "Petisco"),
    ("Festival do Cerrado",                 "16 unidades no total (4 de cada bolinho escolhido). Custo calculado dinamicamente.", 55.0, "Petisco"),
]

# ─────────────────────────────────────────────
# FICHAS TÉCNICAS (ingrediente, qtd em gramas/unidade)
# Formato: (nome_prato, nome_insumo, quantidade, observacao)
# ─────────────────────────────────────────────
FICHAS = [
    # Marmita Goiana Simples
    ("Marmita Goiana Simples", "Arroz agulhinha",      120,  "gramas cozido"),
    ("Marmita Goiana Simples", "Feijão tropeiro",       80,  "gramas"),
    ("Marmita Goiana Simples", "Pururuca artesanal",     2,  "unidades"),
    ("Marmita Goiana Simples", "Mandioca",              80,  "gramas amanteigada"),
    ("Marmita Goiana Simples", "Tomate",                40,  "gramas (vinagrete - 100g total)"),
    ("Marmita Goiana Simples", "Bife acebolado",        90,  "gramas — média 80g-100g"),
    ("Marmita Goiana Simples", "Marmitex tamanho 4",     1,  "unidade"),
    ("Marmita Goiana Simples", "Sacola delivery",        1,  "unidade"),
    ("Marmita Goiana Simples", "Talher descartável",     1,  "unidade"),

    # Marmita Goiana Especial
    ("Marmita Goiana Especial", "Arroz agulhinha",     120,  "gramas cozido"),
    ("Marmita Goiana Especial", "Feijão tropeiro",     100,  "gramas"),
    ("Marmita Goiana Especial", "Pururuca artesanal",    3,  "unidades"),
    ("Marmita Goiana Especial", "Mandioca",            100,  "gramas amanteigada"),
    ("Marmita Goiana Especial", "Tomate",               40,  "gramas (vinagrete - 100g total)"),
    ("Marmita Goiana Especial", "Bife acebolado",      135,  "gramas — média 120g-150g"),
    ("Marmita Goiana Especial", "Marmitex tamanho 4",    1,  "unidade"),
    ("Marmita Goiana Especial", "Sacola delivery",       1,  "unidade"),
    ("Marmita Goiana Especial", "Talher descartável",    1,  "unidade"),

    # Strogonoff de Frango
    ("Strogonoff de Frango do Quintal", "Filé de frango",        210, "gramas - selado e flambado"),
    ("Strogonoff de Frango do Quintal", "Arroz agulhinha",       130, "gramas"),
    ("Strogonoff de Frango do Quintal", "Batata frita palito",   150, "gramas"),
    ("Strogonoff de Frango do Quintal", "Tomate",                 50, "gramas (vinagrete - 120g total)"),
    ("Strogonoff de Frango do Quintal", "Creme de leite",          1, "unidade (lata)"),
    ("Strogonoff de Frango do Quintal", "Marmitex tamanho 4",      1, "unidade"),
    ("Strogonoff de Frango do Quintal", "Pote para vinagrete",     1, "unidade"),
    ("Strogonoff de Frango do Quintal", "Embalagem para batata",   1, "unidade"),
    ("Strogonoff de Frango do Quintal", "Sacola delivery",         1, "unidade"),
    ("Strogonoff de Frango do Quintal", "Talher descartável",      1, "unidade"),

    # Strogonoff de Carne
    ("Strogonoff de Carne", "Filé bovino",          210, "gramas - selado e flambado"),
    ("Strogonoff de Carne", "Arroz agulhinha",      130, "gramas"),
    ("Strogonoff de Carne", "Batata frita palito",  150, "gramas"),
    ("Strogonoff de Carne", "Creme de leite",         1, "unidade (lata)"),
    ("Strogonoff de Carne", "Páprica defumada",       5, "gramas"),
    ("Strogonoff de Carne", "Marmitex tamanho 4",     1, "unidade"),
    ("Strogonoff de Carne", "Embalagem para batata",  1, "unidade"),
    ("Strogonoff de Carne", "Sacola delivery",        1, "unidade"),
    ("Strogonoff de Carne", "Talher descartável",     1, "unidade"),

    # Parmegiana do Quintal
    ("Parmegiana do Quintal", "Filé bovino",           180, "gramas para empanar"),
    ("Parmegiana do Quintal", "Arroz agulhinha",       150, "gramas"),
    ("Parmegiana do Quintal", "Batata frita palito",   120, "gramas"),
    ("Parmegiana do Quintal", "Tomate",                 40, "gramas (vinagrete - 100g total)"),
    ("Parmegiana do Quintal", "Queijo mussarela",       60, "gramas gratinado"),
    ("Parmegiana do Quintal", "Molho de tomate",       100, "gramas"),
    ("Parmegiana do Quintal", "Farinha de trigo",       30, "gramas empanamento"),
    ("Parmegiana do Quintal", "Ovo",                    1, "1 ovo para empanamento"),  # B8: corrigido
    ("Parmegiana do Quintal", "Farinha de rosca/panko", 30, "gramas empanamento"),
    ("Parmegiana do Quintal", "Marmitex tamanho 4",     1,  "unidade"),
    ("Parmegiana do Quintal", "Pote para vinagrete",    1,  "unidade"),
    ("Parmegiana do Quintal", "Embalagem para batata",  1,  "unidade"),
    ("Parmegiana do Quintal", "Sacola delivery",        1,  "unidade"),
    ("Parmegiana do Quintal", "Talher descartável",     1,  "unidade"),

    # Costelinha do Quintal
    ("Costelinha do Quintal", "Costelinha suína",     250, "gramas - cozimento longo e selagem"),
    ("Costelinha do Quintal", "Mandioca",              80, "gramas amanteigada (verificar se mantém)"),
    ("Costelinha do Quintal", "Feijão tropeiro",      100, "gramas"),
    ("Costelinha do Quintal", "Arroz agulhinha",      100, "gramas"),
    ("Costelinha do Quintal", "Marmitex tamanho 1",    1, "unidade (ficha indica tamanho 1)"),
    ("Costelinha do Quintal", "Sacola delivery",       1, "unidade"),
    ("Costelinha do Quintal", "Talher descartável",    1, "unidade"),

    # Frango com Pequi
    ("Frango com Pequi do Quintal", "Coxa de frango",         1, "unidade - cocção lenta"),
    ("Frango com Pequi do Quintal", "Sobrecoxa de frango",    1, "unidade - cocção lenta"),
    ("Frango com Pequi do Quintal", "Arroz agulhinha",      150, "gramas"),
    ("Frango com Pequi do Quintal", "Angu de milho verde",  150, "gramas - textura de purê"),
    ("Frango com Pequi do Quintal", "Pequi em conserva",    100, "gramas - PENDENTE confirmar"),
    ("Frango com Pequi do Quintal", "Pimenta bode",           2, "unidades - PENDENTE confirmar"),
    ("Frango com Pequi do Quintal", "Marmitex tamanho 4",     1, "unidade"),
    ("Frango com Pequi do Quintal", "Sacola delivery",        1, "unidade"),
    ("Frango com Pequi do Quintal", "Talher descartável",     1, "unidade"),

    # Picanha do Quintal
    ("Picanha do Quintal", "Picanha",              90, "gramas - média 80g-100g"),
    ("Picanha do Quintal", "Arroz agulhinha",     120, "gramas"),
    ("Picanha do Quintal", "Batata frita palito", 100, "gramas"),
    ("Picanha do Quintal", "Tomate",               40, "gramas (vinagrete - 100g total)"),
    ("Picanha do Quintal", "Sacola delivery",       1, "unidade"),
    ("Picanha do Quintal", "Talher descartável",    1, "unidade"),

    # Bolinhos
    ("Bolinho Caipira Raiz", "Jiló",                   120, "gramas (8 un)"),
    ("Bolinho Caipira Raiz", "Bacon",                   80, "gramas (8 un)"),
    ("Bolinho Caipira Raiz", "Queijo mussarela",        60, "gramas recheio (8 un)"),
    ("Bolinho Caipira Raiz", "Farinha de trigo",        40, "gramas empanamento"),
    ("Bolinho Caipira Raiz", "Ovo",                   2, "2 ovos para empanamento"),  # B8: corrigido
    ("Bolinho Caipira Raiz", "Farinha de rosca/panko",  40, "gramas empanamento"),
    ("Bolinho Caipira Raiz", "Caixa para bolinhos",      1, "unidade"),
    ("Bolinho Caipira Raiz", "Sacola delivery",          1, "unidade"),

    ("Explosão de Costela", "Costela bovina desfiada",  200, "gramas (8 un)"),
    ("Explosão de Costela", "Queijo mussarela",          60, "gramas coração derretido"),
    ("Explosão de Costela", "Farinha de trigo",          40, "gramas crosta fina"),
    ("Explosão de Costela", "Ovo",                     2, "2 ovos para empanamento"),  # B8: corrigido
    ("Explosão de Costela", "Farinha de rosca/panko",   40, "gramas"),
    ("Explosão de Costela", "Caixa para bolinhos",       1, "unidade"),
    ("Explosão de Costela", "Sacola delivery",           1, "unidade"),

    ("Bolinhos do Cerrado - Rabada", "Rabada bovina desfiada", 200, "gramas (8 un)"),
    ("Bolinhos do Cerrado - Rabada", "Queijo coalho",           60, "gramas cubo no centro"),
    ("Bolinhos do Cerrado - Rabada", "Agrião",                   1, "maço pequeno picadinho"),
    ("Bolinhos do Cerrado - Rabada", "Farinha de trigo",        40, "gramas"),
    ("Bolinhos do Cerrado - Rabada", "Ovo",                   2, "2 ovos para empanamento"),  # B8: corrigido
    ("Bolinhos do Cerrado - Rabada", "Farinha de rosca/panko",  40, "gramas"),
    ("Bolinhos do Cerrado - Rabada", "Caixa para bolinhos",      1, "unidade"),
    ("Bolinhos do Cerrado - Rabada", "Sacola delivery",          1, "unidade"),

    ("Palitinho Goiano", "Queijo provolone",          120, "gramas fatiado (8-10 palitos)"),
    ("Palitinho Goiano", "Farinha de trigo",           30, "gramas tempero + empanamento"),
    ("Palitinho Goiano", "Ovo",                       2, "2 ovos para empanamento"),  # B8: corrigido
    ("Palitinho Goiano", "Farinha de rosca/panko",     30, "gramas"),
    ("Palitinho Goiano", "Caixa para bolinhos",         1, "unidade"),
    ("Palitinho Goiano", "Sacola delivery",             1, "unidade"),
]

# ─────────────────────────────────────────────
# VENDAS 99FOOD (27/04 a 30/04/2026)
# ─────────────────────────────────────────────
VENDAS = [
    ("2026-04-27", "Domingo",  "99Food", 22, 519.14, 52.74, 53.89, 109.15/4,  719.00,  5, 18.87, 22, 0),
    ("2026-04-28", "Segunda",  "99Food", 27, 647.50, 54.18, 68.55, 109.15/4, 1023.00,  9, 23.28, 25, 2),
    ("2026-04-29", "Terça",    "99Food", 37, 817.20, 51.91, 86.74, 109.15/4, 1239.00, 15, 28.42, 36, 1),
    ("2026-04-30", "Quarta",   "99Food", 40, 899.40, 49.81, 93.83, 109.15/4, 1422.00,  7, 19.55, 36, 4),
]


# ─────────────────────────────────────────────
# FUNÇÕES DE SEED
# ─────────────────────────────────────────────
def seed_categorias(conn):
    for nome in CATEGORIAS:
        conn.execute(
            "INSERT OR IGNORE INTO categorias (nome) VALUES (?)", (nome,)
        )
    print(f"  [OK] {len(CATEGORIAS)} categorias inseridas.")


def seed_insumos(conn):
    for nome, cat, unidade, custo, rendimento, status in INSUMOS:
        cat_id = conn.execute(
            "SELECT id FROM categorias WHERE nome = ?", (cat,)
        ).fetchone()["id"]
        conn.execute(
            """INSERT OR IGNORE INTO insumos
               (nome, categoria_id, unidade, custo_compra, fator_rendimento, status_cadastro)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nome, cat_id, unidade, custo, rendimento, status),
        )
    print(f"  [OK] {len(INSUMOS)} insumos inseridos.")


def seed_pratos(conn):
    for nome, desc, preco, cat in PRATOS:
        conn.execute(
            """INSERT OR IGNORE INTO pratos (nome, descricao, preco_venda, categoria)
               VALUES (?, ?, ?, ?)""",
            (nome, desc, preco, cat),
        )
    print(f"  [OK] {len(PRATOS)} pratos inseridos.")


def seed_fichas(conn):
    count = 0
    for prato_nome, insumo_nome, qtd, obs in FICHAS:
        prato = conn.execute(
            "SELECT id FROM pratos WHERE nome = ?", (prato_nome,)
        ).fetchone()
        insumo = conn.execute(
            "SELECT id FROM insumos WHERE nome = ?", (insumo_nome,)
        ).fetchone()

        if not prato:
            print(f"  [WARN] Prato nao encontrado: {prato_nome}")
            continue
        if not insumo:
            print(f"  [WARN] Insumo nao encontrado: {insumo_nome}")
            continue

        conn.execute(
            """INSERT INTO fichas_tecnicas (prato_id, insumo_id, quantidade, observacao)
               VALUES (?, ?, ?, ?)""",
            (prato["id"], insumo["id"], qtd, obs),
        )
        count += 1
    print(f"  [OK] {count} itens de ficha tecnica inseridos.")


def seed_vendas(conn):
    for row in VENDAS:
        conn.execute(
            """INSERT INTO vendas
               (data, dia_semana, plataforma, pedidos, faturamento_bruto,
                ticket_medio, comissao_plataforma, taxa_pagamento,
                receita_total_plat, pedidos_atrasados, tempo_medio_preparo,
                novos_clientes, clientes_recorrentes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            row,
        )
    print(f"  [OK] {len(VENDAS)} registros de venda inseridos.")


def run():
    print("\n[SEED] Iniciando seed do banco de dados...\n")
    criar_tabelas()
    conn = get_connection()
    try:
        seed_categorias(conn)
        seed_insumos(conn)
        seed_pratos(conn)
        seed_fichas(conn)
        seed_vendas(conn)
        conn.commit()
        print("\n[OK] Seed concluido com sucesso! Banco de dados populado.\n")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO] Erro durante o seed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run()
