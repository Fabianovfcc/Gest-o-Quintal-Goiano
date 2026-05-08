import os

def fix_html_files():
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    for f in html_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            changed = False
            # Caso 1: const API = 'http://localhost:5000/api';
            target1 = "const API = 'http://localhost:5000/api';"
            if target1 in content:
                content = content.replace(target1, "const API = '/api';")
                changed = True
            
            # Caso 2: const API='http://localhost:5000/api'; (sem espaços)
            target2 = "const API='http://localhost:5000/api';"
            if target2 in content:
                content = content.replace(target2, "const API='/api';")
                changed = True
                
            if changed:
                with open(f, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f'Atualizado: {f}')
        except Exception as e:
            print(f'Erro ao processar {f}: {e}')

if __name__ == "__main__":
    fix_html_files()
