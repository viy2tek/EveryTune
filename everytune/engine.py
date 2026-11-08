import asyncio
import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from urllib.parse import quote

import httpx

from .models import SearchRequest, SourcePage, rank
from .sources import ADAPTERS, EXTERNAL
from .sources.base import SourceError
from .sources.custom import CustomSource
from .storage import Store
from .providers import provider_group
from .downloads import NO_EXPORT

logger = logging.getLogger("everytune")


class SearchEngine:
    def __init__(self, store: Store, client: httpx.AsyncClient, secrets: dict[str, str], custom_client=None, downloads=None):
        self.store = store
        self.sources = {cls.id: cls(client, secrets) for cls in ADAPTERS}
        self.secrets = secrets
        self.custom_client = custom_client
        self.downloads = downloads
        self.definitions = {}
        self.latest = {}
        self.semaphore = asyncio.Semaphore(store.settings().concurrency)
        self.audio_semaphore=asyncio.Semaphore(store.settings().concurrency)
        self.audio_locks={};self.audio_times={}
        self.sources["musicbrainz_credits"].request = self.sources["musicbrainz"].request
        self.refresh_sources()

    def refresh_sources(self):
        definitions = {s.id:s for s in self.store.source_definitions()}
        for id in set(self.definitions)-set(definitions):
            self.sources.pop(id, None)
        for id, definition in definitions.items():
            if self.custom_client is not None and (self.definitions.get(id) != definition or id not in self.sources):
                self.sources[id] = CustomSource(self.custom_client, self.secrets, definition)
        self.definitions = definitions

    def catalogue(self):
        disabled = self.store.settings().disabled_sources
        sources = [dict(id=s.id, name=s.name, category=s.category, mode="api", enabled=s.id not in disabled,
                        requires_credentials=s.requires_api_key, credentials=list(s.credentials),
                        configured=s.ready(), docs=s.docs, supports_credits=getattr(s,"supports_credits",False) or bool(getattr(s,"definition",None) and (s.definition.credits_path or s.definition.fields.get("credit_name"))),
                        provenance="user" if isinstance(s,CustomSource) else "builtin", health=self.latest.get(s.id, {"status": "not_checked"})) for s in self.sources.values() if not isinstance(s,CustomSource) or s.definition.format != "external"]
        sources += [dict(id=s.id,name=s.name,category=s.category,mode="external",enabled=s.id not in disabled,requires_credentials=False,credentials=[],configured=True,provenance="user",health={"status":"external"}) for s in self.definitions.values() if s.format=="external"]
        sources += [dict(id=id, name=name, category=category, mode="external", enabled=id not in disabled,
                              requires_credentials=False, credentials=[], configured=True,
                              health={"status": "external"}) for id, name, category, _ in EXTERNAL]
        return [{**s,'provider_group':provider_group(s['id'],self.definitions),'supports_files':s['id'] not in NO_EXPORT} for s in sources]

    def validate_sources(self, ids):
        known = set(self.sources) | set(self.definitions) | {s[0] for s in EXTERNAL}
        if ids is not None and set(ids) - known:
            raise ValueError("Fonte desconhecida")

    async def search_source(self, source, request: SearchRequest, settings):
        start = time.monotonic()
        result = dict(source=source.id, name=source.name, status="unavailable", tracks=[], people=[], notices=[], next_cursor=None, cached=False, message=None, rejected_count=0)
        diagnostics=dict(candidates=0,name_or_version=0,no_audio=0,audio_check_failed=0,audio_check_timeout=0,audio_confirmed=0)
        result['diagnostics']=diagnostics
        try:
            if source.id in {"musicbrainz_credits","discogs"} and request.mode != "credits":
                raise SourceError("unsupported","Disponível no modo Pessoa e créditos.")
            if not source.ready():
                raise SourceError("missing_credentials", "Configure as credenciais desta fonte.")
            limit = request.limit or settings.max_results
            cursor = request.cursors.get(source.id)
            terms = request.terms().model_copy(update={"country":settings.country})
            config = self.definitions.get(source.id)
            key = hashlib.sha256(json.dumps(["openverse-files-cover-filter-v2", source.id, terms.model_dump(), limit, cursor,config.model_dump() if config else None], ensure_ascii=False).encode()).hexdigest()
            page = self.store.get(key)
            if page is None:
                async with self.semaphore:
                    async with asyncio.timeout(settings.timeout):
                        page = await source.search_precise(terms, limit, cursor)
                self.store.put(key, page, source.ttl)
            else:
                result["cached"] = True
            matches = rank(page.tracks, terms)
            diagnostics.update(candidates=len(page.tracks),name_or_version=len(page.tracks)-len(matches))
            verified=[]
            notices=list(page.notices)
            deadline=time.monotonic()+settings.timeout
            for index,track in enumerate(matches):
                track.provider_group = provider_group(track.source,self.definitions)
                if self.downloads:
                    track.download_ref = self.downloads.register(track)
                if not request.require_audio:
                    verified.append(track);continue
                if not self.downloads or not track.download_ref:
                    diagnostics['audio_check_failed']+=1;continue
                remaining=deadline-time.monotonic()
                if remaining<=0:
                    diagnostics['audio_check_timeout']+=len(matches)-index
                    notices.append('Parte dos candidatos não foi exibida: a verificação de áudio atingiu o limite de tempo desta fonte.')
                    break
                try:
                    async with asyncio.timeout(remaining):
                        async with self.audio_semaphore:
                            async with self.audio_locks.setdefault(source.id,asyncio.Lock()):
                                delay=max(0,source.interval-(time.monotonic()-max(source.last_request,self.audio_times.get(source.id,0))))
                                await asyncio.sleep(delay)
                                self.audio_times[source.id]=time.monotonic()
                                available=await self.downloads.confirm_audio(track.download_ref)
                    if available:
                        if not rank([track],terms):
                            diagnostics['name_or_version']+=1;continue
                        options=self.downloads.manifest(track.download_ref)['options']
                        audio=[o for o in options if o['kind']=='audio' and o['delivery']=='direct']
                        track.audio_formats=sorted({str(o.get('format') or Path(o['filename']).suffix.lstrip('.')).upper() for o in audio}-{''})
                        track.audio_file_count=len(audio)
                        track.audio_available=True;track.downloadable=True;track.file_access='offered';verified.append(track)
                        diagnostics['audio_confirmed']+=1
                    else:
                        diagnostics['no_audio']+=1
                except (TimeoutError,httpx.TimeoutException):
                    diagnostics['audio_check_timeout']+=1
                except (SourceError,httpx.RequestError,ValueError,KeyError):
                    diagnostics['audio_check_failed']+=1
                    continue
            matches=verified
            rejected = len(page.tracks)-len(matches)
            result.update(status="choose_person" if page.people and not matches else "success" if matches else "no_match" if page.tracks else "empty",
                          tracks=[t.model_dump(mode="json") for t in matches], people=[p.model_dump(mode="json") for p in page.people],notices=notices,next_cursor=page.next_cursor, rejected_count=rejected)
            if rejected:
                reasons=[f"{diagnostics[key]} {label}" for key,label in [('name_or_version','por nomes/versões'),('no_audio','sem áudio confirmado'),('audio_check_failed','com falha na verificação'),('audio_check_timeout','sem verificação concluída no prazo')] if diagnostics[key]]
                result["message"] = 'Candidatos não exibidos: '+', '.join(reasons)+'.'
        except SourceError as exc:
            result.update(status=exc.status, message=exc.message)
        except (TimeoutError, httpx.TimeoutException):
            result.update(status="timeout", message="A fonte demorou demais. As outras continuam disponíveis.")
        except (ValueError, KeyError, TypeError, IndexError, AttributeError):
            result.update(status="unavailable", message="Resposta inválida ou incompatível da plataforma.")
        except httpx.RequestError:
            result.update(status="unavailable", message="Não foi possível conectar à fonte.")
        except Exception:
            # Do not log exception strings: upstream errors can contain credential-bearing URLs.
            result.update(status="unavailable", message="Falha interna do adaptador; consulte a documentação.")
        result["elapsed_ms"] = round((time.monotonic()-start)*1000)
        self.latest[source.id] = {k: result[k] for k in ("status", "message", "elapsed_ms", "cached")}
        self.store.log(source.id, result["status"])
        logger.debug("source=%s status=%s elapsed_ms=%d count=%d", source.id, result["status"], result["elapsed_ms"], len(result["tracks"]))
        return result

    async def events(self, request: SearchRequest):
        started=time.monotonic();first_audio_ms=None
        self.validate_sources(request.sources)
        self.validate_sources(list(request.cursors))
        settings = self.store.settings()
        selected = set(request.sources) if request.sources is not None else {s["id"] for s in self.catalogue()}
        selected -= set(settings.disabled_sources)
        scope=request.provider_scope or settings.provider_scope
        if scope!='both':
            selected={id for id in selected if provider_group(id,self.definitions)==scope}
        external_ids={s['id'] for s in self.catalogue() if s['mode']=='external'}
        skipped=[{'source':s['id'],'name':s['name'],'reason':'external' if s['id'] in external_ids else 'catalogue'} for s in self.catalogue() if request.require_audio and s['id'] in selected and (s['id'] in NO_EXPORT or s['id'] in external_ids)]
        if request.require_audio:selected-=NO_EXPORT | external_ids
        terms = request.terms()
        # shortcut: history stores text only; persist parsed fields if ambiguous-name recall is needed.
        history_query = f"{terms.artist} - {terms.title}" if terms.artist and terms.title else terms.query_text
        self.store.remember(history_query)
        external = [dict(source=id, name=name, category=category, url=url.format(query=quote(terms.query_text, safe="")))
                    for id, name, category, url in EXTERNAL if id in selected]
        external += [dict(source=id,name=source.name,category=source.category,url=source.external_url(terms.query_text)) for id,source in self.sources.items() if id in selected and isinstance(source,CustomSource) and source.definition.format=="external"]
        if request.require_audio:external=[]
        tasks = [asyncio.create_task(self.search_source(source, request, settings)) for id, source in self.sources.items() if id in selected and not (isinstance(source,CustomSource) and source.definition.format=="external")]
        results = []
        try:
            yield {"type": "start", "total": len(tasks), "external": external, "skipped":skipped,"provider_scope":scope,"interpretation": request.terms().model_dump()}
            for task in asyncio.as_completed(tasks):
                result = await task
                results.append(result)
                if first_audio_ms is None and any(t['audio_available'] for t in result['tracks']):
                    first_audio_ms=round((time.monotonic()-started)*1000)
                yield {"type": "source", **result}
            tracks = [t for result in results for t in SourcePage(tracks=result["tracks"]).tracks]
            if request.require_audio:
                try:
                    self.store.measure('search',{'mode':request.mode,'page':bool(request.cursors),
                        'with_audio':bool(tracks),'first_audio_ms':first_audio_ms,
                        'sources':[{'source':r['source'],'status':r['status'],'cached':r['cached'],
                            'audio_count':len(r['tracks']),'diagnostics':r['diagnostics']} for r in results]})
                except sqlite3.Error:logger.warning('Local coverage counters could not be saved')
            yield {"type": "complete", "query": request.query, "interpretation": request.terms().model_dump(), "tracks": [t.model_dump(mode="json") for t in rank(tracks, request.terms())],
                   "sources": [{k: v for k, v in r.items() if k != "tracks"} for r in results], "external": external,"skipped":skipped,"first_audio_ms":first_audio_ms}
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
