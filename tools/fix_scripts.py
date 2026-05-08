import os
import re

def fix_html_scripts():
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    
    script_pattern = re.compile(r'(<script>\s*// Guard de autenticação.*?async function logout\(\) \{.*?</script>)', re.DOTALL)
    head_pattern = re.compile(r'(</head>)', re.IGNORECASE)

    for f in html_files:
        if f == 'login.html':
            continue # Login doesn't need the guard
            
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            match = script_pattern.search(content)
            if match:
                script_block = match.group(1)
                # Remove the script block from its current location
                new_content = content.replace(script_block, '')
                # Insert it right before </head>
                new_content = head_pattern.sub(f'{script_block}\\n\\1', new_content, count=1)
                
                if new_content != content:
                    with open(f, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    print(f'Atualizado (Scripts ordenados): {f}')
            else:
                print(f'Script de guard não encontrado em: {f}')
                
        except Exception as e:
            print(f'Erro ao processar {f}: {e}')

if __name__ == "__main__":
    fix_html_scripts()
