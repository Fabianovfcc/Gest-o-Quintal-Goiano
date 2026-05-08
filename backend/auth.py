"""
auth.py — Camada de autenticação do Sistema CMV Quintal Goiano
Protege todas as rotas da API com API Key + JWT opcional.
"""
import os
import jwt
import bcrypt
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env antes de ler as variáveis
load_dotenv(Path(__file__).parent.parent / '.env')

from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify

# ─── Chaves carregadas do .env ────────────────────────────────────────────────
API_KEY         = os.getenv("CMV_API_KEY", "")
JWT_SECRET      = os.getenv("CMV_JWT_SECRET", secrets.token_hex(32))
ADMIN_PASSWORD  = os.getenv("CMV_ADMIN_PASSWORD", "")
ALLOWED_ORIGINS = os.getenv("CMV_ALLOWED_ORIGINS", "http://localhost:5000").split(",")
ENV             = os.getenv("ENVIRONMENT", "development")


def _is_dev():
    return ENV == "development"


# ─── Verificação de API Key ───────────────────────────────────────────────────
def _check_api_key() -> bool:
    """Valida a API Key recebida no header X-API-Key ou query param api_key."""
    if _is_dev() and not API_KEY:
        return True  # Em dev sem key configurada, libera para facilitar testes locais
    key = request.headers.get("X-API-Key") or request.args.get("api_key", "")
    return secrets.compare_digest(key, API_KEY)


# ─── Decorator: protege rotas com API Key ────────────────────────────────────
def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _check_api_key():
            return jsonify({"ok": False, "erro": "Não autorizado. API Key inválida."}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Geração de JWT (sessão web) ─────────────────────────────────────────────
def gerar_token(usuario: str = "admin", horas: int = 12) -> str:
    payload = {
        "sub": usuario,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=horas),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ─── Decorator: protege rotas com JWT ────────────────────────────────────────
def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Aceita JWT via header Authorization: Bearer <token>
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()

        # Ou via cookie de sessão
        if not token:
            token = request.cookies.get("cmv_session", "")

        if not token or not verificar_token(token):
            return jsonify({"ok": False, "erro": "Sessão inválida ou expirada. Faça login novamente."}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Verificação de senha do admin ───────────────────────────────────────────
def verificar_senha_admin(senha: str) -> bool:
    if not ADMIN_PASSWORD:
        return False
    try:
        return bcrypt.checkpw(senha.encode(), ADMIN_PASSWORD.encode())
    except Exception:
        # Fallback: comparação direta se a senha não foi hashada ainda
        return secrets.compare_digest(senha, ADMIN_PASSWORD)


# ─── Headers de segurança ────────────────────────────────────────────────────
def aplicar_headers_seguranca(response):
    """Aplica headers HTTP de segurança em todas as respostas."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if not _is_dev():
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
