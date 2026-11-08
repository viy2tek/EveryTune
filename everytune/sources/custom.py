import hashlib
import re
from urllib.parse import quote, urlencode, urljoin
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

from ..models import Credit, SourcePage, normalize
from ..public_http import public_url
from .base import MusicSource, SourceError, offset, text


def path_value(value, path):
    if not path:
        return value
    for part in path.split("."):
        selection = re.fullmatch(r"([^\[\]]+)\[([^=\[\]]+)=([^\[\]]+)\]",part)
        if selection:
            key,attribute,expected=selection.groups()
            choices=value.get(key) if isinstance(value,dict) else None
            value=next((item for item in choices if isinstance(item,dict) and str(item.get(attribute))==expected),None) if isinstance(choices,list) else None
            continue
        if isinstance(value, list) and part.isdecimal():
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def html_value(record, selector):
    if selector.startswith("="):
        return selector[1:]
    css, sep, attribute = selector.rpartition("@")
    if not sep:
        css = selector
    node = record.select_one(css) if css else record
    if node is None:
        return None
    return node.get(attribute) if sep else node.get_text(" ", strip=True)


class CustomSource(MusicSource):
    def __init__(self, client, secrets, definition):
        super().__init__(client, secrets)
        self.definition = definition
        self.id, self.name, self.category = definition.id, definition.name, definition.category
        self.docs = definition.endpoint
        self.credentials = (definition.credential_key,) if definition.auth != "none" else ()
        self.interval, self.ttl = definition.interval, definition.ttl
        self.robots = None

    async def check_robots(self, target=None):
        if self.robots is None:
            url = urljoin(self.definition.endpoint, "/robots.txt")
            response = await self.client.get(url)
            if response.status_code in (404, 410):
                rules = []
            elif response.status_code == 200:
                rules = response.text.splitlines()
            else:
                raise SourceError("unavailable", "Não foi possível verificar robots.txt; extração HTML suspensa.")
            self.robots = RobotFileParser()
            self.robots.parse(rules)
        if not self.robots.can_fetch("EveryTune", target or self.definition.endpoint):
            raise SourceError("unavailable", "O site não permite esta extração via robots.txt.")
        self.interval = max(self.interval,self.robots.crawl_delay("EveryTune") or self.robots.crawl_delay("*") or 0)

    def external_url(self, query):
        config=self.definition
        endpoint=config.endpoint.rstrip('/')+'/'+quote(query,safe='') if config.query_in_path else config.endpoint
        params={**config.params} if config.query_in_path else {**config.params,config.query_param:query}
        return endpoint + ('?'+urlencode(params) if params else '')

    async def search_precise(self, terms, limit, cursor):
        return await self.search(terms.query_text, limit, cursor, raw=terms.mode=="source")

    async def search(self, query, limit=20, cursor=None, *, raw=False):
        config = self.definition
        if config.format == "external":
            return SourcePage(notices=["Esta fonte abre pesquisa no site original."])
        parts = cursor.split(":",1) if cursor else []
        start = offset(parts[0]) if parts else (config.page_start if config.page_mode != "offset" else 0)
        local_start = offset(parts[1]) if len(parts)==2 else 0
        endpoint=config.endpoint.rstrip('/')+'/'+quote(query,safe='') if config.query_in_path else config.endpoint
        params = {**config.params} if config.query_in_path else {**config.params,config.query_param:query}
        if config.limit_param:
            params[config.limit_param] = limit
        if config.page_param:
            params[config.page_param] = start
        if config.format == "html" or config.respect_robots:
            await self.check_robots(endpoint+'?'+urlencode(params) if config.method=='GET' and params else endpoint)
        headers = {}
        if config.auth != "none":
            token = self.secrets.get(config.credential_key, "")
            if not token:
                raise SourceError("missing_credentials", "Configure a chave desta fonte personalizada.")
            if config.auth == "header":
                headers[config.auth_name] = config.auth_prefix + token
            else:
                params[config.auth_name] = token
        if config.method=="POST":
            query_auth = {config.auth_name:params.pop(config.auth_name)} if config.auth=="query" else None
            body = {"json_data":params} if config.request_encoding=="json" else {"data":params}
            response = await self.request(endpoint, method="POST", params=query_auth, headers=headers, response_format="response", **body)
        else:
            response = await self.request(endpoint, params=params, headers=headers, response_format="response")
        if len(response.content) > 2_000_000:
            raise SourceError("unavailable", "Resposta muito grande.")
        if config.format == "json":
            payload = response.json()
            rows = path_value(payload, config.results_path)
            if rows is None and config.results_optional:
                parent_path, _, key = config.results_path.rpartition('.')
                parent = path_value(payload,parent_path)
                if isinstance(parent,dict) and key not in parent:
                    rows = []
            if not isinstance(rows, list):
                raise SourceError("unavailable", "O caminho de resultados não contém uma lista JSON.")
            extract = path_value
        else:
            if "html" not in response.headers.get("content-type", ""):
                raise SourceError("unavailable", "A resposta não é uma página HTML.")
            rows = BeautifulSoup(response.text, "html.parser").select(config.results_path)
            extract = html_value
        if config.kind=="catalogue_post" and not raw:
            needle=f" {normalize(query)} "
            rows=[row for row in rows if needle in f" {normalize(str(extract(row,config.fields['title']) or ''))} "]
        tracks = []
        seen_urls=set()
        invalid = 0
        for row in rows[local_start:local_start+limit]:
            try:
                values = {key:extract(row,path) for key,path in config.fields.items()}
                id = text(values.get("id"))
                raw_url = values.get("url") or (config.link_template.replace("{id}",quote(id,safe="")) if config.link_template and id else None)
                if not values.get("title") or not raw_url:
                    invalid += 1
                    continue
                url = urljoin(config.endpoint, str(raw_url))
                public_url(url)
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                artwork = urljoin(config.endpoint,str(values["artwork"])) if values.get("artwork") else None
                if artwork:
                    public_url(artwork)
                credits = []
                if config.format == "json" and config.credits_path:
                    for credit in (path_value(row,config.credits_path) or [])[:100]:
                        name = path_value(credit,config.fields.get("credit_name","name"))
                        role = path_value(credit,config.fields.get("credit_role","role"))
                        if name and role:
                            credits.append(Credit(name=str(name),role=str(role),person_id=text(path_value(credit,config.fields.get("credit_id","id"))),evidence_url=url))
                elif config.format == "html" and config.fields.get("credit_name") and values.get("credit_role"):
                    for person in row.select(config.fields["credit_name"])[:100]:
                        name = person.get_text(" ", strip=True)
                        if name:
                            credits.append(Credit(name=name,role=str(values["credit_role"]),evidence_url=url))
                duration = float(values["duration"]) if values.get("duration") is not None else None
                tracks.append(self.track(id or hashlib.sha256(url.encode()).hexdigest()[:24], str(values["title"]),url,
                    artist=text(values.get("artist")),album=text(values.get("album")),
                    artwork=artwork,
                    duration=duration/1000 if duration is not None and config.duration_unit=="milliseconds" else duration,
                    year=text(values.get("year")),license=text(values.get("license")),kind=config.kind,credits=credits))
            except (ValueError,TypeError,KeyError,IndexError):
                invalid += 1
        next_cursor = f"{start}:{local_start+limit}" if local_start+limit<len(rows) else str(start+(len(rows) if config.page_mode in {"offset","index"} else 1)) if config.page_param and len(rows)>=limit else None
        return SourcePage(tracks=tracks,next_cursor=next_cursor,notices=[f"{invalid} registros sem metadados válidos foram ignorados."] if invalid else [])
