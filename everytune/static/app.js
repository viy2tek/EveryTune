const $ = id => document.getElementById(id);
const statusNames = {not_checked:'Não consultada',success:'Encontrou',choose_person:'Escolha a pessoa',unsupported:'Outro modo',no_match:'Sem correspondência',empty:'Sem resultados',timeout:'Tempo esgotado',rate_limit:'Limite atingido',missing_credentials:'Requer acesso',unavailable:'Indisponível',external:'Site externo',searching:'Buscando…'};
let catalogue = [], settings = {}, tracks = [], cursors = {}, activeQuery = '', controller = null;
let selected = new Set(), completed = 0, total = 0, activeSources = [], loadingMore = false;
let activeFields = {};
let searchEpoch=0;
let chosenIdentity = null, foundPeople = new Map(), sourceNotices = new Map();
const sourceDiagnostics=new Map();
const credentialClears = new Set();
const providerLabels={streaming:'Streaming · pagas e freemium',community:'Comunidade e acervos'};

function preserveFocus(root, fallback) {
  const active = document.activeElement;
  if (!root.contains(active)) return () => {};
  const key = active.dataset.focusKey;
  return () => {
    if (active.isConnected && document.activeElement === active) return;
    if (document.activeElement !== document.body && document.activeElement !== active) return;
    const replacement = key && [...root.querySelectorAll('[data-focus-key]')].find(n=>n.dataset.focusKey===key);
    (replacement || fallback)?.focus({preventScroll:true});
  };
}
function reconcileChildren(root, children) {
  for (const [index, child] of children.entries()) if (root.children[index] !== child) root.insertBefore(child,root.children[index] || null);
  const keep = new Set(children);
  for (const child of [...root.children]) if (!keep.has(child)) child.remove();
}
function setSearchOptions(open) {
  $('source-controls').hidden=!open;
  $('options-toggle').setAttribute('aria-expanded',String(open));
}
function renderSearchSummary() {
  const mode=({auto:0,track:1,credits:2,source:3})[$('search-mode').value];
  $('search-summary').textContent=Home.summary(mode,Number($('exclude-covers').checked));
}

function el(tag, cls, content) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (content !== undefined) node.textContent = content;
  return node;
}
async function api(path, options = {}) {
  const response = await fetch(path, {...options, headers:{'Content-Type':'application/json','X-EveryTune':'1',...options.headers}});
  if (!response.ok) {
    let message = `Falha HTTP ${response.status}. Tente novamente.`;
    try { const data = await response.json(); if (typeof data.detail === 'string') message = data.detail; else if (Array.isArray(data.detail)) message=data.detail.slice(0,3).map(e=>e.msg).join('; '); } catch {}
    throw new Error(message);
  }
  return response;
}
function showError(message) { $('error').textContent = message; $('error').hidden = !message; }
function link(text, url) {
  const node = el('a', '', text);
  if (url && new URL(url).protocol === 'https:') node.href = url;
  node.target = '_blank'; node.rel = 'noopener noreferrer';
  return node;
}
function setView(name) {
  $('search-view').hidden = name !== 'search'; $('settings-view').hidden = name !== 'settings';
  for (const view of ['search','settings']) {
    $('nav-'+view).classList.toggle('active', view === name);
    if (view === name) $('nav-'+view).setAttribute('aria-current','page'); else $('nav-'+view).removeAttribute('aria-current');
  }
  if (name === 'settings') renderSettings();
}
function renderSources() {
  const restoreFocus = preserveFocus($('source-list'),$('options-toggle'));
  $('source-list').replaceChildren();
  const scope=$('provider-scope').value;
  for (const group of ['streaming','community']) {
    if (scope!=='both' && scope!==group) continue;
    const section=el('section','provider-group');section.dataset.providerGroup=group;
    const heading=el('div','provider-heading');heading.append(el('h3','',providerLabels[group]));
    const actions=el('div','provider-actions');
    for (const [text,choose] of [['Todas',true],['Limpar',false]]) {
      const button=el('button','text-button',text);button.type='button';button.setAttribute('aria-label',`${text} de ${group==='streaming' ? 'streaming' : 'comunidade'}`);
      button.dataset.focusKey=`group:${group}:${choose}`;
      button.addEventListener('click',()=>{for (const source of catalogue.filter(s=>s.provider_group===group && s.enabled)) choose ? selected.add(source.id) : selected.delete(source.id);renderSources();});actions.append(button);
    }
    heading.append(actions);section.append(heading);
    for (const source of catalogue.filter(s=>s.mode==='api' && s.supports_files!==false && s.provider_group===group)) {
    const row = el('label','source-option'); row.dataset.source = source.id; row.dataset.status = source.health.status;
    const check = el('input'); check.type = 'checkbox'; check.checked = selected.has(source.id); check.disabled = !source.enabled;
    check.dataset.focusKey=`source:${source.id}`;
    check.addEventListener('change', () => {check.checked ? selected.add(source.id) : selected.delete(source.id);renderSourceCount();});
    const state = el('span','state', !source.enabled ? 'Desativada' : source.configured ? statusNames[source.health.status] : 'Requer acesso');
    row.append(check, el('span','source-name',source.name), state); section.append(row);
    }
    $('source-list').append(section);
  }
  renderSourceCount();
  restoreFocus();
}
function renderSourceCount() {
  const scope=$('provider-scope').value;
  const sources=catalogue.filter(s=>s.mode==='api' && s.supports_files!==false && s.enabled && selected.has(s.id) && (scope==='both' || s.provider_group===scope));
  const missing=sources.filter(s=>!s.configured).length;
  $('scope-summary').textContent=`${sources.length} fontes${missing ? ` · ${missing} precisam de acesso` : ''}`;
  renderSearchSummary();
}
$('provider-scope').addEventListener('change',()=>{settings.provider_scope=$('provider-scope').value;chosenIdentity=null;renderSources();});
function setSourceStatus(id, status, message) {
  const source = catalogue.find(s => s.id === id); if (source) source.health = {status};
  const row = document.querySelector(`[data-source="${id}"]`);
  if (row) { row.dataset.status = status; row.querySelector('.state').textContent = statusNames[status] || status; row.title = message || statusNames[status]; }
}
function renderSettings() {
  $('max-results').value = settings.max_results; $('concurrency').value = settings.concurrency; $('timeout').value = settings.timeout;
  $('settings-sources').replaceChildren(); credentialClears.clear();
  for (const source of catalogue) {
    const row = el('div','setting-source'), info = el('div'), control = el('div'), label = el('label');
    const check = el('input'); check.type = 'checkbox'; check.checked = source.enabled; check.dataset.enable = source.id;
    label.append(check, document.createTextNode(source.name)); info.append(label);
    info.append(el('p','',`${providerLabels[source.provider_group]} · ${source.category} · ${source.provenance === 'user' ? 'Conector configurável' : source.mode === 'api' ? 'Adaptador de catálogo' : 'Pesquisa no site externo'}`));
    if (source.docs) info.append(link('Documentação ↗',source.docs));
    control.append(el('p','',source.mode === 'external' ? 'Abre a pesquisa no catálogo original; não consulta faixas pela API.' : `Última consulta: ${statusNames[source.health.status] || source.health.status}. ${source.requires_credentials ? source.configured ? 'Credenciais configuradas.' : 'Credenciais ausentes.' : 'Acesso sem chave.'}`));
    for (const key of source.credentials) {
      const field = el('label','credential-field',key);
      const input = el('input'); input.type = 'password'; input.autocomplete = 'new-password'; input.dataset.credential = key; input.maxLength = 8192;
      input.placeholder = 'Novo valor — em branco preserva o atual';
      const clear = el('button','','Remover credencial'); clear.type = 'button';
      clear.setAttribute('aria-label',`Remover credencial ${key} — ${source.name}`);
      clear.addEventListener('click', () => { credentialClears.add(key); input.value = ''; input.placeholder = 'Será removida ao salvar'; clear.textContent = 'Remoção marcada'; });
      field.append(input,clear); control.append(field);
    }
    row.append(info,control); $('settings-sources').append(row);
    if (source.provenance === 'user') {
      const edit = el('button','secondary','Editar conector'); edit.type='button'; edit.addEventListener('click',()=>window.editSource?.(source.id));
      const remove = el('button','secondary','Remover'); remove.type='button'; remove.addEventListener('click',()=>window.removeSource?.(source.id)); control.append(edit,remove);
      edit.setAttribute('aria-label',`Editar conector — ${source.name}`);remove.setAttribute('aria-label',`Remover — ${source.name}`);
    }
  }
  window.renderPreferenceFields?.();
}
function options(id, values) {
  const current = $(id).value;
  $(id).replaceChildren(new Option('Todas',''));
  for (const value of [...new Set(values)].sort()) $(id).append(new Option(value,value));
  $(id).value = [...$(id).options].some(o=>o.value===current) ? current : '';
}
function renderDiagnostics() {
  const rows=[];
  for(const result of sourceDiagnostics.values()) {
    const row=el('div','source-diagnostic');row.append(el('strong','small',result.name));
    if(result.reason) row.append(el('p','small muted',result.reason==='external' ? 'Não consultada: atalho externo, sem retorno integrado de arquivos.' : 'Não consultada: conector de catálogo, sem exportação de áudio.'));
    else {
      row.append(el('p','small',`${statusNames[result.status] || result.status}${result.cached ? ' · metadados em cache; áudio reconferido' : ''}`));
      if(result.message) row.append(el('p','small muted',result.message));
      const d=result.diagnostics || {};
      const reasons=[['name_or_version',1],['no_audio',2],['audio_check_failed',3],['audio_check_timeout',4]].filter(([key])=>d[key]).map(([key,code])=>`${d[key]}: ${Home.diagnostic_label(code)}`);
      if(reasons.length) row.append(el('p','small muted',reasons.join(' · ')));
    }
    for(const notice of sourceNotices.get(result.source) || []) row.append(el('p','small muted',notice));
    rows.push(row);
  }
  $('source-notices').hidden=!rows.length;
  $('source-notices-summary').textContent=`Como foi a busca (${rows.length} fontes)`;
  $('source-notices-body').replaceChildren(...rows);
}
function renderResults() {
  document.querySelector('.results-area').hidden=!activeQuery;
  const inlinePanel=document.querySelector('#download-dialog.inline-downloads');
  const panelKey=inlinePanel?.closest('[data-result-key]')?.dataset.resultKey;
  const restoreFocus = preserveFocus($('results'),$('results-title'));
  const existing = new Map([...$('results').querySelectorAll(':scope > [data-result-key]')].map(n=>[n.dataset.resultKey,n]));
  const cards=[];
  const available=tracks.filter(t=>Home.audio_result(Number(t.audio_available===true))===1);
  options('filter-platform',available.map(t=>t.platform)); options('filter-category',available.map(t=>t.category));
  const roleValue = $('filter-role').value;
  $('filter-role').replaceChildren(new Option('Todos',''));
  for (const role of [...new Set(available.flatMap(t=>(t.credits || []).map(c=>c.role)))].sort()) $('filter-role').append(new Option(role,role));
  $('filter-role').value = [...$('filter-role').options].some(o=>o.value===roleValue) ? roleValue : '';
  const artist = $('filter-artist').value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const filtered = available.filter(t => (!$('filter-platform').value || t.platform === $('filter-platform').value) && (!$('filter-category').value || t.category === $('filter-category').value) && (!artist || (t.artist || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().includes(artist)) && (!$('filter-availability').value || t[$('filter-availability').value] === true) && (!$('filter-role').value || (t.credits || []).some(c=>c.role===$('filter-role').value)) && (!$('filter-kind').value || t.kind===$('filter-kind').value));
  const groups = new Map();
  for (const track of [...filtered].sort((a,b)=>b.score-a.score)) {
    const key = track.recording_group || track.group || `${track.source}:${track.source_id}`;
    if (!groups.has(key)) groups.set(key,[]); groups.get(key).push(track);
  }
  $('result-count').textContent = `${groups.size} resultados com áudio · ${filtered.length} origens`;
  for (const [key,group] of groups) {
    const signature=JSON.stringify([group,settings.show_artwork,settings.show_album,settings.show_credits]);
    if (existing.get(key)?.dataset.signature===signature) {cards.push(existing.get(key));continue;}
    const first = group[0], article = el('article','track-group'), main = el('div','track-main');
    article.dataset.resultKey=key;article.dataset.signature=signature;
    const imageTrack = group.find(t=>t.artwork);
    const placeholder = () => el('div','cover cover-placeholder',first.platform.substring(0,2).toUpperCase());
    if (settings.show_artwork !== false) {
      if (imageTrack) { const img = el('img','cover'); img.src = imageTrack.artwork; img.alt = ''; img.loading = 'lazy'; img.referrerPolicy = 'no-referrer'; img.addEventListener('error',()=>img.replaceWith(placeholder()),{once:true}); main.append(img); } else main.append(placeholder());
    }
    const info = el('div','track-info'); info.append(el('h3','',first.title), el('p','',first.artist || 'Artista não informado'));
    const extra = [first.album,first.year,first.duration ? `${Math.floor(first.duration/60)}:${String(Math.floor(first.duration%60)).padStart(2,'0')}` : null, first.kind === 'archive_item' ? 'Item de acervo' : first.kind === 'audio_file' ? 'Arquivo de áudio' : first.kind === 'video' ? 'Vídeo' : first.kind === 'mix' ? 'Mix / programa' : null].filter(Boolean).join(' · ');
    if (extra && settings.show_album !== false) info.append(el('p','',extra));
    main.append(info,el('span',first.matched_on==='source' ? 'match source-match' : 'match',Home.result_label(({source:1,artist_title:2,artist:3,title:4,album:5,credit:6,mention:7})[first.matched_on] || 0)));
    article.append(main); const origins = el('div','origins');
    if(group.length>1) origins.append(el('p','grouped-note',Home.grouped_note()));
    const details=el('details','result-details');details.append(el('summary','','Créditos e licença'));
    details.open=existing.get(key)?.querySelector('.result-details')?.open || false;
    for (const track of group) {
      const origin = el('div','origin'); origin.append(el('span','source-icon',track.platform.substring(0,2).toUpperCase()), link(`Abrir em ${track.platform} ↗`,track.url));
      origin.querySelector('a').dataset.focusKey=`origin:${track.source}:${track.source_id}`;
      if(track.audio_formats?.length) origin.append(el('small','',`Formatos listados: ${track.audio_formats.join(', ')}${track.audio_file_count ? ' · '+track.audio_file_count+' opções de áudio' : ''}`));
      if (Home.file_action(Number(track.file_access==='catalogue'),Number(Boolean(track.download_ref)))===1) {const files=el('button','text-button','Ver arquivos');files.type='button';files.dataset.focusKey=`files:${track.source}:${track.source_id}`;files.setAttribute('aria-label',`Ver arquivos — ${track.title} — ${track.platform}`);files.addEventListener('click',()=>window.showFiles(track.download_ref,track.title,article));origin.append(files);}
      if (track.file_access==='catalogue') origin.append(el('small','','Somente catálogo'));
      if (track.recording_type==='remix') origin.append(el('small','','Remix identificado no título'));
      if (track.recording_type==='cover') origin.append(el('small','','Cover identificado no título'));
      origins.append(origin);
      if (settings.show_credits !== false && track.credits?.length) {
        const credits = el('div','credit-list');
        for (const credit of track.credits) {
          const row = el('p','',`${credit.name} · ${credit.role}`);
          if (credit.evidence_url) { const evidence=link('Ver evidência ↗',credit.evidence_url);evidence.dataset.focusKey=`evidence:${track.source}:${track.source_id}:${credit.name}:${credit.role}:${credit.evidence_url}`;row.append(' ',evidence); }
          credits.append(row);
        }
        credits.prepend(el('strong','small',track.platform));details.append(credits);
      }
      if (track.license) details.append(el('p','license',`${track.platform} · ${track.license}`));
    }
    if(details.children.length>1) origins.append(details);
    article.append(origins); cards.push(article);
  }
  if (!groups.size) { const empty = el('div','empty'); empty.append(el('h3','',available.length ? 'Nenhum resultado com estes filtros.' : controller ? 'Verificando os nomes nas fontes…' : activeFields.mode==='source' ? 'Nenhum resultado retornado.' : 'Nenhum áudio disponível para download confirmado.'),el('p','',controller ? activeFields.mode==='source' ? 'Aguardando os resultados dos sites selecionados.' : 'Só serão exibidos resultados que atendam aos nomes informados.' : 'A faixa pode não estar indexada, faltar nos resultados recebidos ou ter metadados insuficientes. Confira os nomes e os estados das fontes; isso não prova que ela não existe.')); cards.push(empty); }
  reconcileChildren($('results'),cards);
  if(inlinePanel && !inlinePanel.isConnected) {
    const host=cards.find(n=>n.dataset.resultKey===panelKey);
    if(host) host.append(inlinePanel);
    else {document.body.append(inlinePanel);inlinePanel.close();}
  }
  restoreFocus();
  $('filters').hidden = !available.length;
  $('results').classList.toggle('results-grid',settings.view==='grid');
}
function renderExternal(items) {
  $('external').hidden = !items.length; $('external-count').textContent = `(${items.length})`;
  $('external-links').replaceChildren(...items.map(item=>link(item.name+' ↗',item.url)));
}
async function history() {
  const items = await (await api('/api/history')).json();
  $('history').replaceChildren();
  if (items.length) $('history').append(el('span','small muted','Recentes'));
  for (const q of items.slice(0,3)) { const button = el('button','',q); button.type = 'button'; button.addEventListener('click',()=>startQuery(q)); $('history').append(button); }
}
function startQuery(query) { chosenIdentity=null; $('query').value = query; $('search-artist').value = ''; $('search-title').value = ''; $('search-form').requestSubmit(); }
function renderPeople() {
  const restoreFocus=preserveFocus($('people'),$('results-title'));
  $('people').hidden = !foundPeople.size; $('people').replaceChildren();
  if (!foundPeople.size) {restoreFocus();return;}
  $('people').append(el('h3','','Confira a identidade antes de reunir os créditos'));
  for (const person of foundPeople.values()) {
    const row = el('div','person-row'), info = el('div'); info.append(link(person.name+' ↗',person.url),el('p','small muted',`${person.source} · ${person.disambiguation || 'Identidade de catálogo'}`));
    info.querySelector('a').dataset.focusKey=`person-link:${person.source}:${person.id}`;
    const choose = el('button','secondary','Ver créditos desta identidade'); choose.type='button';
    choose.dataset.focusKey=`person:${person.source}:${person.id}`;choose.setAttribute('aria-label',`Ver créditos desta identidade — ${person.name} — ${person.source}`);
    choose.addEventListener('click',()=>{ chosenIdentity=person; $('query').value=person.name; $('search-artist').value=''; $('search-title').value=''; $('search-mode').value='credits';$('provider-scope').value=catalogue.find(s=>s.id===person.source)?.provider_group || 'both';selected.add(person.source);renderSources();search(); });
    row.append(info,choose); $('people').append(row);
  }
  restoreFocus();
}
function handleEvent(event) {
  if (event.type === 'start') {
    total = event.total; completed = 0; $('progress').max = total || 1; if (!loadingMore) renderExternal(event.external);
    for(const result of event.skipped || []) sourceDiagnostics.set(result.source,result);
    renderDiagnostics();
    const terms = event.interpretation;
    $('interpretation').hidden = false;
    $('interpretation').textContent = terms.mode==='source' ? `Texto enviado: “${terms.text}” · Resultados na ordem de cada fonte; os nomes não foram conferidos.` : terms.mode==='credits' ? `Pessoa: “${terms.artist || terms.text}” · Créditos e participações com nome exato.${chosenIdentity ? ' Identidade selecionada; consulta limitada à fonte que a identificou.' : ' Homônimos identificados serão apresentados separadamente.'}` : terms.artist || terms.title ? [terms.artist ? `Artista: “${terms.artist}”` : null,terms.title ? `Faixa: “${terms.title}”` : null].filter(Boolean).join(' · ') + ' · Nomes exatos, ignorando acentos, pontuação e maiúsculas.' : `Nome completo: “${terms.text}”. Para combinar artista e faixa, use Artista - Faixa ou os campos separados.`;
  }
  if (event.type === 'source') {
    completed++; $('progress').value = completed;
    $('progress-label').textContent = `${completed} de ${total} fontes avaliadas · ${event.name}: ${statusNames[event.status]}${event.cached ? ' (cache)' : ''}`;
    setSourceStatus(event.source,event.status,event.message);
    sourceDiagnostics.set(event.source,event);
    for (const person of event.people || []) if (event.status==='choose_person') foundPeople.set(`${person.source}:${person.id}`,person);
    renderPeople();
    if (event.notices?.length) sourceNotices.set(event.source,event.notices.map(n=>`${event.name}: ${n}`));
    renderDiagnostics();
    const existing = new Set(tracks.map(t=>`${t.source}:${t.source_id}`));
    for (const track of event.tracks) if (!existing.has(`${track.source}:${track.source_id}`)) { tracks.push(track); existing.add(`${track.source}:${track.source_id}`); }
    if (event.next_cursor) cursors[event.source] = event.next_cursor; else delete cursors[event.source];
    renderResults();
  }
  if (event.type === 'complete') {
    setHomePhase(tracks.length ? 2 : 3);
    const queried = event.sources.filter(s=>!['missing_credentials','unsupported'].includes(s.status)).length;
    const rejected = event.sources.reduce((count,s)=>count+(s.rejected_count || 0),0);
    $('progress-label').textContent = `${queried} fontes consultadas · somente resultados com áudio confirmado`;
  }
}
async function search(more = false) {
  document.body.classList.add('has-search');
  setSearchOptions(false);setHomePhase(1);
  const epoch=searchEpoch=(searchEpoch+1)>>>0;
  if (controller) controller.abort();
  const thisController = new AbortController(); controller = thisController;
  loadingMore = more;
  showError(''); $('cancel').hidden = false; $('more').hidden = true; $('progress-area').hidden = false; $('progress').value = 0;
  if (!more) {
    tracks = []; cursors = {}; foundPeople.clear(); sourceNotices.clear(); sourceDiagnostics.clear(); renderPeople(); $('source-notices').hidden=true;
    activeQuery = $('query').value.trim() || [$('search-artist').value.trim(),$('search-title').value.trim()].filter(Boolean).join(' - '); activeSources = chosenIdentity ? [chosenIdentity.source] : [...selected];
    activeFields = {mode:$('search-mode').value,provider_scope:$('provider-scope').value,exclude_covers:$('exclude-covers').checked,require_audio:true};
    if (chosenIdentity) { activeFields.identities = {[chosenIdentity.source]:chosenIdentity.id}; if (chosenIdentity.source==='musicbrainz_credits') activeFields.person_id=chosenIdentity.id; }
    if (activeFields.mode!=='source' && $('search-artist').value.trim()) activeFields.artist = $('search-artist').value.trim();
    if (activeFields.mode!=='source' && $('search-title').value.trim()) activeFields.title = $('search-title').value.trim();
  }
  $('results-title').textContent = `Resultados para “${activeQuery}”`;
  const sourceIds = more ? Object.keys(cursors) : activeSources;
  for (const source of catalogue) if (sourceIds.includes(source.id) && source.mode === 'api' && source.enabled) setSourceStatus(source.id,'searching');
  renderResults();
  try {
    const response = await api('/api/search/stream',{method:'POST',body:JSON.stringify({query:activeQuery,...activeFields,sources:sourceIds,limit:settings.max_results,cursors:more ? cursors : {}}),signal:thisController.signal});
    const reader = response.body.getReader(), decoder = new TextDecoder(); let buffer = '';
    while (true) {
      const {done,value} = await reader.read(); buffer += decoder.decode(value || new Uint8Array(),{stream:!done});
      const lines = buffer.split('\n'); buffer = lines.pop();
      for (const line of lines) if (line.trim() && Home.accepts(searchEpoch,epoch)===1 && controller === thisController) handleEvent(JSON.parse(line));
      if (done) { if (buffer.trim() && Home.accepts(searchEpoch,epoch)===1 && controller===thisController) handleEvent(JSON.parse(buffer)); break; }
    }
    await history();
  } catch (error) {
    if(controller!==thisController || Home.accepts(searchEpoch,epoch)!==1) return;
    if (error.name !== 'AbortError') {showError(error.message);setHomePhase(8);}
    else {$('progress-label').textContent = 'Busca cancelada. Resultados já recebidos foram preservados.';setHomePhase(tracks.length ? 2 : 3);}
  }
  finally { if (controller === thisController) { controller = null; $('cancel').hidden = true; $('more').hidden = !Object.keys(cursors).length; for (const source of catalogue) if (source.health.status === 'searching') setSourceStatus(source.id,'not_checked'); renderResults(); } }
}
$('search-form').addEventListener('submit',event=>{event.preventDefault(); if (!($('search-mode').value==='source' ? [$('query')] : [$('query'),$('search-artist'),$('search-title')]).some(node=>node.value.trim())) { showError('Informe um nome ou preencha artista e faixa.'); $('query').focus(); return; } search();});
$('cancel').addEventListener('click',()=>controller?.abort());
$('more').addEventListener('click',()=>search(true));
$('nav-search').addEventListener('click',event=>{event.preventDefault();setView('search');});
$('nav-settings').addEventListener('click',()=>setView('settings'));
$('manage-sources').addEventListener('click',()=>{setView('settings');window.showSettingsPanel?.('sources');document.querySelector('[data-panel="sources"]').focus();});
document.querySelector('a[href="#results-title"]').addEventListener('click',event=>{event.preventDefault();$('results-title').focus();$('results-title').scrollIntoView({block:'start'});});
document.querySelector('a[href="#source-controls"]').addEventListener('click',event=>{event.preventDefault();setSearchOptions(true);$('options-toggle').focus();$('options-toggle').scrollIntoView({block:'start'});});
$('options-toggle').addEventListener('click',()=>setSearchOptions(Home.toggle(Number(!$('source-controls').hidden))===1));
$('exclude-covers').addEventListener('change',renderSearchSummary);
$('select-all').addEventListener('click',()=>{const scope=$('provider-scope').value;for(const source of catalogue.filter(s=>s.enabled && (scope==='both' || s.provider_group===scope))) selected.add(source.id);renderSources();});
for (const node of document.querySelectorAll('[data-query]')) node.addEventListener('click',()=>startQuery(node.dataset.query));
for (const id of ['filter-platform','filter-category','filter-artist','filter-availability','filter-role','filter-kind']) $(id).addEventListener('input',renderResults);
for (const id of ['query','search-artist','search-title']) $(id).addEventListener('input',()=>{chosenIdentity=null;});
$('search-mode').addEventListener('change',()=>{chosenIdentity=null;document.querySelector('.precise-name-fields').hidden=$('search-mode').value==='source';$('mode-help').textContent=$('search-mode').value==='source' ? 'Exploração sem conferir nomes: pode incluir outros artistas.' : $('search-mode').value==='credits' ? 'Produtor, engenheiro, compositor ou intérprete. Cada papel mantém sua origem.' : 'Os nomes precisam corresponder aos metadados da mesma gravação.';renderSearchSummary();});
$('settings-form').addEventListener('submit',async event=>{
  event.preventDefault(); $('save-status').textContent = 'Salvando…';
  try {
    const disabled = [...document.querySelectorAll('[data-enable]')].filter(n=>!n.checked).map(n=>n.dataset.enable);
    const body = {...settings,provider_scope:$('pref-scope').value,download_max_mb:Number($('pref-download-limit').value),download_format:$('pref-download-format').value,download_pack:$('pref-download-pack').value,download_images:$('pref-download-images').checked,disabled_sources:disabled,max_results:Number($('max-results').value),concurrency:Number($('concurrency').value),timeout:Number($('timeout').value),theme:$('pref-theme').value,view:$('pref-view').value,country:$('pref-country').value.toUpperCase(),default_mode:$('pref-mode').value,exclude_covers:$('pref-exclude-covers').checked,show_artwork:$('pref-artwork').checked,show_credits:$('pref-credits').checked,show_album:$('pref-album').checked};
    const values = Object.fromEntries([...credentialClears].map(k=>[k,'']));
    for (const node of document.querySelectorAll('[data-credential]')) if (node.value.trim()) values[node.dataset.credential] = node.value.trim();
    if (Object.keys(values).length) await api('/api/credentials',{method:'PUT',body:JSON.stringify({values})});
    settings = await (await api('/api/settings',{method:'PUT',body:JSON.stringify(body)})).json();
    catalogue = await (await api('/api/sources')).json(); selected = new Set(catalogue.filter(s=>s.enabled && s.supports_files!==false).map(s=>s.id));
    $('exclude-covers').checked=settings.exclude_covers!==false;
    $('provider-scope').value=settings.provider_scope;renderSources(); renderSettings(); window.applyPreferences?.(); renderResults(); $('save-status').textContent = 'Ajustes salvos. Credenciais válidas somente nesta sessão.';
  } catch(error) { $('save-status').textContent = error.message; }
});
$('clear-cache').addEventListener('click',async()=>{try {await api('/api/cache',{method:'DELETE'});$('save-status').textContent='Cache limpo.';}catch(error){$('save-status').textContent=error.message;}});
$('show-logs').addEventListener('click',async()=>{try {const logs=await(await api('/api/logs')).json();$('logs').hidden=false;$('logs').textContent=logs.map(l=>`${new Date(l.at*1000).toLocaleString('pt-BR')}  ${l.source}  ${statusNames[l.status]||l.status}`).join('\n')||'Nenhuma consulta registrada.';}catch(error){$('save-status').textContent=error.message;}});
$('shutdown').addEventListener('click',async()=>{try {await api('/api/shutdown',{method:'POST'});$('save-status').textContent='Servidor encerrado. Você pode fechar esta aba.';}catch(error){$('save-status').textContent=error.message;}});
async function init() {
  try { [catalogue,settings] = await Promise.all(['/api/sources','/api/settings'].map(async path=>(await api(path)).json())); selected=new Set(catalogue.filter(s=>s.enabled && s.supports_files!==false).map(s=>s.id));$('provider-scope').value=settings.provider_scope || 'both';renderSources();$('exclude-covers').checked=settings.exclude_covers!==false;$('search-mode').value=settings.default_mode || 'auto';$('search-mode').dispatchEvent(new Event('change'));window.applyPreferences?.();document.dispatchEvent(new Event('everytune:ready'));await history(); }
  catch(error) {showError('Não foi possível carregar o aplicativo: '+error.message);}
}
init();
