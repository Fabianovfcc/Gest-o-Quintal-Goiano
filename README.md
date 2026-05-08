# Restaurante CMV - Quintal Goiano

Sistema personalizado para controle de Custo de Mercadoria Vendida (CMV) e lucratividade.

## Estrutura do Projeto

- `/data`: Contém as fichas técnicas e dados históricos de venda em JSON.
- `database_schema.sql`: Definição das tabelas para o banco de dados SQLite.
- `implementation_plan.md`: Plano detalhado das fases de desenvolvimento.

## Dados Atuais
- **Faturamento Médio (4 dias):** R$ 4.403,00 (Receita Plataforma).
- **Volume de Pedidos:** ~40/dia.
- **Plataformas:** 99Food (configurada), iFood (em breve).

## Próximos Passos
1. Cadastro de custos de aquisição de insumos (kg/un).
2. Desenvolvimento do parser de XML de Notas Fiscais.
3. Criação da interface Dashboard Premium.
