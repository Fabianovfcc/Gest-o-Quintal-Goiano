"""
backend/sql_compat.py
Adapta queries SQLite para PostgreSQL automaticamente.
"""
from db import is_postgres


def q(query: str) -> str:
    """Adapta query para o banco em uso."""
    if not is_postgres():
        return query
    replacements = {
        "INSERT OR IGNORE INTO":           "INSERT INTO",
        "INSERT OR REPLACE INTO":          "INSERT INTO",
        "ON CONFLICT(descricao_nf) DO UPDATE SET insumo_id = excluded.insumo_id":
            "ON CONFLICT (descricao_nf) DO UPDATE SET insumo_id = EXCLUDED.insumo_id",
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor":
            "ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor",
        "datetime('now','localtime')":     "NOW()",
        "date('now','localtime')":         "CURRENT_DATE",
        "date('now')":                     "CURRENT_DATE",
        "strftime('%Y-%m-%d','now')":      "TO_CHAR(NOW(),'YYYY-MM-DD')",
        "GROUP_CONCAT":                    "STRING_AGG",
        "INTEGER PRIMARY KEY AUTOINCREMENT": "SERIAL PRIMARY KEY",
        "?":                               "%s",
    }
    for old, new in replacements.items():
        query = query.replace(old, new)
    return query
