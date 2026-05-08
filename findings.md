# Findings — Sprint 1 & 2

## Estado confirmado do banco (03/05/2026)
- 53 insumos | todos custo = 0 | status = PENDENTE
- 15 pratos | 10 com preco_venda = 0
- 102 itens de fichas técnicas
- 4 registros de vendas (99Food 27-30/04/2026)
- Tabelas VAZIAS: compras, itens_compra, mapa_insumos, inventario
- Tabela AUSENTE: itens_venda (existe no schema.sql mas não em database.py)

## Bugs confirmados por inspeção de código (Sprint 1)
- B1: itens_venda ausente em database.py → bloqueia CMV real e baixa de estoque
- B4: dashboard.html linha ~560: catch com setKPI hardcoded → confunde usuário
- B5: fichas.html: rota POST /api/pratos/:id/ficha existe mas sem UI
- B6: fichas.html: campo observacao não aparece na tabela
- B8: seed.py: ovo em unidade "dz" com quantidade 0.08/0.17 → cálculo incorreto

## Restrições de arquitetura (Sprint 1)
- app.py: CASE de custo só cobre 'kg' e 'un/dz/maço' — falta 'g', 'ml', 'l'
- fichas.html: carrega insumos mas NÃO retorna insumo_id em GET /api/pratos/:id/ficha
  → duplicação de prato vai quebrar sem corrigir o SELECT

## Sprint 2 — Zero Digitação Manual (Verificação Prévia)
- O motor de conversão `/1000.0` no CASE SQL (para kg) **está correto**, pois as fichas técnicas realmente armazenam as quantidades em **gramas** (ex: Arroz agulhinha = 120.0). Isso confirma que a lógica de "ficha armazena gramas e insumo é kg" foi usada e precisa ser mantida nos novos motores.
- A ferramenta `pytesseract` e `Pillow` estão instalados corretamente. Porém, para utilizar o OCR de fato na máquina do Windows, será necessário garantir a instalação do executável Tesseract nativo se for acionado. O motor de OCR deve possuir fallback para entrada manual ou XML.
- 5 novas tabelas e as configurações e fornecedores deverão ser integrados à função `criar_tabelas` (`database.py`) para dar suporte total à automação.
