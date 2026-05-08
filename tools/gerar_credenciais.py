"""
Execute este script UMA VEZ para gerar as credenciais seguras do sistema.
Cole os valores gerados no seu .env.
"""
import secrets
import bcrypt

print("=" * 60)
print("CREDENCIAIS SEGURAS — Sistema CMV Quintal Goiano")
print("=" * 60)
print()

api_key    = secrets.token_hex(32)
jwt_secret = secrets.token_hex(32)

print(f"CMV_API_KEY={api_key}")
print(f"CMV_JWT_SECRET={jwt_secret}")
print()

senha = input("Digite a senha do admin (será salva com hash seguro): ").strip()
if senha:
    hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    print(f"\nCMV_ADMIN_PASSWORD={hashed}")
    print()
    print("⚠️  Cole esses 3 valores no seu .env antes de fazer o deploy.")
else:
    print("Senha não informada.")
