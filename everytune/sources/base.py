import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from ..models import SearchTerms, SourcePage, TrackResult


class SourceError(Exception):
    def __init__(self, status: str, message: str):
        self.status, self.message = status, message


def retry_seconds(value: str | None) -> float:
    try:
        return max(0, float(value or "1"))
    except ValueError:
        try:
            return max(0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return 1


def text(value) -> str | None:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) or None
    return str(value) if value is not None else None


def year(value) -> str | None:
    value = text(value)
    return value[:4] if value and value[:4].isdigit() else None


def offset(cursor: str | None) -> int:
    if cursor is None:
        return 0
    if not cursor.isdecimal() or len(cursor) > 7:
        raise SourceError("unavailable", "Cursor inválido; refaça a busca.")
    return int(cursor)


class MusicSource(ABC):
    id: str
    name: str
    category: str
    credentials: tuple[str, ...] = ()
    interval: float = 0.3
    ttl: int = 900
    docs: str

    def __init__(self, client: httpx.AsyncClient, secrets: dict[str, str]):
        self.client, self.secrets = client, secrets
        self.lock = asyncio.Lock()
        self.last_request = 0.0
        self.blocked_until = 0.0

    @property
    def requires_api_key(self):
        return bool(self.credentials)

    def ready(self):
        return all(self.secrets.get(k) for k in self.credentials)

    def track(self, source_id, title, url, **kwargs) -> TrackResult:
        return TrackResult(source=self.id, source_id=str(source_id), title=title, url=url,
                           platform=self.name, category=self.category, **kwargs)

    async def request(self, url: str, *, params=None, headers=None, method="GET", data=None, json_data=None, response_format="json"):
        # Endpoints are fixed in adapters; redirects and arbitrary user destinations are never followed.
        for attempt in range(2):
            async with self.lock:
                if self.blocked_until > time.monotonic():
                    raise SourceError("rate_limit", "Aguarde o limite da plataforma antes de tentar novamente.")
                delay = max(0, self.interval - (time.monotonic() - self.last_request))
                if self.last_request and delay > 30:
                    raise SourceError("rate_limit", f"A fonte exige um intervalo entre consultas. Tente novamente em {int(delay)+1} segundos.")
                await asyncio.sleep(delay)
                self.last_request = time.monotonic()
                try:
                    response = await self.client.request(method, url, params=params, headers=headers, data=data, json=json_data)
                except (httpx.TimeoutException, httpx.NetworkError):
                    if attempt:
                        raise
                    response = None
            if response is None:
                await asyncio.sleep(0.3)
                continue
            if response.status_code == 429:
                delay = retry_seconds(response.headers.get("Retry-After"))
                self.blocked_until = time.monotonic() + delay
                if attempt == 0 and delay <= 2:
                    await asyncio.sleep(delay)
                    continue
                raise SourceError("rate_limit", "Limite de requisições atingido; tente mais tarde.")
            if response.status_code in (401, 403):
                raise SourceError("unavailable", f"Acesso recusado pela plataforma (HTTP {response.status_code}). Verifique credenciais e permissões.")
            if response.status_code >= 500 and attempt == 0:
                await asyncio.sleep(0.3)
                continue
            if response.status_code >= 300:
                raise SourceError("unavailable", f"Fonte respondeu HTTP {response.status_code}.")
            return response if response_format == "response" else response.json()
        raise SourceError("unavailable", "Fonte indisponível.")

    async def search_precise(self, terms: SearchTerms, limit: int, cursor: str | None) -> SourcePage:
        return await self.search(terms.query_text, limit, cursor)

    @abstractmethod
    async def search(self, query: str, limit: int = 20, cursor: str | None = None) -> SourcePage: ...
