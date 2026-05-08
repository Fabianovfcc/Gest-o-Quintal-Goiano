# gemini.md — Constituição do Sprint 1 & 2

## Schemas de Dados

### Schema: itens_venda
{
  id: INTEGER PK AUTOINCREMENT,
  venda_id: INTEGER FK → vendas(id) ON DELETE CASCADE,
  prato_id: INTEGER FK → pratos(id),
  quantidade: INTEGER DEFAULT 1,
  valor_unitario: REAL DEFAULT 0,
  criado_em: TEXT DEFAULT datetime('now','localtime')
}

### Schema: payload de custo por prato (saída de /api/pratos/:id/ficha)
{
  prato: { id, nome, categoria, preco_venda, descricao, ativo },
  ingredientes: [
    {
      id: INTEGER,           ← id da ficha_tecnica (para editar/deletar)
      insumo_id: INTEGER,    ← OBRIGATÓRIO para duplicação funcionar
      insumo: STRING,
      unidade: STRING,
      quantidade: REAL,
      observacao: STRING,
      custo_compra: REAL,
      fator_rendimento: REAL,
      status_cadastro: STRING,
      custo_item: REAL | NULL
    }
  ],
  custo_total: REAL | NULL,
  cmv_pct: REAL | NULL
}

### Schema: importação de custos (entrada de POST /api/insumos/importar-custos)
{
  arquivo: FILE (.xlsx),
  colunas_esperadas: [ID, Nome, Categoria, Unidade, "Custo (R$/un)", "Rendimento (0-1)", "Status Atual"]
}

### Schema: preview de importação (saída de POST /api/insumos/importar-custos)
{
  ok: BOOLEAN,
  preview: [{ id, nome, custo, rendimento }],
  erros: [STRING],
  total: INTEGER
}

### Schema: confirmação de importação (entrada de POST /api/insumos/confirmar-custos)
{
  atualizacoes: [{ id: INTEGER, custo: REAL, rendimento: REAL }]
}

## Regras Comportamentais (Invariantes)
1. CMV só é calculado quando custo_compra > 0 E preco_venda > 0 — nunca retornar valor estimado
2. status_cadastro muda para 'COMPLETO' automaticamente quando custo_compra > 0 é salvo
3. Insumo só pode ser deletado se COUNT(fichas_tecnicas WHERE insumo_id) = 0
4. Ovo: unidade = 'un', quantidade = 1 ou 2 (inteiros) — nunca frações
5. Fallback do dashboard: nunca exibir valores numéricos fixos — apenas mensagem de estado
6. Sidebar: mesma ordem em TODOS os arquivos HTML — 8 links, link "ativo" muda por página

## Fórmula de custo por insumo (CASE SQL canônico)
CASE
  WHEN unidade = 'kg'  AND custo > 0 → (custo / rendimento) * (qtd / 1000.0)
  WHEN unidade = 'g'   AND custo > 0 → (custo / rendimento) * qtd
  WHEN unidade = 'l'   AND custo > 0 → (custo / rendimento) * (qtd / 1000.0)
  WHEN unidade = 'ml'  AND custo > 0 → (custo / rendimento) * qtd
  WHEN unidade IN ('un','maço','dz') AND custo > 0 → (custo / rendimento) * qtd
  ELSE NULL
END AS custo_item

## Design System (imutável)
--bg-color: #0f172a
--surface-color: #1e293b
--surface-color-light: #334155
--primary-color: #f59e0b
--primary-glow: rgba(245,158,11,0.2)
--success-color: #10b981
--danger-color: #ef4444
--text-main: #f8fafc
--text-muted: #94a3b8
--border-color: rgba(255,255,255,0.05)
Fonte: 'Outfit' (Google Fonts)
Ícones: Lucide Icons (https://unpkg.com/lucide@latest)
API: const API = 'http://localhost:5000/api'

## Sprint 2 — Schemas adicionais

### Regra de automação de custo (CENTRAL)
Quando uma NF é confirmada:
1. Para cada item vinculado a um insumo:
   a. custo_unitario_novo = valor_unit da NF (preco por unidade de compra)
   b. Se unidade da NF for diferente da unidade do insumo → converter
      Ex: NF vem em "PCT 5KG" com valor R$45,00 → custo_kg = 45/5 = R$9,00/kg
   c. UPDATE insumos SET custo_compra = custo_unitario_novo (ultimo preco sempre)
   d. UPDATE insumos SET estoque_atual += quantidade_comprada
   e. INSERT movimentacoes tipo='entrada_compra'
   f. INSERT precos_fornecedores (historico)
2. CMV de TODOS os pratos que usam esse insumo recalcula automaticamente
   (o calculo e sempre em tempo real via SQL — nao precisa trigger)

### Regra de baixa por venda (CENTRAL)
Quando pedido e processado:
  Para cada prato × quantidade:
    Para cada ingrediente na ficha tecnica:
      baixa = ficha.quantidade × qtd_pedida
      UPDATE insumos SET estoque_atual -= baixa
      INSERT movimentacoes tipo='saida_venda'

### Regra de custo: quantidade da ficha = GRAMAS, insumo.unidade = kg
  custo_ingrediente = (custo_kg / rendimento) × (gramas / 1000)
  Isto ja esta implementado no CASE SQL — confirmar que esta correto.

### Regra de lista de compras
  consumo_diario_medio = AVG(ABS(quantidade)) FROM movimentacoes
    WHERE insumo_id = X AND tipo LIKE 'saida_%'
    AND criado_em >= hoje - dias_media_consumo
  dias_restantes = estoque_atual / consumo_diario_medio
  Se dias_restantes < dias_estoque_minimo:
    quantidade_sugerida = (consumo_diario_medio × dias_alvo_compra) - estoque_atual
    fornecedor_sugerido = MIN(preco_unitario) FROM precos_fornecedores
      WHERE insumo_id = X AND data_compra >= hoje - 30 dias

### O que NUNCA é manual
- Custo dos insumos (vem da nota fiscal)
- Atualização do estoque por venda (vem das plataformas)
- CMV dos pratos (calculado em tempo real)
- Lista de compras (gerada pelo motor)

### O que pode ser manual (único necessário)
- Vincular item novo da NF a insumo (só na primeira compra daquele item)
- Informar sobras do dia na tela de rotina
- Confirmar a lista de compras gerada

## Sprint 3 — Schemas e Regras

### Variáveis de ambiente (.env)
SUPABASE_URL=https://[ref].supabase.co
SUPABASE_KEY=[anon-key]
SUPABASE_DB_URL=postgresql://postgres:[senha]@db.[ref].supabase.co:5432/postgres
FOOD99_API_URL=https://api.99food.com.br/v1
FOOD99_API_KEY=[chave]
FOOD99_STORE_ID=[id-loja]
IFOOD_CLIENT_ID=[client-id]
IFOOD_CLIENT_SECRET=[client-secret]
POLLING_INTERVAL_SECONDS=300
POLLING_ENABLED=false
ENVIRONMENT=development

### Regra de banco dual
- ENVIRONMENT=development → SQLite (data/cmv.db)
- ENVIRONMENT=production  → PostgreSQL (SUPABASE_DB_URL)
- Detecção automática em backend/db.py
- Fallback: se Supabase indisponível → usar SQLite

### Diferenças críticas SQLite → PostgreSQL
- INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
- datetime('now','localtime')       → NOW()
- INSERT OR IGNORE INTO             → INSERT INTO ... ON CONFLICT DO NOTHING
- INSERT OR REPLACE INTO            → INSERT INTO ... ON CONFLICT(...) DO UPDATE SET
- date('now')                       → CURRENT_DATE

### Sidebar final (9 links — obrigatório em todos os HTMLs)
Dashboard | Rotina | Notas Fiscais | Fichas Técnicas | Insumos |
Estoque | Vendas | Desperdício | Configurações
