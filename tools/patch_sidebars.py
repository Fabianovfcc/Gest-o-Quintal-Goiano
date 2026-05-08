"""tools/patch_sidebars.py — POP_06: Atualiza sidebar em todos os HTMLs"""

SIDEBAR_TEMPLATE = """    <nav class="nav-items">
        <a href="dashboard.html" class="nav-item{active_dash}"><i data-lucide="layout-dashboard"></i> Dashboard</a>
        <a href="notas.html" class="nav-item{active_notas}"><i data-lucide="receipt"></i> Notas Fiscais</a>
        <a href="fichas.html" class="nav-item{active_fichas}"><i data-lucide="chef-hat"></i> Fichas Técnicas</a>
        <a href="insumos.html" class="nav-item{active_insumos}"><i data-lucide="package"></i> Insumos</a>
        <a href="estoque.html" class="nav-item{active_estoque}"><i data-lucide="package-open"></i> Estoque</a>
        <a href="#" class="nav-item" style="opacity:0.45;pointer-events:none;" title="Em breve"><i data-lucide="trash-2"></i> Desperdício</a>
        <a href="#" class="nav-item" style="opacity:0.45;pointer-events:none;" title="Em breve"><i data-lucide="shopping-bag"></i> Vendas</a>
        <a href="#" class="nav-item" style="margin-top:auto;"><i data-lucide="settings"></i> Configurações</a>
    </nav>"""

import re

def make_nav(active_page):
    keys = ['dash','notas','fichas','insumos','estoque']
    kw = {f'active_{k}': (' active' if active_page==k else '') for k in keys}
    return SIDEBAR_TEMPLATE.format(**kw)

pages = {
    'dashboard.html': 'dash',
    'notas.html': 'notas',
    'estoque.html': 'estoque',
}

for fname, active in pages.items():
    try:
        with open(fname, encoding='utf-8') as f:
            c = f.read()
        # Replace nav block (match from <nav class="nav-items"> to </nav>)
        new_c = re.sub(
            r'<nav class="nav-items">.*?</nav>',
            make_nav(active),
            c, flags=re.DOTALL
        )
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(new_c)
        print(f'[OK] {fname}')
    except Exception as e:
        print(f'[ERRO] {fname}: {e}')

# fichas.html already updated by patch_fichas.py
# insumos.html already correct from create_insumos.py
print('[OK] fichas.html e insumos.html ja atualizados anteriormente')
print('POP_06 concluido')
