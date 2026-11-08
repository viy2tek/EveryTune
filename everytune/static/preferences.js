import uiPolicy from './ui-policy.mjs';

(() => {
  let editingId = null, auditOffset = 0, auditTotal = 0, customDefinitions = [];
  const panels = ['preferences','sources','custom','coverage','audit','profiles'];
  function showPanel(name) {
    for (const panel of panels) $('panel-'+panel).hidden = panel !== name;
    for (const button of document.querySelectorAll('[data-panel]')) { button.classList.toggle('active',button.dataset.panel===name); button.setAttribute('aria-pressed',String(button.dataset.panel===name)); }
    $('settings-form').hidden = !['preferences','sources'].includes(name);
    if (name==='audit') loadAudit();
    if (name==='coverage') window.loadCoverage?.();
  }
  window.showSettingsPanel = showPanel;
  for (const button of document.querySelectorAll('[data-panel]')) button.addEventListener('click',()=>showPanel(button.dataset.panel));
  window.applyPreferences = () => {
    const dark = settings.theme==='dark' || (settings.theme==='system' && matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    $('results').classList.toggle('results-grid',settings.view==='grid');
  };
  window.renderPreferenceFields = () => {
    $('pref-scope').value=settings.provider_scope || 'both'; $('pref-download-limit').value=settings.download_max_mb || 2048; $('pref-theme').value=settings.theme || 'light'; $('pref-view').value=settings.view || 'list'; $('pref-country').value=settings.country || 'BR'; $('pref-mode').value=settings.default_mode || 'auto';
    $('pref-artwork').checked=settings.show_artwork!==false; $('pref-credits').checked=settings.show_credits!==false; $('pref-album').checked=settings.show_album!==false;
    $('pref-exclude-covers').checked=settings.exclude_covers!==false;
    const format=settings.download_format || '';
    if(format && ![...$('pref-download-format').options].some(o=>o.value===format)) $('pref-download-format').append(new Option(format,format));
    $('pref-download-format').value=format;$('pref-download-pack').value=settings.download_pack || 'zip';$('pref-download-images').checked=settings.download_images===true;
  };
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>window.applyPreferences());
  document.addEventListener('everytune:ready',()=>{window.applyPreferences();window.renderPreferenceFields();});
  if (settings.max_results) {window.applyPreferences();window.renderPreferenceFields();}
  async function reload() {
    [settings,catalogue,customDefinitions] = await Promise.all(['/api/settings','/api/sources','/api/custom-sources'].map(async path=>(await api(path)).json()));
    selected=new Set(catalogue.filter(s=>s.enabled).map(s=>s.id));$('provider-scope').value=settings.provider_scope || 'both';renderSources();renderSettings();window.applyPreferences();
    if (activeQuery) renderResults();
  }
  function fillSource(source) {
    editingId=source.id || null;
    $('source-group').value=source.provider_group || 'community'; $('source-download-selector').value=source.download_selector || ''; $('source-encoding').value=source.request_encoding || 'form'; $('source-method').value=source.method || 'GET'; $('source-name').value=source.name || ''; $('source-format').value=source.format || 'json'; $('source-endpoint').value=source.endpoint || ''; $('source-query-param').value=source.query_param || 'q'; $('source-results-path').value=source.results_path ?? 'results';
    $('source-field-title').value=source.fields?.title ?? 'title';$('source-field-artist').value=source.fields?.artist ?? 'artist';$('source-field-url').value=source.fields?.url ?? 'url';$('source-category').value=source.category || 'Personalizadas';$('source-auth').value=source.auth || 'none';$('source-auth-name').value=source.auth_name || 'Authorization';
    const advanced={...source};
    for (const key of ['id','name','format','method','request_encoding','provider_group','download_selector','endpoint','query_param','results_path','category','auth','auth_name']) delete advanced[key];
    if (advanced.fields) {advanced.fields={...advanced.fields};for (const key of ['title','artist','url']) delete advanced.fields[key];}
    $('source-advanced').value=JSON.stringify(advanced,null,2);$('source-save-status').textContent=editingId ? 'Editando conector existente.' : 'Nova fonte.';
    updateEditor();
  }
  function updateEditor() {
    const format=({external:0,json:1,html:2})[$('source-format').value];
    const mapping=uiPolicy.mapping(format)===1;
    const fields=['source-method','source-auth','source-results-path','source-field-title','source-field-artist','source-field-url','source-download-selector'];
    for (const id of fields) {
      const field=$(id), visible=mapping;
      field.disabled=!visible;field.closest('label').hidden=!visible;
    }
    for (const [id,visible] of [['source-encoding',uiPolicy.post_body(format,Number($('source-method').value==='POST'))===1],['source-auth-name',uiPolicy.auth_name(format,Number($('source-auth').value!=='none'))===1]]) {
      $(id).disabled=!visible;$(id).closest('label').hidden=!visible;
    }
    $('source-advanced-help').textContent=mapping ? 'JSON declarativo para créditos, paginação, parâmetros fixos e outros campos. Nenhum código é executado. HTML: CSS para texto ou a@href para atributo; JSON: caminhos como tracks.items.' : 'JSON declarativo para parâmetros fixos (params) e pesquisa no caminho (query_in_path). O atalho usa GET e não recebe autenticação nem mapeamento de resultados.';
  }
  for (const id of ['source-format','source-method','source-auth']) $(id).addEventListener('change',updateEditor);
  updateEditor();
  window.editSource=async id=>{
    try {customDefinitions=await(await api('/api/custom-sources')).json();fillSource(customDefinitions.find(s=>s.id===id));showPanel('custom');$('source-name').focus();}
    catch(error){$('save-status').textContent=error.message;}
  };
  window.removeSource=async id=>{
    try {await api('/api/custom-sources/'+encodeURIComponent(id),{method:'DELETE'});await reload();$('save-status').textContent='Fonte removida. Você pode restaurar os padrões ou importar um perfil.';}
    catch(error){$('save-status').textContent=error.message;}
  };
  $('new-source').addEventListener('click',()=>fillSource({}));
  $('custom-source-form').addEventListener('submit',async event=>{
    event.preventDefault();$('source-save-status').textContent='Validando configuração…';
    try {
      const extra=JSON.parse($('source-advanced').value || '{}');
      if (!extra || Array.isArray(extra) || typeof extra!=='object') throw new Error('O mapeamento avançado deve ser um objeto JSON.');
      const fields={...(extra.fields || {}),title:$('source-field-title').value,url:$('source-field-url').value};
      if ($('source-field-artist').value) fields.artist=$('source-field-artist').value;
      const definition={...extra,id:editingId || 'custom_'+crypto.randomUUID().replaceAll('-','').slice(0,16),name:$('source-name').value,provider_group:$('source-group').value,download_selector:$('source-download-selector').value || null,format:$('source-format').value,method:$('source-method').value,request_encoding:$('source-encoding').value,endpoint:$('source-endpoint').value,query_param:$('source-query-param').value,results_path:$('source-results-path').value,category:$('source-category').value,auth:$('source-auth').value,auth_name:$('source-auth-name').value,fields};
      if (definition.format==='external') {definition.method='GET';definition.auth='none';definition.auth_name='Authorization';definition.download_selector=null;definition.fields={};definition.results_path='';definition.request_encoding='form';}
      if (definition.method==='GET') definition.request_encoding='form';
      if (definition.auth==='none') definition.auth_name='Authorization';
      const result=await(await api('/api/custom-sources',{method:'PUT',body:JSON.stringify(definition)})).json();editingId=result.id;await reload();$('source-save-status').textContent='Fonte salva. Em Fontes instaladas, ative e configure a chave se necessário. A primeira busca verificará a resposta.';
    } catch(error){$('source-save-status').textContent=error.message;}
  });
  const outcomeLabels={search_connector_validated:'Busca integrada e testada',html_inspected:'Página inspecionada',http_blocked:'Bloqueio HTTP',robots_disallowed:'Restrição robots',robots_unavailable:'Robots não verificável',network_error:'Falha de rede',timeout:'Tempo esgotado',non_html_resource:'Conteúdo não HTML',redirect_limit:'Redirecionamentos',http_error:'Erro HTTP',unsafe_destination:'Destino não público',not_a_direct_music_search:'Guia, comunidade ou índice',no_public_get_search_observed:'Busca pública não identificada',search_not_verified:'Formulário ainda não integrado',html_search_mapping_observed:'Mapeamento HTML observado',inspection_error:'Falha na inspeção'};
  async function loadAudit() {
    try {
      const query=new URLSearchParams({q:$('audit-query').value,outcome:$('audit-outcome').value,offset:String(auditOffset),limit:'40'});
      const data=await(await api('/api/source-audit?'+query)).json();auditTotal=data.matched;
      $('audit-summary').textContent=`${data.completed} de ${data.total} URLs avaliadas. ${data.complete ? 'Auditoria principal concluída.' : 'Auditoria parcial.'} Páginas e buscas observadas não equivalem a integração ou licença de uso.`;
      if ($('audit-outcome').options.length===1) for (const outcome of Object.keys(data.outcomes)) $('audit-outcome').append(new Option(outcomeLabels[outcome] || outcome,outcome));
      $('audit-list').replaceChildren();
      for (const source of data.sources) {
        const row=el('article','audit-row'), header=el('div');header.append(link(source.label || source.title || source.url,source.url),el('span','small muted',outcomeLabels[source.outcome] || source.outcome));
        row.append(header,el('p','small muted',`${source.section || ''} · ${source.url}`));
        if (source.reason) row.append(el('p','small',source.reason));
        if (source.preset_id && catalogue.some(s=>s.id===source.preset_id && s.provenance==='user')) {
          const edit=el('button','secondary','Editar conector disponível');edit.type='button';edit.addEventListener('click',()=>window.editSource(source.preset_id));row.append(edit);
        }
        if (source.get_search_forms?.length && !(source.preset_id && catalogue.some(s=>s.id===source.preset_id))) {
          row.append(el('p','small','Formulário GET observado. O parser dos resultados ainda precisa ser configurado e testado.'));
          const forms=[...new Map(source.get_search_forms.map(form=>[JSON.stringify([form.action,form.search_inputs?.[0],form.fixed_params]),form])).values()];
          for (const form of forms.slice(0,3)) {
            const button=el('button','secondary','Configurar esta busca');button.type='button';
            button.addEventListener('click',()=>{
              const action=form.action || form.url || source.url;
              const parsed=new URL(action,source.url);
              const fixed=Object.fromEntries(parsed.searchParams);parsed.search='';parsed.hash='';
              fillSource({name:source.label || source.title,format:'external',endpoint:parsed.href,query_param:form.query_name || form.query_param || form.search_param || form.search_inputs?.[0] || 'q',params:{...fixed,...(form.hidden_fields || form.fixed_params || {})},limit_param:null,category:source.section || 'Personalizadas'});
              showPanel('custom');
            });row.append(button);
          }
        }
        $('audit-list').append(row);
      }
      $('audit-page').textContent=`${auditTotal ? auditOffset+1 : 0}–${Math.min(auditOffset+40,auditTotal)} de ${auditTotal}`;$('audit-prev').disabled=auditOffset===0;$('audit-next').disabled=auditOffset+40>=auditTotal;
    }catch(error){$('audit-summary').textContent=error.message;}
  }
  $('audit-search').addEventListener('click',()=>{auditOffset=0;loadAudit();});$('audit-prev').addEventListener('click',()=>{auditOffset=Math.max(0,auditOffset-40);loadAudit();});$('audit-next').addEventListener('click',()=>{auditOffset+=40;loadAudit();});
  function download(name,data) {
    const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const anchor=document.createElement('a');anchor.href=url;anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  $('export-profile').addEventListener('click',async()=>{try {download('everytune-profile.json',await(await api('/api/profile')).json());$('profile-status').textContent='Perfil exportado sem credenciais.';}catch(error){$('profile-status').textContent=error.message;}});
  $('import-profile').addEventListener('change',async event=>{
    try {const file=event.target.files[0];if (!file) return;if (file.size>1_000_000) throw new Error('O perfil deve ter até 1 MB.');const data=JSON.parse(await file.text());await api('/api/profile',{method:'PUT',body:JSON.stringify(data)});await reload();$('profile-status').textContent='Perfil importado. As chaves não foram importadas.';}
    catch(error){$('profile-status').textContent=error.message;}finally{event.target.value='';}
  });
  $('reset-profile').addEventListener('click',()=>{$('reset-status').textContent='';$('reset-dialog').showModal();});
  $('reset-cancel').addEventListener('click',()=>$('reset-dialog').close());
  $('reset-backup').addEventListener('click',async()=>{try{download('everytune-antes-de-restaurar.json',await(await api('/api/profile')).json());$('reset-status').textContent='Cópia enviada ao navegador para salvar. Confira o arquivo antes de confirmar.';}catch(error){$('reset-status').textContent=error.message;}});
  $('reset-confirm').addEventListener('click',async()=>{
    $('reset-confirm').disabled=true;
    try {await api('/api/profile',{method:'DELETE'});await reload();$('reset-dialog').close();$('profile-status').textContent='Padrões restaurados. Credenciais de fontes personalizadas removidas da sessão.';}
    catch(error){$('reset-status').textContent=error.message;}
    finally{$('reset-confirm').disabled=false;}
  });
})();
