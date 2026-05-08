"""POP_13+14+15: patch sidebar Rotina em todos os HTMLs + melhorias dash/notas"""
import re

PAGES = ['dashboard.html','notas.html','fichas.html','insumos.html','estoque.html','rotina.html']

NAV_NEW = {
    'dashboard.html': 'active_dash',
    'rotina.html':    'active_rotina',
    'notas.html':     'active_notas',
    'fichas.html':    'active_fichas',
    'insumos.html':   'active_insumos',
    'estoque.html':   'active_estoque',
}

def make_nav(active):
    links = [
        ('dashboard.html','layout-dashboard','Dashboard',    active=='active_dash'),
        ('rotina.html',   'sun',             'Rotina',       active=='active_rotina'),
        ('notas.html',    'receipt',         'Notas Fiscais',active=='active_notas'),
        ('fichas.html',   'chef-hat',        'Fichas',       active=='active_fichas'),
        ('insumos.html',  'package',         'Insumos',      active=='active_insumos'),
        ('estoque.html',  'package-open',    'Estoque',      active=='active_estoque'),
    ]
    items = ''
    for href,icon,label,is_active in links:
        cls = 'nav-item active' if is_active else 'nav-item'
        if label == 'Rotina':
            items += f'        <a href="{href}" class="{cls}" style="border:1px solid rgba(245,158,11,{0.3 if is_active else 0.12});"><i data-lucide="{icon}"></i> {label}</a>\n'
        else:
            items += f'        <a href="{href}" class="{cls}"><i data-lucide="{icon}"></i> {label}</a>\n'
    items += '        <a href="#" class="nav-item" style="opacity:0.45;pointer-events:none;" title="Em breve"><i data-lucide="trash-2"></i> Desperdício</a>\n'
    items += '        <a href="#" class="nav-item" style="opacity:0.45;pointer-events:none;" title="Em breve"><i data-lucide="shopping-bag"></i> Vendas</a>\n'
    items += '        <a href="#" class="nav-item" style="margin-top:auto;"><i data-lucide="settings"></i> Configurações</a>\n'
    return f'    <nav class="nav-items">\n{items}    </nav>'

for page in PAGES:
    try:
        c = open(page, encoding='utf-8').read()
        active_key = NAV_NEW.get(page, 'active_dash')
        new_nav = make_nav(active_key)
        c2 = re.sub(r'<nav class="nav-items">.*?</nav>', new_nav, c, flags=re.DOTALL)
        open(page, 'w', encoding='utf-8').write(c2)
        print(f'[OK] {page}')
    except Exception as e:
        print(f'[ERR] {page}: {e}')

print('POP_13+14+15 sidebar done')
