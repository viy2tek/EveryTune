import asyncio
import json
import logging
import mimetypes
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

import httpx
from . import __version__
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .engine import SearchEngine
from .models import SearchRequest, Settings
from .public_http import PublicTransport
from .source_config import SourceDefinition
from .sources import ADAPTERS, EXTERNAL
from .storage import Store, data_directory
from .downloads import DownloadManager
from .sources.base import SourceError

STATIC = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "everytune" / "static"
# Windows registry associations can otherwise serve ES modules as text/plain.
mimetypes.add_type('text/javascript', '.mjs')
CREDENTIAL_KEYS = {k for cls in ADAPTERS for k in cls.credentials}
DATA = STATIC.parent / "data"


def source_presets(names=("source_presets.json","free_website_presets.json","federated_presets.json")):
    definitions = []
    for name in names:
        path = DATA / name
        if path.exists():
            definitions.extend(SourceDefinition.model_validate(s) for s in json.loads(path.read_text(encoding="utf-8")))
    return definitions


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    settings: Settings
    sources: list[SourceDefinition] = Field(default_factory=list, max_length=200)


class CredentialUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    values: dict[str, SecretStr] = Field(max_length=20)


class DownloadSelection(BaseModel):
    model_config=ConfigDict(extra='forbid')
    ref: str = Field(pattern=r'^[A-Za-z0-9_-]{20,80}$')
    option_ids: list[str] = Field(min_length=1,max_length=500)
    pack: str = Field(pattern=r'^(original|zip)$')


class InspectDownloadPage(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source: str = Field(max_length=50)
    url: str = Field(max_length=5000)


class ProbeDownload(BaseModel):
    model_config=ConfigDict(extra='forbid')
    ref: str = Field(pattern=r'^[A-Za-z0-9_-]{20,80}$')
    option_id: str = Field(max_length=80)


class PreparedFileResponse(FileResponse):
    def __init__(self,*args,manager,id,**kwargs):
        super().__init__(*args,**kwargs)
        self.manager,self.job_id=manager,id

    async def __call__(self,scope,receive,send):
        try:self.manager.begin_serving(self.job_id)
        except (KeyError,ValueError):
            return await JSONResponse({'detail':'Arquivo temporário expirado ou removido.'},status_code=410)(scope,receive,send)
        try:await super().__call__(scope,receive,send)
        finally:self.manager.end_serving(self.job_id)


def create_app(directory: Path | None = None, transport=None):
    @asynccontextmanager
    async def lifespan(app):
        store = Store(directory if directory is not None else data_directory())
        store.initialize_sources(source_presets())
        # Upgrade installs only this new pack once, preserving edits and removed older sources.
        store.initialize_sources(source_presets(("federated_presets.json",)),key="source_federated_v1")
        secrets = {k: os.getenv("EVERYTUNE_" + k.upper(), "") for k in CREDENTIAL_KEYS}
        async with httpx.AsyncClient(timeout=httpx.Timeout(12), follow_redirects=False, transport=transport,
                                    headers={"User-Agent": "EveryTune/0.4 (personal local music discovery; https://fmhy.net/audio)", "Accept": "application/json"}) as client, httpx.AsyncClient(
                                        transport=PublicTransport(),timeout=12,follow_redirects=False,trust_env=False,
                                        headers={"User-Agent":"EveryTune/0.4 (personal source connector)","Accept-Encoding":"identity"}) as custom_client, httpx.AsyncClient(
                                            transport=PublicTransport(metadata=False,max_bytes=32*1024**3),timeout=httpx.Timeout(30,connect=12),follow_redirects=False,trust_env=False,
                                            headers={'User-Agent':'EveryTune/0.4 personal file download','Accept-Encoding':'identity'}) as transfer_client:
            downloads=DownloadManager(custom_client,transfer_client,store)
            app.state.engine = SearchEngine(store, client, secrets, custom_client,downloads)
            downloads.engine=app.state.engine
            app.state.downloads=downloads
            app.state.store = store
            try:
                yield
            finally:
                await downloads.aclose()
                store.close()

    app = FastAPI(title="EveryTune", version=__version__, lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Acesso entre sites recusado"}, status_code=403)
        origin = request.headers.get("origin")
        if origin:
            parsed = urlparse(origin)
            if parsed.scheme != "http" or parsed.netloc != request.headers.get("host"):
                return JSONResponse({"detail": "Origem não autorizada"}, status_code=403)
        if request.method in ("POST", "PUT", "DELETE") and request.headers.get("x-everytune") != "1":
            return JSONResponse({"detail": "Cabeçalho local obrigatório: X-EveryTune: 1"}, status_code=403)
        length = request.headers.get("content-length", "0")
        if not length.isdecimal() or int(length) > 1_000_000:
            return JSONResponse({"detail": "Corpo muito grande"}, status_code=413)
        response = await call_next(request)
        response.headers.update({"X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # FastAPI's default validation response echoes inputs, including secret values.
        return JSONResponse({"detail": [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]}, status_code=422)

    def validate(request):
        try:
            app.state.engine.validate_sources(request.sources)
            app.state.engine.validate_sources(list(request.cursors))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": __version__}

    @app.get("/api/sources")
    async def sources():
        return app.state.engine.catalogue()

    @app.get("/api/integrations")
    async def integrations():
        return app.state.engine.latest

    @app.get('/api/coverage')
    async def coverage():
        return app.state.store.coverage()

    @app.delete('/api/coverage')
    async def clear_coverage():
        app.state.store.clear_coverage()
        return {'cleared':True}

    @app.post('/api/downloads/resolve/{ref}')
    async def resolve_downloads(ref: str):
        try:
            async with asyncio.timeout(60):
                return await app.state.downloads.resolve(ref)
        except KeyError:raise HTTPException(410,'Resultado expirado; faça a pesquisa novamente.') from None
        except SourceError as error:raise HTTPException(429 if error.status=='rate_limit' else 502,error.message) from None
        except ValueError as error:raise HTTPException(422,str(error)) from None
        except Exception:raise HTTPException(502,'Não foi possível verificar os arquivos desta origem. Abra a página original ou tente novamente.') from None

    @app.post('/api/downloads/prepare')
    async def prepare_download(body: DownloadSelection):
        try:return app.state.downloads.prepare(body.ref,body.option_ids,pack=body.pack)
        except KeyError:raise HTTPException(410,'Opções expiradas; verifique os arquivos novamente.') from None
        except ValueError as error:raise HTTPException(422,str(error)) from None

    @app.post('/api/downloads/inspect')
    async def inspect_download_page(body: InspectDownloadPage):
        try:
            async with asyncio.timeout(60):return await app.state.downloads.inspect(body.source,body.url)
        except ValueError as error:raise HTTPException(422,str(error)) from None
        except SourceError as error:raise HTTPException(429 if error.status=='rate_limit' else 502,error.message) from None
        except Exception:raise HTTPException(502,'Não foi possível verificar esta página. Abra a origem para continuar.') from None

    @app.post('/api/downloads/probe')
    async def probe_download(body: ProbeDownload):
        try:
            async with asyncio.timeout(45):return await app.state.downloads.probe(body.ref,body.option_id)
        except KeyError:raise HTTPException(410,'Opção expirada; verifique a origem novamente.') from None
        except ValueError as error:raise HTTPException(422,str(error)) from None
        except SourceError as error:raise HTTPException(502,error.message) from None
        except Exception:raise HTTPException(502,'Não foi possível confirmar o destino como arquivo direto.') from None

    @app.get('/api/downloads/jobs')
    async def download_jobs():
        app.state.downloads.cleanup()
        return [app.state.downloads.job(id) for id in reversed(app.state.downloads.jobs)]

    @app.delete('/api/downloads/jobs/{id}')
    async def cancel_download(id: str):
        try:await app.state.downloads.cancel(id)
        except KeyError:raise HTTPException(404,'Preparação não encontrada.') from None
        except ValueError as error:raise HTTPException(409,str(error)) from None
        return {'cancelled':True}

    @app.get('/api/downloads/files/{id}')
    async def download_file(id: str):
        try:
            path=app.state.downloads.artifact(id)
            job=app.state.downloads.job(id)
        except KeyError:raise HTTPException(404,'Arquivo temporário expirado.') from None
        except ValueError as error:raise HTTPException(409,str(error)) from None
        return PreparedFileResponse(path,manager=app.state.downloads,id=id,filename=job['filename'],media_type='application/zip' if job['pack']=='zip' else 'application/octet-stream',headers={'X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})

    @app.post("/api/search")
    async def search(body: SearchRequest):
        validate(body)
        async for event in app.state.engine.events(body):
            if event["type"] == "complete":
                return event

    @app.post("/api/search/stream")
    async def stream(body: SearchRequest):
        validate(body)
        async def generate():
            async for event in app.state.engine.events(body):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        return StreamingResponse(generate(), media_type="application/x-ndjson")

    @app.get("/api/settings")
    async def settings():
        return app.state.store.settings()

    @app.put("/api/settings")
    async def update_settings(body: Settings):
        try:
            app.state.engine.validate_sources(body.disabled_sources)
        except ValueError:
            raise HTTPException(422, "Fonte desconhecida") from None
        app.state.store.save_settings(body)
        app.state.engine.semaphore = asyncio.Semaphore(body.concurrency)
        return body

    @app.put("/api/credentials")
    async def credentials(body: CredentialUpdate):
        keys = CREDENTIAL_KEYS | {s.credential_key for s in app.state.engine.definitions.values()}
        if set(body.values) - keys or any(len(v.get_secret_value()) > 8192 for v in body.values.values()):
            raise HTTPException(422, "Credencial desconhecida ou muito longa")
        affected={s.id for s in app.state.engine.sources.values() if set(s.credentials)&set(body.values)}
        await app.state.downloads.invalidate(affected)
        app.state.engine.secrets.update({k: v.get_secret_value().strip() for k, v in body.values.items()})
        spotify = app.state.engine.sources["spotify"]
        spotify.expires, spotify.token = 0, ""
        app.state.store.clear_cache()
        return {"saved": True, "storage": "session"}

    @app.get("/api/custom-sources")
    async def custom_sources():
        return app.state.store.source_definitions()

    @app.get("/api/source-audit")
    async def source_audit(q: str = Query(default="",max_length=200), outcome: str = Query(default="",max_length=80), scope: str = Query(default="selected",pattern="^(selected|all)$"), offset: int = Query(default=0,ge=0), limit: int = Query(default=50,ge=1,le=100)):
        if scope=="selected":
            path = DATA / "free-websites-audit.json"
            if not path.exists():
                path = Path(__file__).resolve().parent.parent / "docs" / "free-websites-audit.json"
            raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            rows = [{**s,"label":s.get("name"),"section":" / ".join(s.get("sections",[])),"get_search_forms":s.get("forms",[])} for s in raw.get("sources",[])]
            audit={"sources":rows,"complete":raw.get("complete",False),"total_targets":raw.get("total",0),"completed_targets":raw.get("completed",0),"outcomes":raw.get("outcomes",{})}
        elif not hasattr(app.state,"source_audit"):
            path = DATA / "source-audit.json"
            if not path.exists():
                path = Path(__file__).resolve().parent.parent / "docs" / "source-audit.json"
            app.state.source_audit = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"sources":[],"complete":False}
        if scope=="all":
            audit = app.state.source_audit
        records = [s for s in audit.get("sources",[]) if (not outcome or s.get("outcome")==outcome) and q.casefold() in (s.get("label","")+" "+s.get("url","")+" "+s.get("section","")).casefold()]
        keys = {"url","label","section","outcome","title","page_kind","get_search_forms","integration","status","validation","free_access","preset_id","reason"}
        return {"complete":audit.get("complete",False),"total":audit.get("total_targets",0),"completed":audit.get("completed_targets",0),"matched":len(records),"outcomes":audit.get("outcomes",{}),"sources":[{k:v for k,v in s.items() if k in keys} for s in records[offset:offset+limit]]}

    @app.put("/api/custom-sources")
    async def save_source(body: SourceDefinition):
        if body.id not in app.state.engine.definitions and len(app.state.engine.definitions)>=200:
            raise HTTPException(422,"Limite de 200 fontes personalizadas")
        previous=app.state.engine.definitions.get(body.id)
        if previous and (previous.endpoint,previous.auth,previous.auth_name,previous.auth_prefix)!=(body.endpoint,body.auth,body.auth_name,body.auth_prefix):
            app.state.engine.secrets.pop(body.credential_key,None)
        await app.state.downloads.invalidate({body.id})
        app.state.store.save_source(body)
        app.state.engine.refresh_sources()
        return {"saved":True,"id":body.id}

    @app.delete("/api/custom-sources/{id}")
    async def remove_source(id: str):
        if id not in app.state.engine.definitions:
            raise HTTPException(404,"Fonte personalizada não encontrada")
        await app.state.downloads.invalidate({id})
        app.state.store.delete_source(id)
        app.state.engine.secrets.pop(id+"_token",None)
        settings = app.state.store.settings()
        settings.disabled_sources = [s for s in settings.disabled_sources if s!=id]
        app.state.store.save_settings(settings)
        app.state.engine.refresh_sources()
        return {"deleted":True}

    @app.get("/api/profile")
    async def profile():
        return Profile(settings=app.state.store.settings(),sources=app.state.store.source_definitions())

    @app.put("/api/profile")
    async def import_profile(body: Profile):
        ids = [s.id for s in body.sources]
        known = {s.id for s in app.state.engine.sources.values() if not s.id.startswith("custom_")} | {s[0] for s in EXTERNAL} | set(ids)
        if len(ids)!=len(set(ids)) or set(body.settings.disabled_sources)-known:
            raise HTTPException(422,"IDs repetidos ou fonte desconhecida no perfil")
        await app.state.downloads.invalidate(set(app.state.engine.definitions))
        app.state.store.replace_profile(body.settings,body.sources)
        app.state.engine.refresh_sources()
        app.state.engine.semaphore = asyncio.Semaphore(body.settings.concurrency)
        for key in list(app.state.engine.secrets):
            if key.startswith("custom_"):
                app.state.engine.secrets.pop(key,None)
        return {"imported":True}

    @app.delete("/api/profile")
    async def reset_profile():
        await app.state.downloads.invalidate(set(app.state.engine.definitions))
        app.state.store.replace_profile(Settings(),source_presets())
        app.state.engine.refresh_sources()
        app.state.engine.semaphore = asyncio.Semaphore(Settings().concurrency)
        for key in list(app.state.engine.secrets):
            if key.startswith("custom_"):
                app.state.engine.secrets.pop(key,None)
        return {"reset":True}

    @app.delete("/api/cache")
    async def clear_cache():
        app.state.store.clear_cache()
        return {"cleared": True}

    @app.get("/api/history")
    async def history():
        return app.state.store.history()

    @app.get("/api/logs")
    async def logs():
        return app.state.store.logs()

    @app.post("/api/shutdown")
    async def shutdown():
        callback = getattr(app.state, "shutdown", None)
        if not callback:
            raise HTTPException(409, "Encerre o servidor com Ctrl+C no terminal")
        asyncio.get_running_loop().call_later(0.3, callback)
        return {"stopping": True}

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
