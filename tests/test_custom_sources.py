import asyncio
import json
import socket

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from everytune.app import create_app, source_presets
from everytune.models import Settings
from everytune.public_http import PublicTransport, public_url
from everytune.source_config import SourceDefinition
from everytune.sources.base import SourceError
from everytune.sources.custom import CustomSource

HEADERS = {"X-EveryTune": "1"}


def definition(**values):
    return SourceDefinition(id="custom_fixture", name="Fixture catalogue", endpoint="https://catalog.example.org/search", **values)


@pytest.mark.parametrize("url", [
    "http://catalog.example.org/search", "https://localhost/search", "https://localhost.localdomain/",
    "https://api.local/search", "https://api.internal/search", "https://api.localhost/search",
    "https://127.0.0.1/search", "https://10.0.0.1/search", "https://192.168.0.1/search",
    "https://169.254.169.254/", "https://[::1]/", "https://[::ffff:8.8.8.8]/",
    "https://user:secret@catalog.example.org/", "https://catalog.example.org:8443/search",
    "https://catalog.example.org/search?api_key=SECRET", "https://catalog.example.org/search#fragment",
    "https://[not-an-ip]/", "https://catalog.example.org:bad/", "https://catalog.example.org/\nHeader:foo",
])
def test_definition_rejects_non_public_or_secret_endpoint(url):
    with pytest.raises((ValidationError, ValueError)):
        SourceDefinition(id="custom_fixture", name="Fixture", endpoint=url)


@pytest.mark.parametrize("values", [
    {"params": {"access_token": "secret"}}, {"params": {"api-key": "secret"}},
    {"auth_name": "Host"}, {"auth_name": "Cookie"}, {"fields": {"script": "eval"}},
    {"fields": {"artist": "name"}}, {"fields": {"title": "name"}},
    {"link_template": "https://catalog.example.org/{query}"},
    {"link_template": "https://localhost/{id}"}, {"query_param": "bad\nheader"},
])
def test_definition_rejects_invalid_mapping_and_auth_configuration(values):
    with pytest.raises((ValidationError, ValueError)):
        definition(**values)


async def test_json_mapping_credits_pagination_and_invalid_records():
    config = definition(results_path="data.items", page_param="offset", page_mode="offset", duration_unit="milliseconds",
        credits_path="credits", fields={"title":"name","artist":"performer.name","url":"url","duration":"duration",
        "credit_name":"person.name","credit_role":"role","credit_id":"person.id"})
    rows = [{"name":"Song","performer":{"name":"Singer"},"url":"/song","duration":123000,
             "credits":[{"person":{"name":"Producer Name","id":"person-1"},"role":"producer"}]},
            {"name":"Missing link"}, {"name":"Unsafe link","url":"http://catalog.example.org/song"}]
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"data":{"items":rows}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source = CustomSource(client, {}, config)
        page = await source.search("Producer Name", 3, "6")
    assert len(page.tracks) == 1
    track = page.tracks[0]
    assert track.artist == "Singer" and track.duration == 123
    assert str(track.url) == "https://catalog.example.org/song"
    assert track.credits[0].name == "Producer Name" and track.credits[0].role == "producer"
    assert track.credits[0].person_id == "person-1"
    assert track.credits[0].name != track.artist
    assert page.next_cursor == "9"
    assert "2 registros" in page.notices[0]
    assert requests[0].url.params["q"] == "Producer Name"
    assert requests[0].url.params["offset"] == "6"


async def test_html_mapping_multiple_credits_and_constant_role():
    html = '<article class="record"><a class="title" href="/song">Song</a><span class="person">Alice</span><span class="person">Bob</span></article>'
    config = definition(format="html", results_path="article.record", fields={"title":".title","url":".title@href","credit_name":".person","credit_role":"=Composer"})
    requests = []
    def handler(request):
        requests.append(request)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text=html, headers={"Content-Type":"text/html"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source = CustomSource(client, {}, config)
        page = await source.search("Alice")
    assert len(page.tracks) == 1 and page.tracks[0].artist is None
    assert [(c.name,c.role) for c in page.tracks[0].credits] == [("Alice","Composer"),("Bob","Composer")]
    assert requests[0].url.path == "/robots.txt" and len(requests) == 2


@pytest.mark.parametrize("robots_status,body", [(200,"User-agent: *\nDisallow: /search"), (403,""), (500,"")])
async def test_html_robots_block_stops_search(robots_status, body):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(robots_status, text=body)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source = CustomSource(client, {}, definition(format="html", results_path="article"))
        with pytest.raises(SourceError):
            await source.search("Name")
    assert len(requests) == 1 and requests[0].url.path == "/robots.txt"


@pytest.mark.parametrize("auth", ["header","query"])
async def test_redirect_is_refused_without_forwarding_credentials(auth):
    requests = []
    config = definition(auth=auth, auth_name="X-Key", auth_prefix="")
    def handler(request):
        requests.append(request)
        return httpx.Response(302, headers={"Location":"https://another.example.org/steal"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False) as client:
        source = CustomSource(client, {config.credential_key:"SECRET"}, config)
        with pytest.raises(SourceError) as error:
            await source.search("Name")
    assert error.value.status == "unavailable" and len(requests) == 1
    assert requests[0].url.host == "catalog.example.org"
    assert (requests[0].headers["X-Key"] if auth == "header" else requests[0].url.params["X-Key"]) == "SECRET"
    assert "SECRET" not in error.value.message


async def test_missing_credentials_never_requests_search():
    config = definition(auth="header")
    requests = []
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req:requests.append(req))) as client:
        source = CustomSource(client, {}, config)
        with pytest.raises(SourceError) as error:
            await source.search("Name")
    assert error.value.status == "missing_credentials" and requests == []


async def test_external_source_only_builds_encoded_link():
    config = definition(format="external", params={"type":"album"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request:pytest.fail("External sources must not fetch"))) as client:
        source = CustomSource(client, {}, config)
        assert (await source.search("Name")).tracks == []
        assert source.external_url("Name & Co") == "https://catalog.example.org/search?type=album&q=Name+%26+Co"


async def test_public_transport_pins_dns_and_preserves_host_tls_identity(monkeypatch):
    seen = []
    async def resolve(host, port, **kwargs):
        assert host == "catalog.example.org" and port == 443
        return [(socket.AF_INET,socket.SOCK_STREAM,6,"",("93.184.216.34",443))]
    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"ok":True})
    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", resolve)
    transport = PublicTransport()
    await transport.transport.aclose()
    transport.transport = httpx.MockTransport(handle)
    async with httpx.AsyncClient(transport=transport) as client:
        response = await client.get("https://catalog.example.org/search", headers={"X-Key":"SECRET"})
    assert response.json() == {"ok":True}
    request = seen[0]
    assert request.url.host == "93.184.216.34"
    assert request.headers["Host"] == "catalog.example.org"
    assert request.extensions["sni_hostname"] == "catalog.example.org"
    assert request.headers["X-Key"] == "SECRET"


@pytest.mark.parametrize("addresses", [["127.0.0.1"],["10.0.0.1"],["169.254.169.254"],["::1"],["8.8.8.8","192.168.1.1"],[]])
async def test_public_transport_refuses_private_or_mixed_dns(monkeypatch, addresses):
    async def resolve(*args, **kwargs):
        return [(socket.AF_INET,socket.SOCK_STREAM,6,"",(address,443)) for address in addresses]
    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", resolve)
    transport = PublicTransport()
    await transport.transport.aclose()
    transport.transport = httpx.MockTransport(lambda request:pytest.fail("Private DNS must not connect"))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(SourceError):
            await client.get("https://catalog.example.org/search")


async def test_public_transport_bounds_body_and_refuses_compression(monkeypatch):
    async def resolve(*args, **kwargs):
        return [(socket.AF_INET,socket.SOCK_STREAM,6,"",("8.8.8.8",443))]
    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", resolve)
    class Stream(httpx.AsyncByteStream):
        def __init__(self, content): self.content = content
        async def __aiter__(self):
            yield self.content[:1_000_000]
            yield self.content[1_000_000:]
    for headers, content in (({},b"x"*2_000_001), ({"Content-Encoding":"gzip"}, b"not accepted")):
        transport = PublicTransport()
        await transport.transport.aclose()
        transport.transport = httpx.MockTransport(lambda req:httpx.Response(200,headers=headers,stream=Stream(content)))
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(SourceError):
                await client.get("https://catalog.example.org/search")


@pytest.mark.parametrize("field,value", [("url","https://127.0.0.1/song"),("url","https://localhost/song"),
    ("url","https://user:secret@catalog.example.org/song"),("artwork","https://192.168.1.2/cover.jpg"),
    ("artwork","https://localhost/cover.jpg")])
async def test_custom_source_rejects_private_result_links_and_artwork(field, value):
    config = definition(fields={"title":"title","url":"url","artwork":"artwork"})
    row = {"title":"Song","url":"https://catalog.example.org/song",field:value}
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={"results":[row]}))) as client:
        page = await CustomSource(client, {}, config).search("Song")
    assert page.tracks == [] and "1 registros" in page.notices[0]


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, transport=httpx.MockTransport(lambda request:httpx.Response(200,json={"results":[]})))
    with TestClient(app, base_url="http://127.0.0.1") as client:
        yield client


def test_custom_source_crud_and_profile_export_never_exposes_token(client):
    config = definition(auth="header")
    assert client.put("/api/custom-sources", json=config.model_dump(), headers=HEADERS).status_code == 200
    assert config.id in {s["id"] for s in client.get("/api/custom-sources").json()}
    assert client.put("/api/credentials",json={"values":{config.credential_key:"NEVER-RETURN-THIS"}},headers=HEADERS).status_code == 200
    assert next(s for s in client.get("/api/sources").json() if s["id"]==config.id)["configured"]
    profile = client.get("/api/profile")
    assert profile.status_code == 200 and "NEVER-RETURN-THIS" not in profile.text
    assert client.delete("/api/custom-sources/"+config.id,headers=HEADERS).status_code == 200
    assert config.id not in {s["id"] for s in client.get("/api/custom-sources").json()}
    assert config.credential_key not in client.app.state.engine.secrets
    assert client.delete("/api/custom-sources/"+config.id,headers=HEADERS).status_code == 404


def test_profile_import_validation_is_atomic(client):
    config = definition()
    original = client.get("/api/profile").json()
    changed = {"settings":{**original["settings"],"country":"US","theme":"dark"},"sources":[config.model_dump()]}
    assert client.put("/api/profile",json=changed,headers=HEADERS).status_code == 200
    saved = client.get("/api/profile").json()
    assert saved["settings"]["country"] == "US" and saved["sources"][0]["id"] == config.id
    for invalid in ({**changed,"sources":[config.model_dump(),config.model_dump()]},
                    {**changed,"sources":[{**config.model_dump(),"endpoint":"https://127.0.0.1/"}]},
                    {**changed,"settings":{**changed["settings"],"disabled_sources":["unknown_source"]}}):
        assert client.put("/api/profile",json=invalid,headers=HEADERS).status_code == 422
        assert client.get("/api/profile").json() == saved


def test_invalid_endpoint_api_returns_validation_error_without_echo(client):
    config = definition().model_dump()
    response = client.put("/api/custom-sources",json={**config,"endpoint":"https://catalog.example.org:SECRET/"},headers=HEADERS)
    assert response.status_code == 422 and "SECRET" not in response.text


def test_profile_reset_removes_user_sources_and_their_session_tokens(client):
    config = definition(auth="header")
    assert client.put("/api/custom-sources",json=config.model_dump(),headers=HEADERS).status_code == 200
    assert client.put("/api/credentials",json={"values":{config.credential_key:"SECRET"}},headers=HEADERS).status_code == 200
    assert client.delete("/api/profile",headers=HEADERS).status_code == 200
    profile = client.get("/api/profile").json()
    assert {s["id"] for s in profile["sources"]} == {s.id for s in source_presets()}
    assert profile["settings"] == Settings().model_dump()
    assert config.credential_key not in client.app.state.engine.secrets
