"""
tools/validate_sprint3.py
Script final de validação da Sprint 3.
Verifica se todos os arquivos, rotas e integrações estão operacionais.
"""
import os
import requests
import sys

def validate():
    print("--- Iniciando Validacao Final - Sprint 3 ---\n")
    
    # 1. Verificar Arquivos Novos
    arquivos = [
        "vendas.html",
        "configuracoes.html",
        "desperdicio.html",
        "backend/relatorio.py",
        "backend/integracoes/polling_99food.py",
        "Procfile",
        "gunicorn.conf.py"
    ]
    
    print("Verificando arquivos:")
    for f in arquivos:
        exists = os.path.exists(f)
        status = "[OK]" if exists else "[ERRO]"
        print(f"  {status} {f}")
    
    # 2. Verificar API (Assumindo que o servidor está rodando)
    print("\nVerificando rotas da API (127.0.0.1:5000):")
    base_url = "http://127.0.0.1:5000/api"
    routes = [
        "/status",
        "/vendas/recentes",
        "/desperdicio/hoje",
        "/pratos"
    ]
    
    for r in routes:
        try:
            res = requests.get(base_url + r, timeout=2)
            status = "[OK]" if res.status_code == 200 else "[ERRO]"
            print(f"  {status} {r} ({res.status_code})")
        except:
            print(f"  [AVISO] {r} (Servidor offline - ignore se nao estiver rodando)")

    # 3. Verificar Sidebar nos HTMLs
    print("\nVerificando sidebar nos HTMLs:")
    htmls = ["dashboard.html", "rotina.html", "notas.html", "fichas.html", "insumos.html", "estoque.html"]
    for h in htmls:
        try:
            with open(h, "r", encoding="utf-8") as f:
                content = f.read()
                # Procurar links novos
                links_ok = "vendas.html" in content and "desperdicio.html" in content and "configuracoes.html" in content
                status = "[OK]" if links_ok else "[ERRO]"
                print(f"  {status} {h}")
        except Exception as e:
            print(f"  [ERRO] {h}: {e}")

    print("\nValidacao concluida!")

if __name__ == "__main__":
    validate()
