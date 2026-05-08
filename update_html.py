import os

html_files = [
    'dashboard.html', 'rotina.html', 'notas.html', 'fichas.html',
    'insumos.html', 'estoque.html', 'compras.html', 'vendas.html',
    'desperdicio.html', 'configuracoes.html'
]

logout_btn = """
        <a href="#" class="nav-item" onclick="logout()" style="margin-top:auto; color: #ef4444;">
            <i data-lucide="log-out"></i> Sair
        </a>
    </nav>"""

auth_script = """
<script>
// Guard de autenticação — redireciona para login se sem sessão
(async function() {
    try {
        const res = await fetch('/api/auth/verificar', { credentials: 'include' });
        const data = await res.json();
        if (!data.ok) window.location.href = '/login.html';
    } catch (e) {
        window.location.href = '/login.html';
    }
})();

// Injeta API Key em todas as chamadas fetch automaticamente
const _fetchOriginal = window.fetch;
window.fetch = function(url, opts = {}) {
    const token = sessionStorage.getItem('cmv_token');
    const apiKey = sessionStorage.getItem('cmv_api_key') || '';
    if (typeof url === 'string' && url.includes('/api/')) {
        opts.headers = {
            ...(opts.headers || {}),
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        };
        opts.credentials = 'include';
    }
    return _fetchOriginal(url, opts);
};

async function logout() {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    sessionStorage.clear();
    window.location.href = '/login.html';
}
</script>
</body>"""

for html_file in html_files:
    if os.path.exists(html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'logout()' not in content:
            content = content.replace('</nav>', logout_btn)
            content = content.replace('</body>', auth_script)
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
        print(f"Updated {html_file}")
    else:
        print(f"File {html_file} not found!")
