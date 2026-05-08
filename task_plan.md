# Task Plan — Sprint 3 | Supabase + Plataformas + Completude

## Objetivo
Transformar o sistema de local para produção:
- Banco SQLite → Supabase (PostgreSQL na nuvem)
- Vendas manuais → Polling automático 99Food + iFood
- Sistema acessível de qualquer dispositivo via URL

## Blocos de execução

### BLOCO A — Supabase (banco na nuvem)
- [ ] POP_15: Migrar schema SQLite → PostgreSQL (Supabase)
- [ ] POP_16: Migrar dados existentes
- [ ] POP_17: Adaptar backend para usar psycopg2 / supabase-py

### BLOCO B — Integração com Plataformas
- [ ] POP_18: Polling 99Food (a cada 5 min) → processar pedidos automaticamente
- [ ] POP_19: Importador XLSX 99Food via interface (fallback manual)
- [ ] POP_20: Parser iFood PDF melhorado + importação via interface

### BLOCO C — Páginas faltando
- [ ] POP_21: vendas.html — histórico + importação + lançamento manual
- [ ] POP_22: configuracoes.html — taxas, metas, dados do restaurante
- [ ] POP_23: desperdicio.html — análise semanal + metas + relatório

### BLOCO D — Relatório executivo
- [ ] POP_24: Geração de PDF semanal (reportlab)

### BLOCO E — Hospedagem
- [ ] POP_25: Deploy em Render.com ou Railway (backend Flask)
- [ ] POP_26: Frontend estático servido via Vercel ou junto ao backend

## Invariantes
- Stack adicional: psycopg2-binary, supabase-py, reportlab, schedule
- SQLite mantido como fallback offline
- Nenhuma alteração nas fichas técnicas ou motores existentes
- Design system imutável
