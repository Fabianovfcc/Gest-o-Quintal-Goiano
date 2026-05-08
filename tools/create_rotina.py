H=open('insumos.html',encoding='utf-8').read()
# Build rotina.html by replacing key sections from insumos.html
r=H
r=r.replace('<title>Insumos — CMV Quintal Goiano</title>','<title>Rotina — CMV Quintal Goiano</title>')
r=r.replace('insumos.html" class="nav-item active"','insumos.html" class="nav-item"')
r=r.replace('dashboard.html" class="nav-item"','dashboard.html" class="nav-item active"')
# Replace main content
old_main=r[r.index('<main'):r.index('</main>')+7]
new_main="""<main class="main">
<div style="font-size:26px;font-weight:700;margin-bottom:4px;">Rotina Diária</div>
<div style="color:#94a3b8;font-size:14px;margin-bottom:24px;">Operação do dia — Compras, Desperdício e KPIs</div>

<!-- KPIs -->
<div id="kpis-row" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px;margin-bottom:24px;"></div>

<!-- Lista de Compras -->
<div class="glass" style="margin-bottom:24px;">
  <div style="padding:20px 24px;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between;align-items:center;">
    <div style="font-size:18px;font-weight:700;">Lista de Compras do Dia</div>
    <button class="btn btn-ghost" onclick="gerarLista()" style="font-size:12px;padding:7px 14px;"><i data-lucide="refresh-cw" size="13"></i> Atualizar</button>
  </div>
  <div id="lista-body" style="padding:20px 24px;"></div>
</div>

<!-- Registrar Compra -->
<div class="glass" style="margin-bottom:24px;">
  <div style="padding:20px 24px;border-bottom:1px solid rgba(255,255,255,0.06);">
    <div style="font-size:18px;font-weight:700;">Registrar Compra</div>
    <div style="color:#94a3b8;font-size:13px;margin-top:4px;">Foto, XML ou manual — sistema atualiza custo e estoque automaticamente</div>
  </div>
  <div style="padding:20px 24px;">
    <div style="display:flex;gap:8px;margin-bottom:16px;">
      <button class="btn btn-ghost" id="tab-foto" onclick="showTab('foto')" style="font-size:12px;">📷 Foto da Nota</button>
      <button class="btn btn-ghost" id="tab-xml" onclick="showTab('xml')" style="font-size:12px;">📄 XML NF-e</button>
      <button class="btn btn-ghost" id="tab-manual" onclick="showTab('manual')" style="font-size:12px;">✏️ Manual</button>
    </div>
    <div id="pane-foto">
      <div id="drop-zone" onclick="document.getElementById('foto-input').click()" style="border:2px dashed rgba(245,158,11,0.4);border-radius:12px;padding:32px;text-align:center;cursor:pointer;transition:all 0.2s;" ondragover="event.preventDefault();this.style.borderColor='#f59e0b'" ondragleave="this.style.borderColor='rgba(245,158,11,0.4)'" ondrop="dropFoto(event)">
        <div style="font-size:32px;margin-bottom:8px;">📷</div>
        <div style="color:#f8fafc;font-weight:600;">Arraste a foto da nota aqui</div>
        <div style="color:#94a3b8;font-size:13px;margin-top:4px;">ou clique para selecionar (jpg, png, webp)</div>
        <input type="file" id="foto-input" accept="image/*" style="display:none" onchange="enviarFoto(this)">
      </div>
      <div id="ocr-result" style="display:none;margin-top:16px;"></div>
    </div>
    <div id="pane-xml" style="display:none;">
      <input type="file" id="xml-input" accept=".xml" style="display:block;margin-bottom:12px;background:#334155;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:10px;color:#f8fafc;width:100%">
      <button class="btn btn-primary" onclick="uploadXml()"><i data-lucide="upload"></i> Processar XML</button>
    </div>
    <div id="pane-manual" style="display:none;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
        <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Fornecedor</div>
        <select id="man-forn" class="field-input"></select></div>
        <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Data</div>
        <input type="date" id="man-data" class="field-input"></div>
      </div>
      <div id="man-linhas"></div>
      <button class="btn btn-ghost" style="margin-top:8px;font-size:12px;" onclick="addLinhaManual()">+ Adicionar Item</button>
    </div>
  </div>
</div>

<!-- Desperdício -->
<div class="glass">
  <div style="padding:20px 24px;border-bottom:1px solid rgba(255,255,255,0.06);">
    <div style="font-size:18px;font-weight:700;">Sobras do Dia</div>
    <div style="color:#94a3b8;font-size:13px;margin-top:4px;">Registre o que sobrou — o sistema calcula o custo automaticamente</div>
  </div>
  <div style="padding:20px 24px;">
    <div style="display:flex;gap:8px;margin-bottom:16px;">
      <button class="btn btn-ghost" id="tab-prato" onclick="showDesp('prato')" style="font-size:12px;">🍽️ Por Prato</button>
      <button class="btn btn-ghost" id="tab-ins" onclick="showDesp('ins')" style="font-size:12px;">🧂 Por Ingrediente</button>
    </div>
    <div id="desp-prato">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
        <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Prato</div>
        <select id="dp-prato" class="field-input" onchange="previewDesp()"><option value="">Selecione...</option></select></div>
        <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Porções sobradas</div>
        <input type="number" id="dp-qtd" class="field-input" min="1" step="1" placeholder="0" oninput="previewDesp()"></div>
      </div>
      <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Motivo</div>
      <select id="dp-motivo" class="field-input"><option>sobra_producao</option><option>vencimento</option><option>acidente</option><option>outro</option></select></div>
      <div id="desp-preview" style="margin:12px 0;padding:12px;background:rgba(239,68,68,0.05);border-radius:8px;border:1px solid rgba(239,68,68,0.1);display:none;"></div>
      <button class="btn btn-primary" style="margin-top:12px;" onclick="registrarDespPrato()"><i data-lucide="check"></i> Registrar Perda</button>
    </div>
    <div id="desp-ins" style="display:none;">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;">
        <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Ingrediente</div>
        <select id="di-ins" class="field-input" onchange="previewDespIns()"><option value="">Selecione...</option></select></div>
        <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Quantidade</div>
        <input type="number" id="di-qtd" class="field-input" step="0.1" min="0" placeholder="0" oninput="previewDespIns()"></div>
        <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Unidade</div>
        <div id="di-unidade" class="field-input" style="background:#0f172a;color:#94a3b8;">—</div></div>
      </div>
      <div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Motivo</div>
      <select id="di-motivo" class="field-input"><option>sobra_producao</option><option>vencimento</option><option>acidente</option><option>outro</option></select></div>
      <div id="desp-ins-preview" style="margin:12px 0;color:#f59e0b;font-size:13px;"></div>
      <button class="btn btn-primary" style="margin-top:12px;" onclick="registrarDespIns()"><i data-lucide="check"></i> Registrar Perda</button>
    </div>
    <div style="margin-top:20px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:13px;font-weight:600;margin-bottom:10px;">Registrado Hoje</div>
      <div id="hist-hoje"></div>
    </div>
  </div>
</div>
</main>"""
r=r.replace(old_main, new_main)

# Replace script section
old_script=r[r.rindex('<script>')+8:r.rindex('</script>')]
new_script="""
const API='http://localhost:5000/api';
lucide.createIcons();
let todosInsumos=[], todosPratos=[];

async function init(){
  await carregarKpis(); await carregarLista();
  await carregarPratos(); await carregarInsumos();
  await carregarFornecedores(); carregarHistHoje();
  const hoje=new Date().toISOString().split('T')[0];
  const el=document.getElementById('man-data');
  if(el) el.value=hoje;
}

async function carregarKpis(){
  try{
    const d=await fetch(API+'/rotina/kpis').then(r=>r.json());
    const kpis=[
      {label:'Pedidos Hoje',val:d.pedidos_hoje||0,icon:'shopping-bag',color:'#f59e0b'},
      {label:'Faturamento',val:'R$ '+(d.faturamento_hoje||0).toFixed(2),icon:'dollar-sign',color:'#10b981'},
      {label:'CMV Hoje',val:d.cmv_hoje!=null?d.cmv_hoje+'%':'—',icon:'percent',color:d.cmv_hoje>35?'#ef4444':'#10b981'},
      {label:'Desperdício',val:'R$ '+(d.desperdicio_hoje||0).toFixed(2),icon:'trash-2',color:'#94a3b8'},
      {label:'Críticos',val:d.insumos_criticos||0,icon:'alert-triangle',color:d.insumos_criticos>0?'#ef4444':'#10b981'},
    ];
    document.getElementById('kpis-row').innerHTML=kpis.map(k=>
      `<div style="background:rgba(30,41,59,0.7);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:18px;">
        <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">${k.label}</div>
        <div style="font-size:22px;font-weight:700;color:${k.color};">${k.val}</div>
      </div>`
    ).join('');
  }catch(e){document.getElementById('kpis-row').innerHTML='<div style="color:#94a3b8;font-size:13px;">API offline</div>';}
}

async function carregarLista(){
  try{
    const d=await fetch(API+'/lista-compras/hoje').then(r=>r.json());
    const el=document.getElementById('lista-body');
    if(!d.itens||!d.itens.length){
      el.innerHTML='<div style="color:#94a3b8;font-size:13px;">Aguardando histórico de consumo (mínimo 1 dia de vendas processadas).</div>';
      return;
    }
    el.innerHTML=`<div style="margin-bottom:10px;font-size:13px;color:#94a3b8;">Custo estimado: <strong style="color:#f59e0b">R$ ${(d.custo_total_estimado||0).toFixed(2)}</strong></div>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead><tr><th style="text-align:left;padding:8px;color:#94a3b8;font-size:11px;">Insumo</th><th style="padding:8px;color:#94a3b8;font-size:11px;">Qtd</th><th style="padding:8px;color:#94a3b8;font-size:11px;">Fornecedor</th><th style="padding:8px;color:#94a3b8;font-size:11px;">Preço Est.</th><th style="padding:8px;color:#94a3b8;font-size:11px;">Dias Rest.</th><th style="padding:8px;"></th></tr></thead>
    <tbody>${d.itens.map(i=>{
      const dc=i.dias_restantes<1?'#ef4444':i.dias_restantes<2?'#f59e0b':'#10b981';
      return `<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
        <td style="padding:8px;font-weight:500;">${i.insumo_nome}</td>
        <td style="padding:8px;">${(i.quantidade_sugerida||i.quantidade||0).toFixed(2)} ${i.unidade}</td>
        <td style="padding:8px;color:#94a3b8;">${i.fornecedor_nome||'—'}</td>
        <td style="padding:8px;color:#f59e0b;">R$ ${(i.preco_estimado||0).toFixed(2)}</td>
        <td style="padding:8px;color:${dc};font-weight:600;">${(i.dias_restantes||0).toFixed(1)}d</td>
        <td style="padding:8px;">
          <button onclick="marcarComprado(${i.id})" style="padding:4px 8px;border-radius:6px;border:none;background:rgba(16,185,129,0.1);color:#10b981;cursor:pointer;font-size:11px;">✓</button>
        </td>
      </tr>`;
    }).join('')}</tbody></table>`;
  }catch(e){document.getElementById('lista-body').innerHTML='<div style="color:#94a3b8;font-size:13px;">Erro ao carregar lista.</div>';}
}

async function gerarLista(){
  toast('Gerando lista...','ok');
  await fetch(API+'/lista-compras/gerar');
  carregarLista();
}

async function marcarComprado(id){
  await fetch(API+'/lista-compras/'+id+'/status',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:'comprado'})});
  carregarLista();
}

function showTab(t){
  ['foto','xml','manual'].forEach(x=>{
    document.getElementById('pane-'+x).style.display=x===t?'block':'none';
  });
}
showTab('foto');

function showDesp(t){
  document.getElementById('desp-prato').style.display=t==='prato'?'block':'none';
  document.getElementById('desp-ins').style.display=t==='ins'?'block':'none';
}

function dropFoto(e){
  e.preventDefault();
  const f=e.dataTransfer.files[0];
  if(f) enviarFotoFile(f);
}
async function enviarFoto(input){
  if(input.files[0]) await enviarFotoFile(input.files[0]);
}
async function enviarFotoFile(file){
  const el=document.getElementById('ocr-result');
  el.style.display='block';
  el.innerHTML='<div style="color:#94a3b8;">🔄 Lendo nota...</div>';
  const fd=new FormData(); fd.append('arquivo',file);
  try{
    const r=await fetch(API+'/ocr/nota',{method:'POST',body:fd});
    const d=await r.json();
    if(!d.ok){el.innerHTML=`<div style="color:#ef4444;">${d.detalhe||d.erro}</div>`;return;}
    el.innerHTML=`<div style="font-size:13px;margin-bottom:8px;color:#94a3b8;">${d.total} itens encontrados</div>
    <table style="width:100%;font-size:13px;border-collapse:collapse;">
    <thead><tr><th style="text-align:left;padding:6px;color:#94a3b8;font-size:11px;">Produto (nota)</th><th style="padding:6px;color:#94a3b8;font-size:11px;">Qtd</th><th style="padding:6px;color:#94a3b8;font-size:11px;">Valor</th><th style="padding:6px;color:#94a3b8;font-size:11px;">Insumo</th></tr></thead>
    <tbody>${d.itens.map(i=>`<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
      <td style="padding:6px;">${i.descricao_nf}</td>
      <td style="padding:6px;">${i.quantidade_bruta} ${i.unidade_nf}</td>
      <td style="padding:6px;color:#f59e0b;">R$ ${(i.valor_total||0).toFixed(2)}</td>
      <td style="padding:6px;color:${i.insumo_id?'#10b981':'#f59e0b'}">${i.nome||'⚠ Não identificado'}</td>
    </tr>`).join('')}</tbody></table>`;
  }catch(e){el.innerHTML='<div style="color:#ef4444;">Erro no OCR.</div>';}
}

function uploadXml(){toast('Use a tela Notas Fiscais para importar XML.','ok');}

async function carregarPratos(){
  const d=await fetch(API+'/pratos').then(r=>r.json());
  todosPratos=d;
  const sel=document.getElementById('dp-prato');
  sel.innerHTML='<option value="">Selecione...</option>'+d.map(p=>`<option value="${p.id}">${p.nome}</option>`).join('');
}

async function carregarInsumos(){
  const d=await fetch(API+'/insumos').then(r=>r.json());
  todosInsumos=d;
  const sel=document.getElementById('di-ins');
  sel.innerHTML='<option value="">Selecione...</option>'+d.map(i=>`<option value="${i.id}" data-un="${i.unidade}" data-custo="${i.custo_compra||0}">${i.nome}</option>`).join('');
}

async function carregarFornecedores(){
  const d=await fetch(API+'/fornecedores').then(r=>r.json());
  const sel=document.getElementById('man-forn');
  if(sel) sel.innerHTML=d.map(f=>`<option value="${f.id}">${f.nome}</option>`).join('');
}

async function previewDesp(){
  const pid=document.getElementById('dp-prato').value;
  const qtd=parseFloat(document.getElementById('dp-qtd').value)||0;
  const el=document.getElementById('desp-preview');
  if(!pid||!qtd){el.style.display='none';return;}
  const d=await fetch(API+'/pratos/'+pid+'/ficha').then(r=>r.json());
  const custo=(d.custo_total||0)*qtd;
  el.style.display='block';
  el.innerHTML=`<div style="font-size:13px;margin-bottom:6px;color:#94a3b8;">${d.ingredientes?.length||0} ingredientes serão baixados</div><div style="font-size:16px;font-weight:700;color:#ef4444;">Custo estimado: R$ ${custo.toFixed(2)}</div>`;
}

function previewDespIns(){
  const sel=document.getElementById('di-ins');
  const opt=sel.options[sel.selectedIndex];
  const un=opt?.dataset?.un||'—';
  const custo=parseFloat(opt?.dataset?.custo)||0;
  const qtd=parseFloat(document.getElementById('di-qtd').value)||0;
  document.getElementById('di-unidade').textContent=un;
  document.getElementById('desp-ins-preview').textContent=
    custo>0&&qtd>0?`Custo estimado: R$ ${(custo*qtd).toFixed(2)}`:'';
}

async function registrarDespPrato(){
  const pid=document.getElementById('dp-prato').value;
  const qtd=parseFloat(document.getElementById('dp-qtd').value)||0;
  if(!pid||!qtd){toast('Preencha prato e quantidade.','err');return;}
  const r=await fetch(API+'/desperdicio/por-prato',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({prato_id:pid,quantidade_porcoes:qtd,motivo:document.getElementById('dp-motivo').value})});
  const d=await r.json();
  if(d.ok){toast(`Perda registrada — R$ ${(d.custo_total||0).toFixed(2)}`,'ok');document.getElementById('dp-qtd').value='';document.getElementById('desp-preview').style.display='none';carregarHistHoje();carregarKpis();}
  else toast(d.erro,'err');
}

async function registrarDespIns(){
  const ins=document.getElementById('di-ins').value;
  const qtd=parseFloat(document.getElementById('di-qtd').value)||0;
  if(!ins||!qtd){toast('Preencha ingrediente e quantidade.','err');return;}
  const r=await fetch(API+'/desperdicio/por-insumo',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({insumo_id:ins,quantidade:qtd,motivo:document.getElementById('di-motivo').value})});
  const d=await r.json();
  if(d.ok){toast(`R$ ${(d.custo_estimado||0).toFixed(2)} registrado`,'ok');document.getElementById('di-qtd').value='';carregarHistHoje();carregarKpis();}
  else toast(d.erro,'err');
}

async function carregarHistHoje(){
  try{
    const d=await fetch(API+'/rotina/perdas-hoje').then(r=>r.json());
    const total=d.reduce((s,p)=>s+(p.custo_estimado||0),0);
    const el=document.getElementById('hist-hoje');
    el.innerHTML=d.length?
      `<div style="margin-bottom:8px;font-size:13px;color:#ef4444;">Total: R$ ${total.toFixed(2)}</div>`+
      d.map(p=>`<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:13px;">
        <span>${p.insumo_nome||'Prato'} — ${p.quantidade} ${p.insumo_nome?'un':'porções'}</span>
        <span style="color:#ef4444;">R$ ${(p.custo_estimado||0).toFixed(2)}
          <button onclick="estornar(${p.id})" style="margin-left:8px;padding:2px 6px;border-radius:4px;border:none;background:rgba(239,68,68,0.1);color:#ef4444;cursor:pointer;font-size:10px;">↩</button>
        </span></div>`).join('')
      :'<div style="color:#94a3b8;font-size:13px;">Nenhuma perda registrada hoje.</div>';
  }catch(e){}
}

async function estornar(id){
  if(!confirm('Estornar esta perda?'))return;
  const r=await fetch(API+'/desperdicio/'+id,{method:'DELETE'});
  const d=await r.json();
  if(d.ok){toast('Estornado.','ok');carregarHistHoje();carregarKpis();}
  else toast(d.erro,'err');
}

function addLinhaManual(){
  const c=document.getElementById('man-linhas');
  const i=document.createElement('div');
  i.style.cssText='display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:8px;margin-bottom:8px;';
  i.innerHTML=`<select class="field-input"><option value="">Insumo...</option>${todosInsumos.map(x=>`<option value="${x.id}">${x.nome}</option>`).join('')}</select>
  <input type="number" class="field-input" placeholder="Qtd" step="0.1">
  <input type="number" class="field-input" placeholder="R$/un" step="0.01">
  <button onclick="this.parentElement.remove()" style="padding:6px 10px;border-radius:6px;border:none;background:rgba(239,68,68,0.1);color:#ef4444;cursor:pointer;">✕</button>`;
  c.appendChild(i);
}

function toast(msg,tipo){
  const el=document.getElementById('toast')||Object.assign(document.createElement('div'),{id:'toast'});
  if(!el.parentElement)document.body.appendChild(el);
  Object.assign(el.style,{position:'fixed',bottom:'24px',right:'24px',padding:'14px 20px',borderRadius:'12px',fontWeight:'600',fontSize:'14px',zIndex:'999',background:tipo==='ok'?'#10b981':'#ef4444',color:'#fff',display:'block'});
  el.textContent=msg;
  setTimeout(()=>el.style.display='none',3000);
}

init();
"""
r=r.replace(old_script, new_script)
r=r.replace('<title>Insumos — CMV Quintal Goiano</title>','<title>Rotina — CMV Quintal Goiano</title>')
open('rotina.html','w',encoding='utf-8').write(r)
print('OK rotina.html criado')
