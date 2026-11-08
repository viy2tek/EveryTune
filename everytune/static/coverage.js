(() => {
  let loading=0, sampleController=null;
  const sum=values=>Object.values(values || {}).reduce((a,b)=>a+b,0);
  const seconds=ms=>ms==null ? 'não medido' : `${(ms/1000).toLocaleString('pt-BR',{maximumFractionDigits:2})} s`;
  function sampleSources() {
    const scope=$('provider-scope').value;
    return catalogue.filter(s=>s.mode==='api' && s.supports_files!==false && s.enabled && selected.has(s.id) && (scope==='both' || scope===s.provider_group));
  }
  window.loadCoverage=async()=>{
    const epoch=++loading;
    const names=sampleSources().map(s=>s.name);
    $('coverage-scope').textContent=`${names.length} fontes marcadas no foco atual: ${names.slice(0,3).join(', ') || 'nenhuma'}${names.length>3 ? ' e outras '+(names.length-3) : ''}. Para conferir ou mudar a seleção, volte à busca e abra Opções de busca.`;
    try {
      const data=await(await api('/api/coverage')).json();
      if(epoch!==loading) return;
      const rate=data.searches ? `${Math.round(data.with_audio/data.searches*100)}%` : 'sem amostra';
      $('coverage-summary').textContent=`${data.with_audio}/${data.searches} buscas com áudio (${rate}) · ${data.pages} páginas adicionais · mediana até o primeiro áudio: ${seconds(data.first_audio_ms)} · ${data.downloads.ready || 0}/${sum(data.downloads)} preparações prontas. Até ${data.retention} medições recentes por tipo. ${data.source_mode_searches} buscas sem conferência de nomes. Preparar não confirma salvamento no navegador.`;
      const rows=data.sources.map(result=>{
        const row=el('tr');
        const failures=Object.entries(result.statuses).filter(([key])=>!['success','empty','no_match'].includes(key)).map(([key,n])=>`${n} ${statusNames[key] || key}`);
        const d=result.diagnostics;
        for(const [key,code] of [['name_or_version',1],['no_audio',2],['audio_check_failed',3],['audio_check_timeout',4]]) if(d[key]) failures.push(`${d[key]} ${Home.diagnostic_label(code)}`);
        const title=el('th','',catalogue.find(s=>s.id===result.source)?.name || result.source);title.scope='row';row.append(title);
        for(const text of [`${result.with_audio}/${result.attempts}`,String(result.cached),failures.join(' · ') || 'Nenhum registrado',`${result.downloads.ready || 0}/${sum(result.downloads)}`]) row.append(el('td','',text));
        return row;
      });
      $('coverage-sources').replaceChildren(...rows);
      if(!rows.length) {const row=el('tr'),cell=el('td','','Faça uma busca ou teste uma lista para começar a medir.');cell.colSpan=5;row.append(cell);$('coverage-sources').append(row);}
    }catch(error){if(epoch===loading) $('coverage-summary').textContent=error.message;}
  };
  $('coverage-refresh').addEventListener('click',window.loadCoverage);
  $('coverage-clear').addEventListener('click',async()=>{
    try{++loading;await api('/api/coverage',{method:'DELETE'});await window.loadCoverage();}
    catch(error){$('coverage-summary').textContent=error.message;}
  });
  $('coverage-cancel').addEventListener('click',()=>sampleController?.abort());
  $('coverage-run').addEventListener('click',async()=>{
    if(sampleController) return;
    const queries=$('coverage-queries').value.split('\n').map(q=>q.trim()).filter(Boolean);
    const sources=sampleSources().map(s=>s.id),scope=$('provider-scope').value;
    if(!queries.length || queries.length>10 || queries.some(q=>q.length>300) || !sources.length) {
      $('coverage-status').textContent='Informe de 1 a 10 buscas, com até 300 caracteres cada, e selecione ao menos uma fonte de áudio na busca.';return;
    }
    const controller=new AbortController();sampleController=controller;
    $('coverage-run').disabled=true;$('coverage-clear').disabled=true;$('coverage-cancel').hidden=false;$('coverage-results').replaceChildren();
    let completed=0;
    try {
      for(const query of queries) {
        if(controller.signal.aborted) break;
        $('coverage-status').textContent=`${completed}/${queries.length} concluídas · Testando “${query}”…`;
        const row=el('article','coverage-case');row.append(el('strong','',query));$('coverage-results').append(row);
        try {
          const response=await api('/api/search/stream',{method:'POST',signal:controller.signal,body:JSON.stringify({query,sources,provider_scope:scope,mode:'auto',require_audio:true,exclude_covers:true,limit:settings.max_results})});
          const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='',complete=null;
          try {
            while(true) {
              const {done,value}=await reader.read();buffer+=decoder.decode(value || new Uint8Array(),{stream:!done});
              const lines=buffer.split('\n');buffer=lines.pop();if(done && buffer.trim()) lines.push(buffer);
              for(const line of lines) if(line.trim()) {const event=JSON.parse(line);if(event.type==='complete') complete=event;}
              if(done) break;
            }
          }finally{reader.releaseLock();}
          if(!complete) throw new Error('A consulta terminou sem relatório completo.');
          const audio=complete.tracks.filter(t=>t.audio_available===true);
          row.append(el('p','small',`${audio.length} origens com áudio confirmado · primeiro áudio: ${seconds(complete.first_audio_ms)}`));
          for(const source of complete.sources) row.append(el('p','small muted',`${source.name}: ${statusNames[source.status] || source.status}${source.cached ? ' · metadados em cache' : ''}${source.message ? ' · '+source.message : ''}`));
        }catch(error){
          if(error.name==='AbortError') {row.append(el('p','small','Consulta cancelada; sem relatório completo.'));break;}
          row.append(el('p','small',error.message));
        }
        completed++;
        await window.loadCoverage();
      }
      $('coverage-status').textContent=`${controller.signal.aborted ? 'Teste cancelado. ' : ''}${completed}/${queries.length} consultas concluídas. Áudio disponível não comprova upload oficial.`;
    }finally{
      sampleController=null;$('coverage-run').disabled=false;$('coverage-clear').disabled=false;$('coverage-cancel').hidden=true;
      await window.loadCoverage();
    }
  });
})();
