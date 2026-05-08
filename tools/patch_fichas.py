import re

with open('fichas.html', encoding='utf-8') as f:
    c = f.read()

# 1) Sidebar com 8 links
old_nav = """    <nav class="nav-items">
        <a href="dashboard.html" class="nav-item"><i data-lucide="layout-dashboard"></i> Dashboard</a>
        <a href="notas.html"     class="nav-item"><i data-lucide="receipt"></i> Notas Fiscais</a>
        <a href="fichas.html"    class="nav-item active"><i data-lucide="chef-hat"></i> Fichas Técnicas</a>
        <a href="estoque.html"   class="nav-item"><i data-lucide="package-open"></i> Estoque</a>
        <a href="#" class="nav-item" style="margin-top:auto;"><i data-lucide="settings"></i> Configurações</a>
    </nav>"""
new_nav = """    <nav class="nav-items">
        <a href="dashboard.html" class="nav-item"><i data-lucide="layout-dashboard"></i> Dashboard</a>
        <a href="notas.html" class="nav-item"><i data-lucide="receipt"></i> Notas Fiscais</a>
        <a href="fichas.html" class="nav-item active"><i data-lucide="chef-hat"></i> Fichas Técnicas</a>
        <a href="insumos.html" class="nav-item"><i data-lucide="package"></i> Insumos</a>
        <a href="estoque.html" class="nav-item"><i data-lucide="package-open"></i> Estoque</a>
        <a href="#" class="nav-item" style="opacity:0.45;pointer-events:none;" title="Em breve"><i data-lucide="trash-2"></i> Desperdício</a>
        <a href="#" class="nav-item" style="opacity:0.45;pointer-events:none;" title="Em breve"><i data-lucide="shopping-bag"></i> Vendas</a>
        <a href="#" class="nav-item" style="margin-top:auto;"><i data-lucide="settings"></i> Configurações</a>
    </nav>"""
c = c.replace(old_nav, new_nav)

# 2) Botão novo prato no header
c = c.replace(
    '<h2>Cardápio</h2>',
    '<h2>Cardápio</h2><button onclick="abrirModalNovoPrato()" style="width:100%;margin-top:8px;padding:7px;border-radius:8px;border:none;background:linear-gradient(135deg,#f59e0b,#ea580c);color:#fff;cursor:pointer;font-weight:600;font-size:12px;display:flex;align-items:center;justify-content:center;gap:6px;"><i data-lucide=\'plus\' size=\'14\'></i> Novo Prato</button>'
)

# 3) Coluna Obs no thead
c = c.replace(
    '<th>Status</th>\n                            <th></th>',
    '<th>Obs.</th>\n                            <th>Status</th>\n                            <th></th>'
)

# 4) renderPratos com botão duplicar
old_render = """        el.innerHTML = lista.map(p => `
            <button class="prato-btn ${pratoAtual?.id === p.id ? 'active' : ''}"
                    onclick="selecionarPrato(${p.id})">
                <div class="prato-nome">${p.nome}</div>
                <div class="prato-cat">${p.categoria} · ${p.total_ingredientes} ingredientes
                    ${p.ingredientes_pendentes > 0
                        ? `<span style="color:#ef4444;"> · ${p.ingredientes_pendentes} pendentes</span>`
                        : ''}
                </div>
            </button>
        `).join('');"""
new_render = """        el.innerHTML = lista.map(p => `
            <button class="prato-btn ${pratoAtual?.id === p.id ? 'active' : ''}"
                    style="position:relative" onclick="selecionarPrato(${p.id})">
                <div class="prato-nome">${p.nome}</div>
                <div class="prato-cat">${p.categoria} · ${p.total_ingredientes||0} ing.
                    ${p.ingredientes_pendentes > 0 ? '<span style="color:#ef4444;"> pendentes</span>' : ''}
                </div>
                <span class="btn-dup" onclick="duplicarPrato(event,${p.id})" title="Duplicar">&#x29C9;</span>
            </button>
        `).join('');"""
c = c.replace(old_render, new_render)

# 5) renderFicha tbody com obs e formulario inline
old_tbody = """        tbody.innerHTML = (data.ingredientes || []).map(ing => {
            const custoPorUnit = ing.custo_compra > 0
                ? `R$ ${(ing.custo_compra).toLocaleString('pt-BR',{minimumFractionDigits:2})}/${ing.unidade}`
                : '—';
            const custoItem = ing.custo_item != null
                ? `R$ ${ing.custo_item.toLocaleString('pt-BR',{minimumFractionDigits:4})}`
                : '—';
            const statusHtml = ing.status_cadastro === 'PENDENTE'
                ? `<span class="status-pendente"><i data-lucide="alert-circle" size="12"></i> Pendente</span>`
                : `<span class="status-ok"><i data-lucide="check-circle" size="12"></i> OK</span>`;

            return `<tr data-id="${ing.id || ''}">
                <td style="font-weight:500">${ing.insumo}</td>
                <td><input class="qty-input" type="number" value="${ing.quantidade}" step="0.1" min="0"
                           onchange="marcarAlterado(this)"></td>
                <td style="color:var(--muted)">${ing.unidade}</td>
                <td style="color:var(--muted)">${custoPorUnit}</td>
                <td style="color:var(--primary);font-weight:600">${custoItem}</td>
                <td>${statusHtml}</td>
                <td style="display:flex;gap:6px;">
                    <button class="btn-save-row" onclick="salvarItemFicha(this)">Salvar</button>
                    <button class="btn-del-row" onclick="deletarItemFicha(this)"><i data-lucide="trash-2" size="12"></i></button>
                </td>
            </tr>`;
        }).join('');"""
new_tbody = """        const fmtR2 = v => v != null ? `R$ ${v.toLocaleString('pt-BR',{minimumFractionDigits:2})}` : '—';
        tbody.innerHTML = (data.ingredientes || []).map(ing => {
            const custoPorUnit = ing.custo_compra > 0 ? fmtR2(ing.custo_compra)+'/'+ing.unidade : '—';
            const custoItem = ing.custo_item != null ? `R$ ${ing.custo_item.toLocaleString('pt-BR',{minimumFractionDigits:4})}` : '—';
            const st = ing.status_cadastro === 'PENDENTE'
                ? `<span class="status-pendente"><i data-lucide="alert-circle" size="12"></i> Pendente</span>`
                : `<span class="status-ok"><i data-lucide="check-circle" size="12"></i> OK</span>`;
            return `<tr data-id="${ing.id||''}">
                <td style="font-weight:500">${ing.insumo}</td>
                <td><input class="qty-input inp-qtd" type="number" value="${ing.quantidade}" step="0.1" min="0"></td>
                <td style="color:var(--muted)">${ing.unidade}</td>
                <td style="color:var(--muted)">${custoPorUnit}</td>
                <td style="color:var(--primary);font-weight:600">${custoItem}</td>
                <td><input class="qty-input inp-obs" type="text" value="${ing.observacao||''}" placeholder="obs..." style="width:110px"></td>
                <td>${st}</td>
                <td style="display:flex;gap:6px;">
                    <button class="btn-save-row" onclick="salvarItemFicha(this)">Salvar</button>
                    <button class="btn-del-row" onclick="deletarItemFicha(this)"><i data-lucide="trash-2" size="12"></i></button>
                </td>
            </tr>`;
        }).join('') + `<tr style="background:rgba(245,158,11,0.04);border-top:1px dashed rgba(245,158,11,0.2);">
            <td colspan="8"><div style="display:flex;gap:8px;align-items:center;padding:6px 0;">
                <select id="sel-insumo" class="qty-input" style="width:200px" onfocus="carregarInsumoSelect()"><option value="">Buscar insumo...</option></select>
                <input id="qtd-novo" type="number" class="qty-input" placeholder="Qtd" step="0.1" style="width:75px">
                <input id="obs-novo" type="text" class="qty-input" placeholder="Observacao" style="width:120px">
                <button class="btn-save-row" onclick="adicionarIngrediente()" style="white-space:nowrap">+ Adicionar</button>
            </div></td>
        </tr>`;"""
c = c.replace(old_tbody, new_tbody)

# 6) salvarItemFicha - salvar obs tbm
old_save = "        const qtd = parseFloat(row.querySelector('.qty-input').value);"
new_save = "        const qtd = parseFloat(row.querySelector('.inp-qtd').value);\n        const obs = row.querySelector('.inp-obs')?.value || '';"
c = c.replace(old_save, new_save, 1)

old_body_save = "body: JSON.stringify({ quantidade: qtd }),"
new_body_save = "body: JSON.stringify({ quantidade: qtd, observacao: obs }),"
c = c.replace(old_body_save, new_body_save, 1)

# 7) Adicionar CSS btn-dup e scripts de modal/duplicar/adicionar antes de </script>
extra_css = """
        .btn-dup { position:absolute;right:10px;top:50%;transform:translateY(-50%);
            padding:3px 7px;border-radius:6px;color:var(--muted);font-size:16px;
            opacity:0;transition:opacity 0.2s;cursor:pointer;background:none;border:none; }
        .prato-btn:hover .btn-dup { opacity:1; }
        .btn-dup:hover { background:rgba(255,255,255,0.08);color:var(--text); }"""
c = c.replace("        @keyframes fadeIn", extra_css + "\n        @keyframes fadeIn", 1)

extra_js = """
    // Modal novo prato
    function abrirModalNovoPrato() { document.getElementById('modal-np').style.display='flex'; }
    function fecharModalNovoPrato() { document.getElementById('modal-np').style.display='none'; }
    async function salvarNovoPrato() {
        const nome = document.getElementById('np-nome').value.trim();
        if (!nome) { toast('Nome obrigatorio.','err'); return; }
        const res = await fetch(API+'/pratos',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({nome,categoria:document.getElementById('np-cat').value,
            descricao:document.getElementById('np-desc').value,
            preco_venda:parseFloat(document.getElementById('np-preco').value)||0})});
        const d = await res.json();
        if(d.ok){fecharModalNovoPrato();await carregarPratos();selecionarPrato(d.prato.id);toast('Prato criado!','ok');}
        else toast(d.erro,'err');
    }
    // Duplicar prato
    async function duplicarPrato(e,id) {
        e.stopPropagation();
        if(!confirm('Duplicar prato com toda a ficha tecnica?')) return;
        const res = await fetch(API+'/pratos/'+id+'/duplicar',{method:'POST'});
        const d = await res.json();
        if(d.ok){await carregarPratos();selecionarPrato(d.prato.id);toast('Prato duplicado!','ok');}
        else toast(d.erro,'err');
    }
    // Adicionar ingrediente
    let todosInsumos = [];
    async function carregarInsumoSelect() {
        if(todosInsumos.length) return;
        todosInsumos = await fetch(API+'/insumos').then(r=>r.json());
        const sel = document.getElementById('sel-insumo');
        sel.innerHTML = '<option value="">Selecione...</option>' +
            todosInsumos.map(i=>`<option value="${i.id}">${i.nome} (${i.unidade})</option>`).join('');
    }
    async function adicionarIngrediente() {
        if(!pratoAtual) return;
        const insumo_id = document.getElementById('sel-insumo').value;
        const quantidade = parseFloat(document.getElementById('qtd-novo').value);
        const observacao = document.getElementById('obs-novo').value;
        if(!insumo_id||isNaN(quantidade)){toast('Preencha insumo e quantidade.','err');return;}
        const res = await fetch(API+'/pratos/'+pratoAtual.id+'/ficha',{method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({insumo_id,quantidade,observacao})});
        const d = await res.json();
        if(d.ok){document.getElementById('qtd-novo').value='';document.getElementById('obs-novo').value='';
            selecionarPrato(pratoAtual.id);toast('Ingrediente adicionado!','ok');}
        else toast(d.erro,'err');
    }"""
c = c.replace("    carregarPratos();\n</script>", extra_js + "\n    carregarPratos();\n</script>", 1)

# 8) Modal HTML antes de </body>
modal_html = """
<!-- MODAL NOVO PRATO -->
<div id="modal-np" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:100;align-items:center;justify-content:center;">
  <div style="background:#1e293b;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:32px;width:420px;display:flex;flex-direction:column;gap:16px;">
    <div style="font-size:18px;font-weight:700;">Novo Prato</div>
    <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Nome *</div>
    <input id="np-nome" type="text" placeholder="Nome do prato" style="width:100%;background:#334155;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:9px 12px;color:#f8fafc;font-size:14px;outline:none;"></div>
    <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Categoria</div>
    <select id="np-cat" style="width:100%;background:#334155;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:9px 12px;color:#f8fafc;font-size:14px;outline:none;">
    <option>Marmita</option><option>Prato Principal</option><option>Petisco</option><option>Acompanhamento</option><option>Bebida</option></select></div>
    <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Descricao</div>
    <textarea id="np-desc" rows="2" placeholder="Descricao opcional" style="width:100%;background:#334155;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:9px 12px;color:#f8fafc;font-size:14px;outline:none;resize:none;"></textarea></div>
    <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Preco de Venda (R$)</div>
    <input id="np-preco" type="number" step="0.01" min="0" placeholder="0,00" style="width:100%;background:#334155;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:9px 12px;color:#f8fafc;font-size:14px;outline:none;"></div>
    <div style="display:flex;gap:10px;justify-content:flex-end;">
    <button onclick="fecharModalNovoPrato()" style="padding:9px 18px;border-radius:10px;border:none;background:#334155;color:#f8fafc;cursor:pointer;font-weight:600;">Cancelar</button>
    <button onclick="salvarNovoPrato()" style="padding:9px 18px;border-radius:10px;border:none;background:linear-gradient(135deg,#f59e0b,#ea580c);color:#fff;cursor:pointer;font-weight:600;">Criar</button>
    </div>
  </div>
</div>"""
c = c.replace('</body>', modal_html + '\n</body>')

with open('fichas.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('OK - fichas.html atualizado com sucesso')
