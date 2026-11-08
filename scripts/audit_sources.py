"""Audit public page metadata from the FMHY inventory; never execute remote code/media."""
import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
import ipaddress
import json
from pathlib import Path
import re
import socket
import time
from urllib.parse import parse_qsl, urlencode, urldefrag, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "source-audit.json"
REPORT = ROOT / "docs" / "SOURCE_AUDIT.md"
AGENT = "EveryTuneSourceAudit"
USER_AGENT = "EveryTuneSourceAudit/0.1 (read-only music source inventory; https://fmhy.net/audio)"
PAGE_BYTES = 220_000
ROBOTS_BYTES = 64_000
BINARY_SUFFIXES = {".exe", ".msi", ".zip", ".rar", ".7z", ".tar", ".gz", ".dmg", ".apk", ".deb", ".rpm", ".mp3", ".flac", ".ogg", ".wav", ".m4a", ".mp4", ".webm", ".pdf", ".torrent"}
SEARCH_NAMES = {"q", "query", "search", "s", "term", "terms", "keyword", "keywords", "searchterm", "search_query", "artist", "track", "title"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def public_url(url):
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        return False
    if port not in (None, 80, 443):
        return False
    host = parts.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".localhost", ".internal")):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError:
            return False
        return len(host) <= 253 and all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in host.split("."))


def navigable_search_form(form):
    return form["method"] == "get" and bool(form["search_inputs"]) and public_url(form["action"]) and not any(re.search(r"password|passwd|^pwd$|^pass$", name, re.I) for name in form["inputs"])


class PageParser(HTMLParser):
    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.title = []
        self.in_title = False
        self.form = None
        self.forms = []
        self.anchor = None
        self.docs = []
        self.scripts = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "title":
            self.in_title = True
        elif tag == "form":
            self.form = {"method": attrs.get("method", "get").lower(), "action": urljoin(self.url, attrs.get("action") or self.url), "inputs": [], "search_inputs": [], "fixed_params": {}}
        elif tag in {"input", "textarea", "select"} and self.form is not None:
            name = attrs.get("name")
            if name:
                self.form["inputs"].append(name[:100])
                if attrs.get("type", "").lower() == "hidden" and not re.search(r"token|secret|password|key|csrf|session|nonce|signature|auth", name, re.I) and len(attrs.get("value", "")) <= 200:
                    self.form["fixed_params"][name] = attrs.get("value", "")
                if attrs.get("type", "").lower() != "hidden" and (attrs.get("type", "").lower() == "search" or name.casefold() in SEARCH_NAMES):
                    self.form["search_inputs"].append(name[:100])
        elif tag == "a" and attrs.get("href"):
            self.anchor = {"url": urljoin(self.url, attrs["href"]), "label": ""}
        elif tag == "script" and attrs.get("src"):
            url = urljoin(self.url, attrs["src"])
            if public_url(url) and len(self.scripts) < 12:
                self.scripts.append(url)

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if self.anchor is not None:
            self.anchor["label"] += data[:150]

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "form" and self.form is not None:
            self.forms.append(self.form)
            self.form = None
        elif tag == "a" and self.anchor is not None:
            item = self.anchor
            self.anchor = None
            label = " ".join(item["label"].split())[:100]
            if public_url(item["url"]) and re.search(r"\b(api|developers?|documentation|github|source code)\b", label, re.I) and len(self.docs) < 12:
                self.docs.append({"label": label, "url": item["url"]})

    def result(self):
        forms = self.forms + ([self.form] if self.form else [])
        return {"title": " ".join("".join(self.title).split())[:220],
                "search_forms": [f for f in forms if f["search_inputs"]],
                "get_search_forms": [f for f in forms if navigable_search_form(f)],
                "documentation_links": self.docs, "script_urls": self.scripts}


class Auditor:
    def __init__(self, concurrency, timeout):
        self.semaphore = asyncio.Semaphore(concurrency)
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=False,
                                       limits=httpx.Limits(max_connections=concurrency),
                                       headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.1"})
        self.host_locks = {}
        self.robots = {}
        self.robots_locks = {}
        self.dns = {}
        self.last_request = {}
        self.page_limit = PAGE_BYTES

    async def validate_destination(self, url):
        if not public_url(url):
            raise ValueError("Destino privado, esquema/porta não permitidos ou credenciais na URL")
        parts = urlsplit(url)
        host = parts.hostname
        if host not in self.dns:
            answers = await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(host, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM), 5)
            self.dns[host] = bool(answers) and all(ipaddress.ip_address(answer[4][0]).is_global for answer in answers)
        if not self.dns[host]:
            raise ValueError("DNS resolveu para endereço não público")

    async def fetch(self, url, max_bytes, *, robots_request=False):
        redirects = []
        for _ in range(5):
            await self.validate_destination(url)
            parts = urlsplit(url)
            if Path(parts.path).suffix.lower() in BINARY_SUFFIXES:
                return {"url": url, "status": None, "outcome": "non_page_link", "bytes_read": 0, "redirects": redirects}
            delay = 0.25
            if not robots_request:
                policy = await self.robot_policy(url)
                if policy["status"] != "allowed" or (policy.get("parser") and not policy["parser"].can_fetch(AGENT, url)):
                    return {"url": url, "status": None, "outcome": "robots_disallowed" if policy["status"] == "allowed" else policy["status"], "robots_url": policy["url"], "robots_http_status": policy.get("http_status"), "redirects": redirects}
                delay = max(delay, policy.get("delay", 0))
            lock = self.host_locks.setdefault(parts.netloc, asyncio.Lock())
            async with lock:
                await asyncio.sleep(max(0, delay-(time.monotonic()-self.last_request.get(parts.netloc, 0))))
                async with self.semaphore:
                    self.last_request[parts.netloc] = time.monotonic()
                    async with self.client.stream("GET", url) as response:
                        status = response.status_code
                        location = response.headers.get("location")
                        content_type = response.headers.get("content-type", "").lower()
                        if status in {301, 302, 303, 307, 308} and location:
                            redirects.append({"url": url, "status": status})
                            url = urljoin(url, location)
                            continue
                        result = {"url": url, "status": status, "content_type": content_type, "redirects": redirects}
                        if status != 200:
                            result["outcome"] = "http_blocked" if status in {401, 403, 429, 451} else "http_error"
                            return result
                        if not robots_request and not any(kind in content_type for kind in ("text/html", "application/xhtml+xml", "text/plain", "application/json")):
                            return {**result, "outcome": "non_html_resource", "bytes_read": 0}
                        body = bytearray()
                        truncated = False
                        async for chunk in response.aiter_bytes():
                            remaining = max_bytes-len(body)
                            body.extend(chunk[:remaining])
                            if len(chunk) > remaining or len(body) >= max_bytes:
                                truncated = True
                                break
                        result.update(body=body.decode("utf-8", errors="replace"), bytes_read=len(body), truncated=truncated, outcome="fetched")
                        return result
            # Serial requests per host, no automated retry or rate-limit bypass.
        return {"url": url, "outcome": "redirect_limit", "redirects": redirects, "status": None}

    async def robot_policy(self, url):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        lock = self.robots_locks.setdefault(origin, asyncio.Lock())
        async with lock:
            if origin not in self.robots:
                robots_url = origin + "/robots.txt"
                policy = {"url": robots_url}
                try:
                    async with asyncio.timeout(12):
                        response = await self.fetch(robots_url, ROBOTS_BYTES, robots_request=True)
                    policy["http_status"] = response.get("status")
                    if response.get("status") in (404, 410):
                        policy["status"] = "allowed"
                    elif response.get("status") == 200 and not response.get("truncated"):
                        parser = RobotFileParser(robots_url)
                        parser.parse(response.get("body", "").splitlines())
                        rate = parser.request_rate(AGENT)
                        policy.update(status="allowed", parser=parser, delay=max(parser.crawl_delay(AGENT) or 0, rate.seconds/rate.requests if rate and rate.requests else 0))
                    elif response.get("status") in (401, 403):
                        policy["status"] = "robots_disallowed"
                    else:
                        policy["status"] = "robots_unavailable"
                except (httpx.RequestError, TimeoutError, OSError, ValueError):
                    policy["status"] = "robots_unavailable"
                self.robots[origin] = policy
            return self.robots[origin]

    async def audit(self, item):
        record = {**item, "checked_at": now(), "validation": "automatic_page_metadata_only", "integration": "not_verified", "page_body_limit": self.page_limit}
        url = urldefrag(item["url"])[0]
        if Path(urlsplit(url).path).suffix.lower() in BINARY_SUFFIXES:
            return {**record, "outcome": "non_page_link", "evidence": "Extensão de arquivo; nenhum corpo requisitado"}
        try:
            async with asyncio.timeout(28):
                response = await self.fetch(url, self.page_limit)
            body = response.pop("body", "")
            record.update(response)
            record["requested_url"] = item["url"]
            if record["outcome"] == "fetched":
                if "text/html" in record["content_type"] or "application/xhtml+xml" in record["content_type"]:
                    parser = PageParser(record["url"])
                    parser.feed(body)
                    record.update(parser.result())
                    record["outcome"] = "html_inspected"
                    if re.search(r"just a moment|attention required.*cloudflare|verify you are human|access denied", record.get("title", ""), re.I):
                        record["outcome"] = "challenge_page"
                    host = urlsplit(record["url"]).hostname
                    section = item.get("section", "").lower()
                    if host in {"github.com", "gitlab.com", "codeberg.org", "sourceforge.net", "greasyfork.org"}:
                        kind = "repository_or_software"
                    elif any(word in section for word in ("editor", "synth", "plugin", "player", "ripping", "tools", "lyrics", "extension", "converter")):
                        kind = "tool_or_related_service"
                    elif any(word in section for word in ("radio", "podcast", "ambient")):
                        kind = "radio_podcast_or_ambient"
                    elif record.get("get_search_forms"):
                        kind = "public_search_form_candidate"
                    elif record.get("script_urls"):
                        kind = "website_with_javascript"
                    else:
                        kind = "website_unclassified"
                    record["page_kind"] = kind
                else:
                    record["outcome"] = "text_or_json_inspected"
                    record["evidence"] = "Tipo textual/JSON observado; sem presumir endpoint de busca"
        except (TimeoutError, httpx.TimeoutException):
            record.update(outcome="timeout", evidence="Timeout; nenhuma tentativa de contornar o serviço")
        except (ValueError, OSError, httpx.RequestError) as error:
            record.update(outcome="unsafe_destination" if isinstance(error, ValueError) else "network_error", evidence=type(error).__name__)
        return record


def save(records, total, complete=False):
    for record in records.values():
        if "search_forms" in record:
            record["get_search_forms"] = [form for form in record["search_forms"] if navigable_search_form(form)]
            if record.get("page_kind") == "public_search_form_candidate" and not record["get_search_forms"]:
                record["page_kind"] = "website_with_javascript" if record.get("script_urls") else "website_unclassified"
            host = urlsplit(record["url"]).hostname or ""
            if host.startswith(("git.", "gitlab.", "forgejo.", "gitea.")):
                record["page_kind"] = "repository_or_software"
    counts = dict(Counter(r["outcome"] for r in records.values()))
    result = {"catalogue": "https://fmhy.net/audio", "checked_at": now(), "inventory_count": 1188,
              "total_targets": total, "completed_targets": len(records), "complete": complete,
              "method": "Automatic read-only page metadata audit; robots respected; no remote code, audio or binary executed/downloaded; no authentication or protection bypass",
              "limits": {"page_bytes": PAGE_BYTES, "robots_bytes": ROBOTS_BYTES, "redirects": 5},
              "outcomes": counts, "sources": list(records.values())}
    temporary = OUTPUT.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(OUTPUT)
    return result


def write_report(result):
    rows = result["sources"]
    candidates = [r for r in rows if r.get("get_search_forms") and r.get("page_kind") == "public_search_form_candidate" and r["outcome"] == "html_inspected"]
    lines = ["# Auditoria automática de links FMHY Audio", "", f"Data UTC: {result['checked_at']}. Alvos processados: **{len(rows)}/{result['total_targets']}**. Inventário original: 1.188 URLs únicas; JUMO incluído como referência adicional quando ausente.", "",
             "Esta é uma inspeção de metadados públicos, não validação manual de cada serviço nem 1.188 integrações. Nenhum áudio, executável ou script remoto foi executado. Bloqueios, CAPTCHA, autenticação e robots não foram contornados. Páginas JS não foram executadas pelo auditor: ausência de form HTML não prova ausência de busca. Encontrar um form não verifica autorização para scraping, API ou incorporação de resultados.", "", "## Cobertura", "", "| Situação | Quantidade |", "|---|---:|"]
    lines += [f"| {status} | {count} |" for status, count in sorted(result["outcomes"].items())]
    kinds = Counter(r.get("page_kind", "não classificado por acesso/conteúdo") for r in rows)
    lines += ["", "## Tipo de página observado", "", "| Tipo | Quantidade |", "|---|---:|"]
    lines += [f"| {kind} | {count} |" for kind, count in kinds.most_common()]
    search_path = ROOT / "docs" / "search-audit.json"
    if search_path.exists():
        search_audit = json.loads(search_path.read_text(encoding="utf-8"))
        lines += ["", "## Auditoria das barras de pesquisa", "", f"[search-audit.json](search-audit.json): {search_audit['completed_sites']}/{search_audit['total_sites']} páginas de catálogos com forms GET processadas; {search_audit['total_form_queries']} consultas de formulário registradas. Cada formulário navegável foi inspecionado novamente para recuperar parâmetros fixos, e cada URL de busca passou por robots/DNS/limites de corpo. HTTP 200 ou eco do termo não prova que um catálogo tem a faixa correta; JSON-LD/microdata e possíveis campos HTML são apenas evidências, não equivalem a um adaptador validado.", "", "| Resultado da consulta | Quantidade |", "|---|---:|"]
        lines += [f"| {status} | {count} |" for status, count in sorted(search_audit["query_outcomes"].items())]
    validated = [item for item in rows if item.get("catalogue_validation")]
    if validated:
        lines += ["", "## Verificações de busca de catálogo", "", "Estas consultas foram executadas em páginas de resultados reais, com robots permitido e sem áudio. Os presets HTML continuam sujeitos a mudanças e às condições do site; a inspeção não é uma API oficial nem uma autorização jurídica de reprodução.", "", "| Fonte | Consulta / evidência | Resultado observado / preset |", "|---|---|---|"]
        for item in validated:
            check = item["catalogue_validation"]
            lines.append(f"| {item['label']} | [{check['query']}]({check['search_url']}) | {check['conclusion']} |")
        lines += ["", "Presets: [source_presets.json](../everytune/data/source_presets.json). Fixtures sanitizadas em `tests/fixtures/catalogue_ucsb.html`, `catalogue_vgmrips.html` e `catalogue_ocremix.html`, preservando 1–2 registros observados, sem scripts, previews ou links de download. Os campos de créditos constantes (=Performer, =Composer, =Arranger) refletem rótulos efetivamente vistos. Compositores/arranjadores não são apresentados como cantores.", "", "UCSB exige `nq=1` junto de `query_type=keyword`; sem `nq`, a consulta de teste devolveu o catálogo inteiro e foi rejeitada como validação de busca. CitizenFreak devolve títulos sem artista no próprio cartão: mantido como externo para não inventar a atribuição. OC ReMix `/site-search/` usa Google/JavaScript; o preset usa o formulário HTML específico `/quicksearch/remix/`, cuja resposta foi verificada. VGMRips retorna packs/álbuns e seus compositores, não faixas individuais."]
    lines += ["", "## Candidatos com formulário GET observado", "", "Todos os candidatos são apenas evidência de navegação externa; cada integração precisa de validação de resultado, termos, paginação e identidade dos créditos. A lista completa, incluindo bloqueios e scripts de SPA a inspecionar, está em [source-audit.json](source-audit.json).", "", "| Página | Seção FMHY | Evidência de pesquisa |", "|---|---|---|"]
    for item in candidates:
        forms = item["get_search_forms"]
        evidence = "; ".join(f"GET `{f['action']}` com {', '.join('`'+n+'`' for n in f['search_inputs'])}" for f in forms[:2])
        label = (item.get("label") or item.get("title") or "Site").replace("|", " ").replace("[", "").replace("]", "")
        section = item.get("section", "").replace("|", " ")
        lines.append(f"| [{label}]({item.get('requested_url',item['url'])}) | {section} | {evidence.replace('|','%7C')} |")
    lines += ["", "## Critérios e limites", "", "- Até 220.000 bytes por página e 64.000 por robots, com truncamento registrado. HTML parcial pode ocultar forms ou documentação; scripts listados não foram executados.", "- Robots 401/403 ou regras impeditivas bloqueiam a visita; robots indisponível/429/5xx não é tratado como permissão. 404/410 indica ausência de arquivo robots.", "- Cada destino e redirect é validado para HTTP(S), portas 80/443 e DNS público. Respostas não HTML/texto/JSON são encerradas antes da leitura do corpo; extensões de mídia/binários não são requisitadas.", "- Requisições serializadas por host, concorrência global limitada, sem retries automáticos para desbloquear sites. URLs com fragmentos visitam a página-base, mantendo o alvo original no registro.", "- `repository_or_software` e `tool_or_related_service` são classificações heurísticas baseadas em host/seção; não afirmações de que o produto nunca possui pesquisa.", "- Só ações GET foram registradas como candidatos de redirecionamento. Forms POST e chamadas JavaScript precisam de inspeção específica. A ausência de API/form observado é desconhecimento, não incompatibilidade permanente.", "- Não há investigação de licença ou termo de cada site neste crawler. Nenhum candidato foi adicionado ao aplicativo automaticamente.", "", "## Reexecutar", "", "```powershell", ".\\.venv\\Scripts\\python scripts/audit_sources.py --self-test", ".\\.venv\\Scripts\\python scripts/audit_sources.py", "```", "", "O JSON é um checkpoint atômico, salvo a cada 25 alvos. Reexecução só processa URLs ainda ausentes; `--refresh` refaz a auditoria. `--concurrency` e `--timeout` controlam o custo de rede."]
    REPORT.write_text("\n".join(lines)+"\n", encoding="utf-8")


def self_test():
    for url in ("https://127.0.0.1/", "http://10.0.0.1/", "http://[::1]/", "https://localhost/", "https://a.local/", "file:///a", "https://user:secret@example.org/", "https://example.org:8080/", "https://{domain}/", "https://host:bad/"):
        assert not public_url(url), url
    assert public_url("https://example.org/search?q=music")
    parser = PageParser("https://example.org/a/")
    parser.feed('<title>Music &amp; credits</title><form action="/search"><input name="q" type="search"><input name="csrf" value="SECRET"></form><form method="post"><input name="query"></form><a href="/docs/api">API documentation</a><script src="/app.js"></script>')
    data = parser.result()
    assert data["title"] == "Music & credits"
    assert len(data["search_forms"]) == 2 and len(data["get_search_forms"]) == 1
    assert data["get_search_forms"][0]["action"] == "https://example.org/search"
    assert data["get_search_forms"][0]["search_inputs"] == ["q"]
    assert "SECRET" not in str(data)
    assert data["documentation_links"][0]["url"] == "https://example.org/docs/api"
    assert data["script_urls"] == ["https://example.org/app.js"]
    assert not navigable_search_form({"method":"get","action":"https://example.org/","search_inputs":["title"],"inputs":["title","password"]})
    assert parser.result()["get_search_forms"][0]["fixed_params"] == {}
    metadata = structured_metadata('<script type="application/ld+json">{"@type":"MusicRecording","name":"Track","byArtist":{"@type":"Person","name":"Artist"}}</script>')
    assert metadata["music_jsonld_examples"][0]["name"] == "Track"
    assert metadata["music_jsonld_examples"][0]["byArtist"] == ["Artist"]
    assert structured_metadata('<script type="application/ld+json">INVALID</script>')["invalid_jsonld"] == 1
    presets_path = ROOT / "everytune" / "data" / "source_presets.json"
    if presets_path.exists():
        from bs4 import BeautifulSoup
        fixtures = {"custom_ucsb_cylinders": ("catalogue_ucsb.html", 2, "Kathleen Parlow."), "custom_vgmrips": ("catalogue_vgmrips.html", 2, "Koji Kondo"), "custom_ocremix": ("catalogue_ocremix.html", 1, "Avitron")}
        for definition in json.loads(presets_path.read_text(encoding="utf-8")):
            if definition["id"] not in fixtures:
                continue
            filename, count, person = fixtures[definition["id"]]
            html = (ROOT / "tests" / "fixtures" / filename).read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "html.parser")
            rows = soup.select(definition["results_path"])
            assert len(rows) == count
            assert person in [node.get_text(" ", strip=True) for node in rows[0].select(definition["fields"]["credit_name"])]
            assert not soup.select("script,audio,video,iframe,a.download")
    print("Self-check passed: public URL policy, forms, secrets omitted, docs and scripts.")


def structured_metadata(body):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, "html.parser")
    music = []
    types = Counter()
    visited = 0
    def walk(value, depth=0):
        nonlocal visited
        visited += 1
        if depth > 8 or visited > 800:
            return
        if isinstance(value, list):
            for child in value[:100]:
                walk(child, depth+1)
        elif isinstance(value, dict):
            raw_types = value.get("@type", [])
            observed = [raw_types] if isinstance(raw_types, str) else raw_types if isinstance(raw_types, list) else []
            types.update(t for t in observed if isinstance(t, str))
            if set(observed) & {"MusicRecording", "MusicAlbum"} and len(music) < 3:
                item = {"types": observed, "name": str(value.get("name", ""))[:200], "fields": sorted(value.keys())[:30]}
                for field in ("byArtist", "composer", "producer", "contributor", "creator", "author"):
                    names = value.get(field, [])
                    names = names if isinstance(names, list) else [names]
                    item[field] = [str(n.get("name", ""))[:150] if isinstance(n, dict) else str(n)[:150] for n in names[:10]]
                music.append(item)
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child, depth+1)
    invalid = 0
    for script in soup.select('script[type="application/ld+json"]')[:20]:
        try:
            if len(script.get_text()) <= 300_000:
                walk(json.loads(script.get_text()))
        except (ValueError, RecursionError, TypeError):
            invalid += 1
    microdata = []
    for node in soup.select('[itemtype*="MusicRecording"], [itemtype*="MusicAlbum"]')[:3]:
        name = node.select_one('[itemprop="name"]')
        artists = node.select('[itemprop="byArtist"], [itemprop="composer"], [itemprop="producer"]')
        microdata.append({"type": node.get("itemtype"), "name": name.get_text(" ", strip=True)[:200] if name else None,
                          "credit_text": [a.get_text(" ", strip=True)[:150] for a in artists[:10]]})
    selectors = {}
    for selector in (".artist", ".artists", ".performer", ".composer", ".producer", '[itemprop="byArtist"]', '[itemprop="contributor"]'):
        values = [n.get_text(" ", strip=True)[:150] for n in soup.select(selector)[:2]]
        if any(values):
            selectors[selector] = values
    return {"jsonld_types": dict(types), "music_jsonld_examples": music, "invalid_jsonld": invalid,
            "music_microdata_examples": microdata, "possible_credit_selectors": selectors,
            "metadata_status": "music_structured_data_observed" if music or microdata else "no_music_structured_data_observed_in_bounded_html"}


async def audit_search_forms(args):
    audit = json.loads(OUTPUT.read_text(encoding="utf-8"))
    targets = [item for item in audit["sources"] if item.get("get_search_forms") and item.get("page_kind") == "public_search_form_candidate" and item["outcome"] == "html_inspected"]
    path = ROOT / "docs" / "search-audit.json"
    records = {}
    if path.exists() and not args.refresh:
        previous = json.loads(path.read_text(encoding="utf-8"))
        records = {item["source_url"]: item for item in previous.get("sources", [])}
    auditor = Auditor(min(args.concurrency, 10), args.timeout)
    queue = asyncio.Queue()
    for item in targets:
        if item.get("requested_url", item["url"]) not in records:
            queue.put_nowait(item)
    def save_search(complete=False):
        queries = [query for item in records.values() for query in item.get("form_queries", [])]
        value = {"checked_at": now(), "total_sites": len(targets), "completed_sites": len(records), "total_form_queries": len(queries), "complete": complete,
                 "method": "One neutral query per observed navigable GET form; original HTML re-inspected for fixed parameters; robots, public DNS, 1MB body cap; metadata only, no JS execution or audio",
                 "query_outcomes": dict(Counter(q["outcome"] for q in queries)), "sources": list(records.values())}
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
        return value
    async def worker():
        while not queue.empty():
            item = queue.get_nowait()
            source_url = item.get("requested_url", item["url"])
            record = {"source_url": source_url, "label": item.get("label"), "section": item.get("section"), "checked_at": now(), "form_queries": []}
            try:
                async with asyncio.timeout(28):
                    page = await auditor.fetch(source_url, 1_000_000)
                body = page.pop("body", "")
                record["page_outcome"] = page["outcome"]
                if page["outcome"] == "fetched" and "html" in page.get("content_type", ""):
                    parser = PageParser(page["url"])
                    parser.feed(body)
                    forms = parser.result()["get_search_forms"]
                    seen = set()
                    for form in forms:
                        query_field = form["search_inputs"][0]
                        parts = urlsplit(form["action"])
                        fixed = {**dict(parse_qsl(parts.query)), **form.get("fixed_params", {})}
                        if any(re.search(r"token|secret|password|api.?key|authorization|session|csrf", name, re.I) for name in fixed):
                            continue
                        query = "Mario" if "soundtrack" in item.get("section", "").lower() else "Beethoven"
                        parameters = {**fixed, query_field: query}
                        url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(parameters), ""))
                        if url in seen:
                            continue
                        seen.add(url)
                        entry = {"search_url": url, "query": query, "query_param": query_field, "observed_fixed_params": fixed, "integration": "not_verified"}
                        try:
                            async with asyncio.timeout(28):
                                response = await auditor.fetch(url, 1_000_000)
                            html = response.pop("body", "")
                            entry.update(response)
                            if response["outcome"] == "fetched" and "html" in response.get("content_type", ""):
                                meta_parser = PageParser(response["url"])
                                meta_parser.feed(html)
                                entry["page_title"] = meta_parser.result()["title"]
                                entry["query_echoed_in_html"] = query.casefold() in html.casefold()
                                entry.update(structured_metadata(html))
                        except (httpx.RequestError, OSError, ValueError, TimeoutError) as error:
                            entry.update(outcome="query_error", evidence=type(error).__name__)
                        record["form_queries"].append(entry)
            except (httpx.RequestError, OSError, ValueError, TimeoutError) as error:
                record.update(page_outcome="page_error", evidence=type(error).__name__)
            records[source_url] = record
            if len(records) % 10 == 0:
                result = save_search()
                print(f"Search forms: {len(records)}/{len(targets)} sites; {result['total_form_queries']} queries", flush=True)
            queue.task_done()
    try:
        await asyncio.gather(*(worker() for _ in range(min(args.concurrency, 10))))
    finally:
        await auditor.client.aclose()
        value = save_search(complete=len(records) == len(targets))
        write_report(audit)
    print(f"Search audit complete: {value['completed_sites']}/{value['total_sites']}; {value['total_form_queries']} queries; {value['query_outcomes']}")


async def main(args):
    inventory = json.loads((ROOT / "docs" / "fmhy-audio-links.json").read_text(encoding="utf-8"))["links"]
    targets = {item["url"]: item for item in inventory}
    targets.setdefault("https://jumo-dl.pages.dev/", {"url": "https://jumo-dl.pages.dev/", "label": "JUMO-DL", "section": "User reference"})
    records = {}
    if OUTPUT.exists() and not args.refresh:
        previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        records = {item.get("requested_url", item["url"]): item for item in previous.get("sources", []) if item.get("requested_url", item["url"]) in targets}
        for item in records.values():
            item.setdefault("page_body_limit", previous.get("limits", {}).get("page_bytes", PAGE_BYTES))
        if args.expand_catalogues:
            records = {url:item for url,item in records.items() if not (item.get("truncated") and item.get("page_kind") in {"website_with_javascript", "website_unclassified"} and item["page_body_limit"] < 1_000_000)}
    auditor = Auditor(args.concurrency, args.timeout)
    if args.expand_catalogues:
        auditor.page_limit = 1_000_000
    queue = asyncio.Queue()
    for url, item in targets.items():
        if url not in records:
            queue.put_nowait(item)
    async def worker():
        while not queue.empty():
            item = queue.get_nowait()
            try:
                record = await auditor.audit(item)
            except Exception as error:
                record = {**item, "requested_url": item["url"], "checked_at": now(), "outcome": "audit_error", "evidence": type(error).__name__, "integration": "not_verified"}
            records[item["url"]] = record
            if len(records) % 25 == 0:
                result = save(records, len(targets))
                write_report(result)
                print(f"Checked {len(records)}/{len(targets)}: {result['outcomes']}", flush=True)
            queue.task_done()
    try:
        await asyncio.gather(*(worker() for _ in range(args.concurrency)))
    finally:
        await auditor.client.aclose()
        result = save(records, len(targets), complete=len(records) == len(targets))
        write_report(result)
    print(f"Complete: {len(records)}/{len(targets)}; {result['outcomes']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--concurrency", type=int, choices=range(1, 21), default=12)
    parser.add_argument("--timeout", type=float, default=8)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--search-forms", action="store_true", help="Probe all observed GET catalogue search forms with a neutral term")
    parser.add_argument("--expand-catalogues", action="store_true", help="Reinspect only truncated potential-catalogue pages with a 1MB cap")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.search_forms:
        asyncio.run(audit_search_forms(args))
    else:
        asyncio.run(main(args))
