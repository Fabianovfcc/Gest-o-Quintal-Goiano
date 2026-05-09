"""
backend/db.py
Gerenciador de conexão dual: SQLite (dev) ou PostgreSQL/Supabase (prod).
Lê variáveis de ambiente em tempo de execução (não no import).
Inclui adaptador de compatibilidade para psycopg2.
"""
import os, sqlite3
from pathlib import Path

# Carregar .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

SQLITE_PATH = str(Path(__file__).parent.parent / 'data' / 'cmv.db')


def _adapt_sql(sql: str) -> str:
    """Traduz dialeto SQLite para PostgreSQL básico."""
    if not isinstance(sql, str):
        return sql
    
    replacements = {
        "INSERT OR IGNORE INTO":           "INSERT INTO",
        "INSERT OR REPLACE INTO":          "INSERT INTO",
        "datetime('now','localtime')":     "NOW()",
        "date('now','localtime')":         "CURRENT_DATE",
        "date('now')":                     "CURRENT_DATE",
        "strftime('%Y-%m-%d','now')":      "TO_CHAR(NOW(),'YYYY-MM-DD')",
        "GROUP_CONCAT":                    "STRING_AGG",
        "INTEGER PRIMARY KEY AUTOINCREMENT": "SERIAL PRIMARY KEY",
        "?":                               "%s",
    }
    # Caso especial para ON CONFLICT (comum no sistema)
    if "ON CONFLICT" in sql:
        sql = sql.replace("excluded.", "EXCLUDED.")
        
    for old, new in replacements.items():
        sql = sql.replace(old, new)
    return sql


class PostgresCompatibleConnection:
    """
    Adaptador para fazer o psycopg2 se comportar como o sqlite3.
    """
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=()):
        sql = _adapt_sql(sql)
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql, params_list):
        sql = _adapt_sql(sql)
        cur = self.conn.cursor()
        cur.executemany(sql, params_list)
        return cur

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def cursor(self):
        # Retorna um cursor que também adapta SQL ao ser usado
        return PostgresCompatibleCursor(self.conn.cursor())


class PostgresCompatibleCursor:
    """Cursor que adapta SQL automaticamente."""
    def __init__(self, cursor):
        self.cursor = cursor
    
    def execute(self, sql, params=()):
        self.cursor.execute(_adapt_sql(sql), params)
        return self
        
    def _dict_row(self, row):
        if not row: return None
        # Transforma a tupla retornada pelo pg8000 em um dicionário compatível com sqlite3.Row
        return {desc[0]: val for desc, val in zip(self.cursor.description, row)}
        
    def fetchone(self): return self._dict_row(self.cursor.fetchone())
    def fetchall(self): return [self._dict_row(row) for row in self.cursor.fetchall()]
    @property
    def lastrowid(self):
        # Tenta obter o último ID inserido via LASTVAL() se necessário
        # Nota: Idealmente usar RETURNING id, mas aqui é para compatibilidade
        try:
            self.cursor.execute("SELECT LASTVAL()")
            return self.cursor.fetchone()[0]
        except:
            return None


def _use_pg() -> bool:
    """Verifica em tempo de execução se deve usar PostgreSQL."""
    db_url = os.getenv('SUPABASE_DB_URL', '')
    env    = os.getenv('ENVIRONMENT', 'development')
    return bool(db_url) and env == 'production'


def get_connection():
    """Retorna conexão com o banco correto conforme ambiente."""
    if _use_pg():
        import pg8000.dbapi
        import urllib.parse
        import ssl
        
        db_url = os.getenv('SUPABASE_DB_URL')
        parsed = urllib.parse.urlparse(db_url)
        
        # Contexto SSL que permite conexão criptografada sem verificar certificado
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        
        conn = pg8000.dbapi.connect(
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            ssl_context=ssl_ctx
        )
        return PostgresCompatibleConnection(conn)
    else:
        os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def is_postgres() -> bool:
    return _use_pg()


def sql_now() -> str:
    return "NOW()" if _use_pg() else "datetime('now','localtime')"


def sql_today() -> str:
    return "CURRENT_DATE" if _use_pg() else "date('now','localtime')"
