"""tools/create_insumos.py — Cria insumos.html (POP_05)"""
html = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Insumos — CMV Quintal Goiano</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest"></script>
<style>
:root{--bg:#0f172a;--surface:#1e293b;--surface2:#334155;--primary:#f59e0b;--primary-glow:rgba(245,158,11,0.15);--success:#10b981;--danger:#ef4444;--text:#f8fafc;--muted:#94a3b8;--border:rgba(255,255,255,0.06);}
*{margin:0;padding:0;box-sizing:border-box;font-family:'Outfit',sans-serif;}
body{background:var(--bg);color:var(--text);display:flex;min-height:100vh;}
.sidebar{width:260px;padding:24px;display:flex;flex-direction:column;border-right:1px solid var(--border);background:linear-gradient(180deg,#0f172a 0%,rgba(30,41,59,0.5) 100%);position:fixed;top:0;left:0;height:100vh;}
.brand{display:flex;align-items:center;gap:12px;font-size:22px;font-weight:700;color:var(--primary);margin-bottom:36px;}
.nav-items{display:flex;flex-direction:column;gap:6px;flex:1;}
.nav-item{display:flex;align-items:center;gap:12px;padding:11px 16px;border-radius:12px;color:var(--muted);text-decoration:none;transition:all 0.2s;font-weight:500;font-size:14px;}
.nav-item:hover{color:var(--text);background:rgba(255,255,255,0.05);}
.nav-item.active{color:var(--primary);background:var(--primary-glow);border:1px solid rgba(245,158,11,0.1);}
.main{margin-left:260px;flex:1;padding:36px 40px;display:flex;flex-direction:column;gap:24px;}
.glass{background:rgba(30,41,59,0.7);backdrop-filter:blur(12px);border:1px solid var(--border);border-radius:16px;}
.btn{display:inline-flex;align-items:center;gap:8px;padding:9px 18px;border-radius:10px;border:none;font-weight:600;cursor:pointer;font-size:14px;transition:all 0.2s;}
.btn-primary{background:linear-gradient(135deg,#f59e0b,#ea580c);color:#fff;box-shadow:0 4px 15px rgba(234,88,12,0.3);}
.btn-primary:hover{transform:translateY(-2px);}
.btn-ghost{background:var(--surface2);color:var(--text);}
.btn-ghost:hover{background:#475569;}
/* Progresso */
.prog-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;}
.prog-card{padding:16px;border-radius:12px;background:rgba(30,41,59,0.7);border:1px solid var(--border);}
.prog-card-title{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;}
.prog-bar-bg{background:rgba(255,255,255,0.05);border-radius:4px;height:6px;margin-bottom:6px;overflow:hidden;}
.prog-bar-fill{height:100%;border-radius:4px;transition:width 0.6s cubic-bezier(0.25,0.46,0.45,0.94);}
.prog-count{font-size:11px;color:var(--muted);}
/* Tabela */
.tbl-header{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid var(--border);flex-wrap:wrap;gap:12px;}
table{width:100%;border-collapse:collapse;font-size:14px;}
th{text-align:left;padding:10px 12px;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid var(--border);}
td{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.03);vertical-align:middle;}
tr.row-completo{border-left:3px solid var(--success);}
tr.row-pendente{border-left:3px solid var(--danger);opacity:0.85;}
tr.row-alerta td:nth-child(7){color:#f59e0b;font-weight:600;}
.cell-edit{background:var(--surface2);border:1px solid transparent;border-radius:6px;padding:4px 8px;color:var(--text);font-size:13px;width:90px;outline:none;transition:border 0.2s;}
.cell-edit:focus{border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-glow);}
.badge{display:inline-flex;padding:2px 8px;border-radius:5px;font-size:11px;font-weight:600;}
.badge-ok{background:rgba(16,185,129,0.1);color:#10b981;}
.badge-pend{background:rgba(239,68,68,0.1);color:#ef4444;}
.cat-header{padding:10px 12px;font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;background:rgba(255,255,255,0.02);border-bottom:1px solid var(--border);}
/* Modal */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:100;align-items:center;justify-content:center;}
.modal-box{background:#1e293b;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:32px;width:440px;display:flex;flex-direction:column;gap:16px;}
.field-label{font-size:11px;color:var(--muted);margin-bottom:4px;}
.field-input{width:100%;background:#334155;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:9px 12px;color:#f8fafc;font-size:14px;outline:none;}
.field-input:focus{border-color:var(--primary);}
/* Importação */
.import-zone{border:2px dashed rgba(245,158,11,0.3);border-radius:12px;padding:24px;text-align:center;cursor:pointer;transition:all 0.2s;margin-top:12px;}
.import-zone:hover{border-color:var(--primary);background:var(--primary-glow);}
.preview-table{max-height:280px;overflow-y:auto;margin-top:12px;}
.toast{position:fixed;bottom:24px;right:24px;padding:14px 20px;border-radius:12px;font-weight:600;font-size:14px;z-index:999;display:none;}
.toast.ok{background:#10b981;color:#fff;}
.toast.err{background:#ef4444;color:#fff;}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
.fade-in{animation:fadeIn 0.3s ease;}
</style>
</head>
<body>
<aside class="sidebar">
  <div class="brand"><i data-lucide="flame"></i> Quintal Goiano</div>
  <nav class="nav-items">
    <a href="dashboard.html" class="nav-item"><i data-lucide="layout-dashboard"></i> Dashboard</a>
    <a href="notas.html" class="nav-item"><i data-lucide="receipt"></i> Notas Fiscais</a>
    <a href="fichas.html" class="nav-item"><i data-lucide="chef-hat"></i> Fichas Técnicas</a>
    <a href="insumos.html" class="nav-item active"><i data-lucide="package"></i> Insumos</a>
    <a href="estoque.html" class="nav-item"><i data-lucide="package-open"></i> Estoque</a>
    <a href="#" class="nav-item" style="opacity:0.45;pointer-events:none;" title="Em breve"><i data-lucide="trash-2"></i> Desperdício</a>
    <a href="#" class="nav-item" style="opacity:0.45;pointer-events:none;" title="Em breve"><i data-lucide="shopping-bag"></i> Vendas</a>
    <a href="#" class="nav-item" style="margin-top:auto;"><i data-lucide="settings"></i> Configurações</a>
  </nav>
</aside>

<main class="main">
  <!-- HEADER -->
  <div class="fade-in" style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
    <div>
      <div style="font-size:26px;font-weight:700;">Gestão de Insumos</div>
      <div style="color:var(--muted);font-size:14px;margin-top:4px;">Cadastre custos para desbloquear o cálculo de CMV</div>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <button class="btn btn-ghost" onclick="baixarTemplate()"><i data-lucide="download"></i> Baixar Template XLSX</button>
      <button class="btn btn-ghost" onclick="document.getElementById('upload-xlsx').click()"><i data-lucide="upload"></i> Importar XLSX</button>
      <input type="file" id="upload-xlsx" accept=".xlsx" style="display:none" onchange="uploadXlsx(this)">
      <button class="btn btn-primary" onclick="abrirModalNovoInsumo()"><i data-lucide="plus"></i> Novo Insumo</button>
    </div>
  </div>

  <!-- PROGRESSO GLOBAL -->
  <div class="glass" style="padding:20px 24px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <div style="font-weight:700;">Progresso de Cadastro</div>
      <div id="prog-global" style="font-size:13px;color:var(--muted);">Calculando...</div>
    </div>
    <div style="background:rgba(255,255,255,0.05);border-radius:6px;height:8px;overflow:hidden;margin-bottom:16px;">
      <div id="prog-global-bar" style="height:100%;border-radius:6px;background:linear-gradient(90deg,#f59e0b,#10b981);transition:width 0.8s ease;width:0%"></div>
    </div>
    <div class="prog-grid" id="prog-cats"></div>
  </div>

  <!-- TABELA DE INSUMOS -->
  <div class="glass fade-in">
    <div class="tbl-header">
      <div style="font-size:18px;font-weight:700;">Todos os Insumos</div>
      <div style="display:flex;gap:8px;">
        <input type="text" id="search-ins" placeholder="Buscar..." oninput="filtrar()" style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:8px 12px;color:var(--text);font-size:13px;outline:none;width:180px;">
        <select id="cat-filter" onchange="filtrar()" style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:8px 12px;color:var(--text);font-size:13px;outline:none;">
          <option value="">Todas as categorias</option>
        </select>
      </div>
    </div>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr>
          <th>Insumo</th><th>Categoria</th><th>Unid.</th>
          <th>Custo R$/un.</th><th>Rendimento</th>
          <th>Est. Atual</th><th>Est. Mínimo</th><th>Status</th><th>Ação</th>
        </tr></thead>
        <tbody id="ins-body"></tbody>
      </table>
    </div>
  </div>

  <!-- PAINEL IMPORTAÇÃO PREVIEW -->
  <div id="painel-preview" class="glass" style="display:none;padding:24px;">
    <div style="font-size:16px;font-weight:700;margin-bottom:8px;">Preview da Importação</div>
    <div id="preview-info" style="color:var(--muted);font-size:13px;margin-bottom:12px;"></div>
    <div class="preview-table" id="preview-body"></div>
    <div style="display:flex;gap:10px;margin-top:16px;">
      <button class="btn btn-ghost" onclick="cancelarImport()">Cancelar</button>
      <button class="btn btn-primary" onclick="confirmarImport()"><i data-lucide="check"></i> Confirmar Importação</button>
    </div>
  </div>
</main>

<!-- TOAST -->
<div class="toast" id="toast"></div>

<!-- MODAL NOVO INSUMO -->
<div id="modal-ni" class="modal-overlay">
  <div class="modal-box">
    <div style="font-size:18px;font-weight:700;">Novo Insumo</div>
    <div><div class="field-label">Nome *</div><input id="ni-nome" type="text" class="field-input" placeholder="Nome do insumo"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div><div class="field-label">Categoria</div>
      <select id="ni-cat" class="field-input">
        <option>Proteínas</option><option>Carboidratos</option><option>Laticínios e Frios</option>
        <option>Vegetais e Temperos</option><option>Embalagens</option><option>Bebidas</option><option>Outros</option>
      </select></div>
      <div><div class="field-label">Unidade</div>
      <select id="ni-unidade" class="field-input">
        <option value="kg">kg</option><option value="g">g</option><option value="l">L</option>
        <option value="ml">ml</option><option value="un">un</option><option value="maço">maço</option><option value="dz">dz</option>
      </select></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div><div class="field-label">Custo (R$/un)</div><input id="ni-custo" type="number" step="0.01" min="0" class="field-input" placeholder="0,00"></div>
      <div><div class="field-label">Rendimento (0 a 1)</div><input id="ni-rend" type="number" step="0.01" min="0.01" max="1" class="field-input" value="1.0" placeholder="ex: 0.85"></div>
    </div>
    <div><div class="field-label">Estoque Mínimo</div><input id="ni-min" type="number" step="0.1" min="0" class="field-input" placeholder="0"></div>
    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:4px;">
      <button class="btn btn-ghost" onclick="fecharModalNovoInsumo()">Cancelar</button>
      <button class="btn btn-primary" onclick="salvarNovoInsumo()">Criar Insumo</button>
    </div>
  </div>
</div>

<script>
const API = 'http://localhost:5000/api';
lucide.createIcons();
let todosInsumos = [];
let previewData = [];

async function carregarInsumos() {
  try {
    todosInsumos = await fetch(API+'/insumos').then(r=>r.json());
    renderProgresso(todosInsumos);
    renderFiltros(todosInsumos);
    renderTabela(todosInsumos);
  } catch(e) {
    document.getElementById('ins-body').innerHTML =
      '<tr><td colspan="9" style="padding:20px;color:var(--muted);">API offline — inicie o servidor Flask.</td></tr>';
  }
}

function renderProgresso(ins) {
  const total = ins.length;
  const completos = ins.filter(i=>i.status_cadastro==='COMPLETO').length;
  const pct = total ? Math.round(completos/total*100) : 0;
  document.getElementById('prog-global').textContent = `${completos}/${total} insumos com custo (${pct}%)`;
  document.getElementById('prog-global-bar').style.width = pct+'%';

  const cats = {};
  ins.forEach(i=>{
    const c = i.categoria_nome||'Outros';
    if(!cats[c]) cats[c]={total:0,ok:0};
    cats[c].total++;
    if(i.status_cadastro==='COMPLETO') cats[c].ok++;
  });
  const colors = {0:'#ef4444',1:'#f59e0b'};
  document.getElementById('prog-cats').innerHTML = Object.entries(cats).map(([cat,v])=>{
    const p=Math.round(v.ok/v.total*100);
    const col = p===100?'#10b981':p>0?'#f59e0b':'#ef4444';
    return `<div class="prog-card">
      <div class="prog-card-title">${cat}</div>
      <div class="prog-bar-bg"><div class="prog-bar-fill" style="width:${p}%;background:${col}"></div></div>
      <div class="prog-count">${v.ok}/${v.total} completos</div>
    </div>`;
  }).join('');
}

function renderFiltros(ins) {
  const cats = [...new Set(ins.map(i=>i.categoria_nome))].sort();
  const sel = document.getElementById('cat-filter');
  const existing = [...sel.options].map(o=>o.value);
  cats.forEach(c=>{ if(!existing.includes(c)){const o=document.createElement('option');o.value=c;o.textContent=c;sel.appendChild(o);} });
}

function filtrar() {
  const q = document.getElementById('search-ins').value.toLowerCase();
  const cat = document.getElementById('cat-filter').value;
  renderTabela(todosInsumos.filter(i=>i.nome.toLowerCase().includes(q)&&(!cat||i.categoria_nome===cat)));
}

function renderTabela(lista) {
  const cats = [...new Set(lista.map(i=>i.categoria_nome))].sort();
  const tbody = document.getElementById('ins-body');
  tbody.innerHTML = cats.map(cat=>{
    const rows = lista.filter(i=>i.categoria_nome===cat);
    return `<tr><td colspan="9" class="cat-header">${cat}</td></tr>` +
    rows.map(ins=>{
      const ok = ins.status_cadastro==='COMPLETO';
      const alerta = ins.estoque_atual < (ins.estoque_minimo||0) && ins.estoque_minimo > 0;
      const rowCls = ok?'row-completo':'row-pendente';
      const alertaCls = alerta?'row-alerta':'';
      return `<tr class="${rowCls} ${alertaCls}" data-id="${ins.id}">
        <td style="font-weight:500">${ins.nome}</td>
        <td style="color:var(--muted);font-size:12px">${ins.categoria_nome||'—'}</td>
        <td style="color:var(--muted)">${ins.unidade}</td>
        <td><input class="cell-edit" type="number" step="0.01" min="0" value="${ins.custo_compra||0}"
            placeholder="0,00" onblur="salvarCusto(${ins.id},this,'custo')" onkeydown="if(event.key==='Enter')this.blur();if(event.key==='Escape')this.value='${ins.custo_compra||0}'"></td>
        <td><input class="cell-edit" type="number" step="0.01" min="0.01" max="1" value="${ins.fator_rendimento||1}"
            placeholder="0-1" title="Fator de rendimento: 0.72 = perde 28% no preparo"
            onblur="salvarCusto(${ins.id},this,'rend')" onkeydown="if(event.key==='Enter')this.blur()"></td>
        <td><input class="cell-edit" type="number" step="0.1" min="0" value="${ins.estoque_atual||0}"
            onblur="salvarCusto(${ins.id},this,'estoque')" onkeydown="if(event.key==='Enter')this.blur()"></td>
        <td><input class="cell-edit" type="number" step="0.1" min="0" value="${ins.estoque_minimo||0}"
            style="${alerta?'color:#f59e0b':''}"
            onblur="salvarCusto(${ins.id},this,'minimo')" onkeydown="if(event.key==='Enter')this.blur()"></td>
        <td><span class="badge ${ok?'badge-ok':'badge-pend'}">${ins.status_cadastro}</span></td>
        <td>
          <button onclick="deletarInsumo(${ins.id},'${ins.nome}')" style="padding:4px 8px;border-radius:6px;border:none;background:rgba(239,68,68,0.1);color:#ef4444;cursor:pointer;font-size:11px;">Remover</button>
        </td>
      </tr>`;
    }).join('');
  }).join('');
}

async function salvarCusto(id, el, campo) {
  const val = parseFloat(el.value);
  if(isNaN(val)) return;
  const payload = {};
  if(campo==='custo') payload.custo_compra = val;
  else if(campo==='rend') payload.fator_rendimento = val;
  else if(campo==='estoque') payload.estoque_atual = val;
  else if(campo==='minimo') payload.estoque_minimo = val;
  try {
    const res = await fetch(API+'/insumos/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const d = await res.json();
    if(d.ok){ toast('Salvo!','ok'); await carregarInsumos(); }
    else toast(d.erro||'Erro','err');
  } catch(e){ toast('API offline','err'); }
}

async function deletarInsumo(id, nome) {
  if(!confirm(`Remover "${nome}"? Nao sera possivel se estiver em fichas tecnicas.`)) return;
  const res = await fetch(API+'/insumos/'+id,{method:'DELETE'});
  const d = await res.json();
  if(d.ok){ toast('Removido.','ok'); carregarInsumos(); }
  else toast(d.erro,'err');
}

// Modal novo insumo
function abrirModalNovoInsumo() { document.getElementById('modal-ni').style.display='flex'; }
function fecharModalNovoInsumo() { document.getElementById('modal-ni').style.display='none'; }
async function salvarNovoInsumo() {
  const nome = document.getElementById('ni-nome').value.trim();
  if(!nome){ toast('Nome obrigatorio.','err'); return; }
  const res = await fetch(API+'/insumos',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({nome,categoria:document.getElementById('ni-cat').value,
      unidade:document.getElementById('ni-unidade').value,
      custo_compra:parseFloat(document.getElementById('ni-custo').value)||0,
      fator_rendimento:parseFloat(document.getElementById('ni-rend').value)||1,
      estoque_minimo:parseFloat(document.getElementById('ni-min').value)||0})});
  const d = await res.json();
  if(d.ok){ fecharModalNovoInsumo(); carregarInsumos(); toast('Insumo criado!','ok'); }
  else toast(d.erro,'err');
}

// Importação XLSX
function baixarTemplate() { window.location.href = API+'/insumos/exportar-template'; }

async function uploadXlsx(input) {
  if(!input.files[0]) return;
  const fd = new FormData();
  fd.append('arquivo', input.files[0]);
  input.value='';
  try {
    const res = await fetch(API+'/insumos/importar-custos',{method:'POST',body:fd});
    const d = await res.json();
    if(!d.ok){ toast(d.erro,'err'); return; }
    previewData = d.preview;
    document.getElementById('preview-info').textContent =
      `${d.total} insumos encontrados no arquivo. Erros: ${d.erros.length}. Confirme para aplicar.`;
    document.getElementById('preview-body').innerHTML =
      `<table style="width:100%;font-size:13px;">
        <thead><tr><th style="text-align:left;padding:6px;color:var(--muted)">Insumo</th>
        <th style="text-align:right;padding:6px;color:var(--muted)">Custo</th>
        <th style="text-align:right;padding:6px;color:var(--muted)">Rendimento</th></tr></thead>
        <tbody>${d.preview.slice(0,20).map(p=>`<tr>
          <td style="padding:5px 6px">${p.nome}</td>
          <td style="text-align:right;padding:5px 6px;color:var(--primary)">R$ ${p.custo.toFixed(2)}</td>
          <td style="text-align:right;padding:5px 6px;color:var(--muted)">${p.rendimento}</td>
        </tr>`).join('')}
        ${d.preview.length>20?`<tr><td colspan="3" style="padding:5px 6px;color:var(--muted)">... e mais ${d.preview.length-20} itens</td></tr>`:''}
        </tbody></table>`;
    document.getElementById('painel-preview').style.display='block';
    lucide.createIcons();
  } catch(e){ toast('Erro no upload.','err'); }
}

function cancelarImport() { document.getElementById('painel-preview').style.display='none'; previewData=[]; }

async function confirmarImport() {
  if(!previewData.length) return;
  const res = await fetch(API+'/insumos/confirmar-custos',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({atualizacoes:previewData})});
  const d = await res.json();
  if(d.ok){ toast(`${d.atualizados} insumos atualizados!`,'ok'); cancelarImport(); carregarInsumos(); }
  else toast(d.erro,'err');
}

function toast(msg,tipo) {
  const el=document.getElementById('toast');
  el.textContent=msg; el.className=`toast ${tipo}`; el.style.display='block';
  setTimeout(()=>el.style.display='none',3000);
}

carregarInsumos();
</script>
</body>
</html>"""
with open('insumos.html','w',encoding='utf-8') as f:
    f.write(html)
print('OK - insumos.html criado com sucesso')
