import json
import socket

import httpx
import pytest
from fastapi.testclient import TestClient

from everytune.app import create_app
from everytune.launcher import reserve_port

HEADERS={"X-EveryTune":"1"}


@pytest.fixture
def client(tmp_path):
    app=create_app(tmp_path,transport=httpx.MockTransport(lambda request:httpx.Response(200,json={"results":[]})))
    with TestClient(app,base_url="http://127.0.0.1") as client:
        yield client


def test_local_server_and_static_files(client):
    assert client.get("/api/health").json()["status"]=="ok"
    assert "EveryTune" in client.get("/").text
    for path in ["app.js","style.css","icon.svg","ui-policy.mjs","home.mjs","home.css","home-adapter.js"]:
        assert client.get("/static/"+path).status_code==200
    assert 'javascript' in client.get('/static/ui-policy.mjs').headers['content-type']
    assert client.get("/openapi.json").status_code==200
    assert "frame-ancestors 'none'" in client.get("/").headers["content-security-policy"]


def test_search_rest_stream_empty_and_history(client):
    body={"query":"Song", "sources":["itunes"],"require_audio":False}
    result=client.post("/api/search",json=body,headers=HEADERS).json()
    assert result["tracks"]==[]
    assert result["sources"][0]["status"]=="empty"
    events=[json.loads(l) for l in client.post("/api/search/stream",json=body,headers=HEADERS).text.splitlines()]
    assert [e["type"] for e in events]==["start","source","complete"]
    assert events[1]["cached"]
    assert client.get("/api/history").json()==["Song"]
    assert client.get("/api/integrations").json()["itunes"]["status"]=="empty"


def test_settings_credentials_not_returned_or_stored(client):
    assert client.put("/api/credentials",json={"values":{"youtube_api_key":"SECRET"}},headers=HEADERS).status_code==200
    assert "SECRET" not in client.get("/api/sources").text
    assert "SECRET" not in client.get("/api/settings").text
    assert "SECRET" not in client.get("/api/logs").text
    source=next(s for s in client.get("/api/sources").json() if s["id"]=="youtube")
    assert source["configured"]
    db=client.app.state.store.db
    for table in ("cache","settings","logs","history"):
        assert "SECRET" not in str(db.execute(f"SELECT * FROM {table}").fetchall())
    result=client.put("/api/credentials",json={"values":{"unknown":"SECRET"}},headers=HEADERS)
    assert result.status_code==422 and "SECRET" not in result.text
    assert client.put("/api/settings",json={"max_results":5,"disabled_sources":["itunes"]},headers=HEADERS).status_code==200
    assert client.get("/api/settings").json()["max_results"]==5
    result=client.post("/api/search",json={"query":"Song","sources":["itunes"]},headers=HEADERS).json()
    assert result["sources"]==[]
    assert client.delete("/api/cache",headers=HEADERS).status_code==200


def test_trust_boundary_and_validation_do_not_echo_secrets(client):
    assert client.post("/api/search",json={"query":"Song"}).status_code==403
    assert client.post("/api/search",json={"query":"Song"},headers={**HEADERS,"Origin":"https://evil.example"}).status_code==403
    assert client.get("/api/settings",headers={"Host":"evil.example"}).status_code==400
    assert client.get("/api/sources",headers={"Sec-Fetch-Site":"cross-site"}).status_code==403
    assert client.post("/api/search",json={"query":"Song","sources":["https://evil.example"]},headers=HEADERS).status_code==422
    assert client.post("/api/search",json={"query":" "},headers=HEADERS).status_code==422
    result=client.put("/api/credentials",json={"values":{"youtube_api_key":{"SECRET":"SECRET"}}},headers=HEADERS)
    assert result.status_code==422 and "SECRET" not in result.text


def test_external_links_are_not_track_results(client):
    result=client.post("/api/search",json={"query":"song & title","sources":["bandcamp"],"require_audio":False},headers=HEADERS).json()
    assert result["tracks"]==[] and result["sources"]==[]
    assert result["external"][0]["url"]=="https://bandcamp.com/search?q=song%20%26%20title&item_type=t"


def test_port_collision_and_reservation():
    with reserve_port(0) as first:
        port=first.getsockname()[1]
        with reserve_port(port) as second:
            assert second.getsockname()[0]=="127.0.0.1"
            assert second.getsockname()[1]!=port
