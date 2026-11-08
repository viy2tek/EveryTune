"""Public-only requests: pin DNS results, preserve TLS identity, bound response sizes."""
import asyncio
import ipaddress
import socket

import httpx

from .sources.base import SourceError


def public_url(value: str) -> httpx.URL:
    try:
        url = httpx.URL(value)
    except httpx.InvalidURL:
        raise ValueError("URL inválida; use um endereço HTTPS público") from None
    if url.scheme != "https" or not url.host or url.username or url.password or url.port not in (None, 443):
        raise ValueError("Use HTTPS público, porta 443 e sem credenciais na URL")
    if url.host.casefold() in {"localhost", "localhost.localdomain"} or url.host.endswith((".local", ".localhost", ".internal")):
        raise ValueError("Destino local não permitido")
    try:
        address = ipaddress.ip_address(url.host)
    except ValueError:
        return url
    if not address.is_global or getattr(address, "ipv4_mapped", None):
        raise ValueError("IP não público")
    return url


class PublicTransport(httpx.AsyncBaseTransport):
    def __init__(self, *, metadata=True, max_bytes=2_000_000):
        self.metadata, self.max_bytes = metadata, max_bytes
        self.transport = httpx.AsyncHTTPTransport(retries=0, trust_env=False,limits=httpx.Limits(max_keepalive_connections=0))

    async def handle_async_request(self, request):
        url = public_url(str(request.url))
        addresses = await asyncio.get_running_loop().getaddrinfo(url.host, 443, type=socket.SOCK_STREAM)
        ips = {item[4][0] for item in addresses}
        if not ips or any(not ipaddress.ip_address(ip).is_global or getattr(ipaddress.ip_address(ip), "ipv4_mapped", None) for ip in ips):
            raise SourceError("unavailable", "DNS aponta para rede não pública; consulta recusada.")
        pinned = httpx.Request(request.method, url.copy_with(host=sorted(ips)[0]), headers=request.headers,
                               stream=request.stream, extensions={**request.extensions, "sni_hostname": url.host})
        pinned.headers["Host"] = url.netloc.decode()
        pinned.headers["Connection"] = "close"
        response = await self.transport.handle_async_request(pinned)
        content_type = response.headers.get("content-type", "").lower()
        if self.metadata and content_type and not any(kind in content_type for kind in ("text/","json","xml")):
            await response.aclose()
            raise SourceError("unavailable", "O destino retornou mídia/binário em vez de metadados.")
        if response.headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
            await response.aclose()
            raise SourceError("unavailable", "A fonte ignorou a solicitação de resposta sem compressão.")
        response.stream = BoundedStream(response.stream,self.max_bytes)
        return response

    async def aclose(self):
        await self.transport.aclose()


class BoundedStream(httpx.AsyncByteStream):
    def __init__(self, stream, max_bytes=2_000_000):
        self.stream = stream
        self.max_bytes = max_bytes

    async def __aiter__(self):
        size = 0
        async for chunk in self.stream:
            size += len(chunk)
            if size > self.max_bytes:
                raise SourceError("unavailable", "Resposta excede o limite de tamanho configurado.")
            yield chunk

    async def aclose(self):
        await self.stream.aclose()
