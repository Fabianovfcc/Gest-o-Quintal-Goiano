import requests
import json

try:
    r = requests.get("http://127.0.0.1:5000/api/vendas/recentes")
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
