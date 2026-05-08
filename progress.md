## Sprint 3 — Continuação (04/05/2026)

### Já concluído (não tocar)
- [x] backend/db.py: conexão dual SQLite/PostgreSQL
- [x] backend/sql_compat.py: adaptador de queries
- [x] backend/integracoes/polling_99food.py: motor de polling
- [x] app.py: importa db.py em todas as rotas
- [x] data/supabase_schema.sql: schema PostgreSQL
- [x] tools/migrar_para_supabase.py
- [x] requirements.txt: 12 dependências

### A executar agora
- [ ] FIX-01: app.py → iniciar_polling() no startup
- [ ] FIX-02: sidebar → 3 links novos em 6 HTMLs existentes
- [ ] NOVO-01: vendas.html
- [ ] NOVO-02: configuracoes.html
- [ ] NOVO-03: desperdicio.html
- [ ] NOVO-04: backend/relatorio.py + rota /api/relatorio/semanal
- [ ] NOVO-05: Procfile + gunicorn.conf.py
- [ ] NOVO-06: tools/validate_sprint3.py
