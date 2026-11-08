(() => {
  let manifest=null, chosen=new Set(), timer=null, resolving=0, opener=null, currentRef=null, pollEpoch=0, preparingSelection=false;
  const linkedJobs=new Map();
  const dialog=$('download-dialog');
  const kinds={audio:'Áudio',artwork:'Imagem'};
  const states={queued:'Na fila',running:'Preparando',ready:'Pronto para salvar',failed:'Falhou',cancelled:'Cancelado'};
  function qualityText(q,basis=0) {
    return q ? Home.quality((q.codec || '').toUpperCase(),q.bit_rate || 0,q.sample_rate || 0,q.bits_per_sample || 0,q.channels || 0,basis) : Home.quality_unknown();
  }
  function size(bytes) {
    if (!Number.isFinite(bytes)) return 'Tamanho não informado';
    const units=['B','KB','MB','GB'];let unit=0;
    while(bytes>=1024 && unit<units.length-1){bytes/=1024;unit++;}
    return `${bytes.toLocaleString('pt-BR',{maximumFractionDigits:1})} ${units[unit]}`;
  }
  function error(message='') {$('download-error').textContent=message;$('download-error').hidden=!message;}
  function populateSources() {const current=$('download-inspect-source').value;$('download-inspect-source').replaceChildren(...catalogue.filter(s=>s.enabled && (s.mode==='external' || s.provenance==='user' || ['archive','commons'].includes(s.id))).map(s=>new Option(s.name,s.id)));if ([...$('download-inspect-source').options].some(o=>o.value===current)) $('download-inspect-source').value=current;}
  function show(host=null) {
    populateSources();
    const active=document.activeElement;
    if(dialog.open) dialog.close();
    opener=active;
    dialog.classList.toggle('inline-downloads',Boolean(host));
    (host || document.body).append(dialog);
    if(host) {dialog.setAttribute('role','region');dialog.show();}
    else {dialog.removeAttribute('role');dialog.showModal();}
  }
  document.addEventListener('everytune:ready',populateSources);if(catalogue.length) populateSources();
  function filtered() {return (manifest?.options || []).filter(o=>(!$('download-kind').value || o.kind===$('download-kind').value) && (!$('download-format').value || o.format===$('download-format').value));}
  function selection() {$('download-selection-count').textContent=`${chosen.size} arquivos selecionados`;$('download-zip').disabled=preparingSelection || Home.can_zip(chosen.size)!==1;$('download-zip').textContent=$('download-pack').value==='original' ? 'Preparar arquivos separados' : 'Preparar ZIP selecionado';}
  function fileFormat(option) {
    const suffix=option.filename?.split('.').pop().toUpperCase();
    const format=suffix || option.format?.toUpperCase() || '';
    return ({WAVE:'WAV',AIF:'AIFF'})[format] || format;
  }
  function renderOptions() {
    const restoreFocus=preserveFocus($('download-options'),$('download-title'));
    $('download-options').replaceChildren();
    for (const option of filtered()) {
      const row=el('div','download-option'),check=el('input');check.type='checkbox';check.id=`download-file-${option.id}`;check.checked=chosen.has(option.id);check.disabled=option.delivery!=='direct';check.setAttribute('aria-label',`Selecionar ${option.label || option.filename} — ${option.filename}`);
      check.dataset.focusKey=`file-option:${option.id}`;
      check.addEventListener('change',()=>{check.checked ? chosen.add(option.id) : chosen.delete(option.id);selection();});
      const info=el('label','download-option-info');info.htmlFor=check.id;info.append(el('strong','',option.label || option.filename),el('p','small muted',option.filename),el('p','small muted',`${option.format || 'Formato não informado'} · ${kinds[option.kind] || 'Outro'} · ${size(option.size)}`));
      if(option.kind==='audio') info.append(el('p','small audio-quality',qualityText(option.quality)));
      row.append(check,info);
      if (option.delivery==='external') {
        const open=link(option.open_url?.startsWith('magnet:') ? 'Abrir no cliente externo ↗' : 'Abrir origem / espelho ↗',option.open_url?.startsWith('https:') ? option.open_url : null);
        if (option.open_url?.startsWith('magnet:?')) open.href=option.open_url;
        const actions=el('div','download-option-actions');actions.append(open);
        if(option.open_url?.startsWith('https:')) {const probe=el('button','text-button','Verificar arquivo direto');probe.type='button';probe.addEventListener('click',async()=>{probe.disabled=true;error();const ref=manifest.ref;try{const data=await(await api('/api/downloads/probe',{method:'POST',body:JSON.stringify({ref,option_id:option.id})})).json();if(manifest?.ref===ref) renderManifest(data,true);}catch(failure){error(failure.message);probe.disabled=false;}});actions.append(probe);}
        row.append(actions);
      } else {
        const button=el('button','secondary',`Preparar ${option.format || 'arquivo'}`);button.type='button';button.dataset.focusKey=`prepare:${option.id}`;button.setAttribute('aria-label',`Preparar ${option.format || 'arquivo'} — ${option.filename}`);button.addEventListener('click',()=>prepare([option.id],'original'));row.append(button);
      }
      $('download-options').append(row);
    }
    if (!filtered().length) $('download-options').append(el('p','small muted',manifest?.options.length ? 'Nenhum arquivo com estes filtros.' : 'Nenhum arquivo confirmado por este conector.'));
    selection();
    restoreFocus();
  }
  async function prepare(ids,pack,ref=manifest.ref) {
    if(currentRef===ref) error();
    if(currentRef===ref) setHomePhase(6);
    try {
      const job=await(await api('/api/downloads/prepare',{method:'POST',body:JSON.stringify({ref,option_ids:ids,pack})})).json();
      if(!linkedJobs.has(ref)) linkedJobs.set(ref,new Set());linkedJobs.get(ref).add(job.id);
      await poll();if(currentRef===ref) $('download-jobs').scrollIntoView({block:'nearest'});
      return true;
    }catch(failure){if(currentRef===ref){error(failure.message);setHomePhase(8);}return false;}
  }
  async function poll() {
    const epoch=pollEpoch=(pollEpoch+1)>>>0;
    clearTimeout(timer);
    try {
      const allJobs=await(await api('/api/downloads/jobs')).json();
      if(Home.accepts(pollEpoch,epoch)!==1) return;
      const jobs=dialog.classList.contains('inline-downloads') ? allJobs.filter(job=>linkedJobs.get(currentRef)?.has(job.id)) : allJobs;
      $('nav-downloads').textContent=allJobs.length ? `Downloads (${allJobs.length})` : 'Downloads';
      const restoreFocus=preserveFocus($('download-jobs'),$('download-queue-title'));
      const existing=new Map([...$('download-jobs').querySelectorAll('[data-job]')].map(row=>[row.dataset.job,row]));
      const rows=[], announcements=[];
      for (const job of jobs) {
        const row=existing.get(job.id) || el('article','download-job');row.dataset.job=job.id;
        const info=el('div');info.append(el('strong','',job.filename),el('p','small muted',`${states[job.status] || job.status} · ${job.files_done}/${job.files_total} arquivos · ${size(job.bytes)}${job.total_bytes ? ' / '+size(job.total_bytes) : ''}`));
        if(job.status==='ready' && job.quality_files?.length) {
          const quality=job.pack==='zip' ? el('details','quality-details') : el('div','quality-details');
          if(job.pack==='zip') {const summary=el('summary','','Dados técnicos dos áudios');summary.dataset.focusKey=`quality:${job.id}`;quality.append(summary);}
          for(const item of job.quality_files) {
            if(job.pack==='zip') quality.append(el('p','small',item.filename));
            if(item.declared) quality.append(el('p','small audio-quality',qualityText(item.declared)));
            quality.append(el('p','small audio-quality',qualityText(item.measured,item.basis==='header' ? 2 : 1)));
          }
          info.append(quality);
        }
        if (job.message) info.append(el('p','small download-job-error',job.message));
        if (job.status==='running' || job.status==='queued') {const progress=el('progress');progress.setAttribute('aria-label',`Preparando ${job.filename}`);if(job.total_bytes){progress.max=job.total_bytes;progress.value=job.bytes;}info.append(progress);}
        const signature=JSON.stringify([job.filename,job.status,job.files_done,job.files_total,job.bytes,job.total_bytes,job.message,job.quality_files]);
        if (row.dataset.status!==job.status) {
          announcements.push(`${job.filename}: ${states[job.status] || job.status}${job.message ? '. '+job.message : ''}`);
          const actions=el('div','download-job-actions');
          if (Home.can_save(({queued:1,running:6,ready:7,failed:8,cancelled:0})[job.status] ?? 0)===1) {const save=el('a','download-save','Salvar arquivo');save.href='/api/downloads/files/'+encodeURIComponent(job.id);save.download=job.filename;save.dataset.focusKey=`save:${job.id}`;save.setAttribute('aria-label',`Salvar arquivo — ${job.filename}`);actions.append(save);setHomePhase(7);}
          const remove=el('button','text-button',['running','queued'].includes(job.status) ? 'Cancelar' : 'Remover');remove.type='button';remove.dataset.focusKey=`remove:${job.id}`;remove.setAttribute('aria-label',`${remove.textContent} — ${job.filename}`);remove.addEventListener('click',async()=>{try{await api('/api/downloads/jobs/'+encodeURIComponent(job.id),{method:'DELETE'});await poll();}catch(failure){error(failure.message);}});actions.append(remove);
          row.replaceChildren(info,actions);row.dataset.status=job.status;
        } else if(row.dataset.infoSignature!==signature) row.firstElementChild.replaceWith(info);
        row.dataset.infoSignature=signature;
        rows.push(row);
      }
      if (!jobs.length) rows.push(el('p','small muted','Nenhuma preparação nesta sessão.'));
      reconcileChildren($('download-jobs'),rows);restoreFocus();
      if (announcements.length) $('download-job-status').textContent=announcements.join('. ');
      if (allJobs.some(j=>['queued','running'].includes(j.status))) timer=setTimeout(poll,1000);
    }catch(failure){if(Home.accepts(pollEpoch,epoch)===1) error(failure.message);}
  }
  function renderManifest(data,preserve=false) {
      data={...data,options:data.options.filter(o=>Home.allowed_file(({audio:1,artwork:2})[o.kind] || 0)===1)};
      manifest=data;if(!preserve) chosen.clear();$('download-subtitle').textContent=`${data.source} · ${data.title}`;
      if(!preserve) {
        const preferred=settings.download_format || '';
        const hasFormat=Boolean(preferred) && data.options.some(o=>o.kind==='audio' && o.delivery==='direct' && fileFormat(o)===preferred);
        for(const option of data.options) if(Home.select_file(({audio:1,artwork:2})[option.kind] || 0,Number(option.delivery==='direct'),Number(Boolean(preferred) && fileFormat(option)===preferred),Number(hasFormat && settings.download_images===true))===1) chosen.add(option.id);
        $('download-pack').value=settings.download_pack || 'zip';
        $('download-preference-note').textContent=preferred ? hasFormat ? `${preferred}: arquivos marcados conforme suas preferências. Revise a seleção antes de preparar.` : `${preferred} não está disponível nesta origem. Escolha outro formato; nenhum substituto foi marcado.` : 'Escolha os arquivos. Você pode salvar formato e pacote preferidos nos ajustes.';
      }
      const valid=new Set(data.options.filter(o=>o.delivery==='direct').map(o=>o.id));chosen=new Set([...chosen].filter(id=>valid.has(id)));
      $('download-evidence').replaceChildren(link('Ver página de origem ↗',data.page_url));
      if (data.license) $('download-evidence').append(document.createTextNode(` · Licença informada: ${data.license}`));
      $('download-notices').replaceChildren(...data.notices.map(n=>el('p','',n)));
      $('download-kind').value='';$('download-format').replaceChildren(new Option('Todos',''));
      for (const format of [...new Set(data.options.map(o=>o.format).filter(Boolean))].sort()) $('download-format').append(new Option(format,format));
      $('download-manifest').hidden=false;renderOptions();
      setHomePhase(5);
  }
  window.showFiles=async(ref,title,host=null)=>{
    if(currentRef===ref && manifest?.ref===ref) {$('download-title').textContent='Arquivos';$('download-subtitle').textContent=`${manifest.source} · ${manifest.title}`;$('download-manifest').hidden=false;show(host);poll();return;}
    currentRef=ref;setHomePhase(4);
    const request=++resolving;manifest=null;chosen.clear();error();
    $('download-title').textContent='Arquivos';$('download-subtitle').textContent=`Verificando a origem: ${title}`;$('download-manifest').hidden=true;show(host);poll();
    try {
      const data=await(await api('/api/downloads/resolve/'+encodeURIComponent(ref),{method:'POST'})).json();
      if (Home.accepts(resolving,request)!==1) return;
      renderManifest(data);
    }catch(failure){if(request===resolving){$('download-subtitle').textContent=title;error(failure.message);}}
  };
  $('download-inspect-form').addEventListener('submit',async event=>{event.preventDefault();const request=++resolving;currentRef=null;show();poll();error();$('download-subtitle').textContent='Verificando a página informada…';$('download-manifest').hidden=true;try{const data=await(await api('/api/downloads/inspect',{method:'POST',body:JSON.stringify({source:$('download-inspect-source').value,url:$('download-inspect-url').value})})).json();if(request===resolving) renderManifest(data);}catch(failure){if(request===resolving) error(failure.message);}});
  $('nav-downloads').addEventListener('click',()=>{++resolving;$('download-title').textContent='Seus downloads';$('download-subtitle').textContent='Arquivos preparados nesta sessão';$('download-manifest').hidden=true;error();show();poll();});
  $('download-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{
    if(dialog.open) return;
    const active=document.activeElement;
    if(active!==document.body && !dialog.contains(active)) return;
    const replacement=opener?.isConnected ? opener : [...document.querySelectorAll('[data-focus-key]')].find(n=>n.dataset.focusKey===opener?.dataset.focusKey);
    (replacement || $('results-title')).focus({preventScroll:true});
  });
  dialog.addEventListener('keydown',event=>{if(event.key==='Escape' && dialog.classList.contains('inline-downloads')) {event.preventDefault();dialog.close();}});
  for (const id of ['download-kind','download-format']) $(id).addEventListener('change',renderOptions);
  $('download-select-visible').addEventListener('click',()=>{for(const option of filtered()) if(option.delivery==='direct') chosen.add(option.id);renderOptions();});
  $('download-clear').addEventListener('click',()=>{chosen.clear();renderOptions();});
  $('download-pack').addEventListener('change',selection);
  $('download-zip').addEventListener('click',async()=>{
    if(preparingSelection || !chosen.size) return;
    const ids=[...chosen],ref=manifest.ref,pack=$('download-pack').value;
    preparingSelection=true;selection();
    try {
      if(pack==='zip') await prepare(ids,'zip',ref);
      else {
        let created=0;
        for(const id of ids) {
          if(!await prepare([id],'original',ref)) {
            if(currentRef===ref) error(`${created}/${ids.length} preparações criadas. As restantes continuam selecionadas. ${$('download-error').textContent}`);
            break;
          }
          created++;
          if(currentRef===ref) chosen.delete(id);
        }
        if(currentRef===ref) {renderOptions();$('download-preference-note').textContent=`${created}/${ids.length} preparações criadas. Acompanhe o andamento abaixo; isso ainda não salva os arquivos no navegador.`;}
      }
    }finally{preparingSelection=false;selection();}
  });
})();
