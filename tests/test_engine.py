import asyncio
from types import SimpleNamespace

import httpx
import pytest

from everytune.engine import SearchEngine
from everytune.models import SearchRequest, Settings, SourcePage
from everytune.sources.base import MusicSource
from everytune.storage import Store


class Fake(MusicSource):
    id,name,category,docs="fake","Fake","Test","https://example.org"
    async def search(self, query, limit=20, cursor=None):
        return SourcePage(tracks=[self.track("id","Song","https://example.org/song",artist="Artist")])


@pytest.fixture
def store(tmp_path):
    result=Store(tmp_path)
    yield result
    result.close()


async def test_parallel_completion_and_isolated_failure(store):
    ready=set()
    barrier=asyncio.Event()
    class Parallel(Fake):
        async def search(self,*args):
            ready.add(self.id)
            if len(ready)==2: barrier.set()
            await asyncio.wait_for(barrier.wait(),1)
            if self.id=="bad": raise ValueError("SECRET")
            return await super().search(*args)
    async with httpx.AsyncClient() as client:
        engine=SearchEngine(store,client,{})
        a,b=Parallel(client,{}),Parallel(client,{})
        a.id,b.id="good","bad"
        engine.sources={a.id:a,b.id:b}
        events=[e async for e in engine.events(SearchRequest(require_audio=False,query="Song",sources=["good","bad"]))]
    assert ready=={"good","bad"}
    final=events[-1]
    assert len(final["tracks"])==1
    assert {s["status"] for s in final["sources"]}=={"success","unavailable"}
    assert "SECRET" not in str(events)


async def test_cache_and_expiry(store,monkeypatch):
    async with httpx.AsyncClient() as client:
        engine=SearchEngine(store,client,{})
        source=Fake(client,{})
        request=SearchRequest(require_audio=False,query="Song")
        assert not (await engine.search_source(source,request,Settings()))["cached"]
        assert (await engine.search_source(source,request,Settings()))["cached"]
        monkeypatch.setattr("everytune.storage.time.time",lambda: 1e12)
        assert not (await engine.search_source(source,request,Settings()))["cached"]
        store.clear_cache()
        assert store.db.execute("SELECT count(*) FROM cache").fetchone()[0]==0


async def test_timeout_and_missing_credentials(store):
    class Slow(Fake):
        async def search(self,*args): await asyncio.sleep(1)
    async with httpx.AsyncClient() as client:
        engine=SearchEngine(store,client,{})
        result=await engine.search_source(Slow(client,{}),SearchRequest(require_audio=False,query="Song"),SimpleNamespace(max_results=10,timeout=.01,country="BR"))
        assert result["status"]=="timeout"
        result=await engine.search_source(engine.sources["youtube"],SearchRequest(require_audio=False,query="Song"),Settings())
        assert result["status"]=="missing_credentials"


async def test_invalid_json_and_bad_payload(store):
    for response in (httpx.Response(200,text="bad json"),httpx.Response(200,json={"results":[{}]})):
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request:response)) as client:
            engine=SearchEngine(store,client,{})
            result=await engine.search_source(engine.sources["itunes"],SearchRequest(require_audio=False,query="Song"),Settings())
            assert result["status"]=="unavailable"


def test_storage_persistence_and_history_bound(tmp_path):
    store=Store(tmp_path)
    store.save_settings(Settings(max_results=5))
    for i in range(105): store.remember(str(i))
    assert store.db.execute("SELECT count(*) FROM history").fetchone()[0]==100
    store.close()
    store=Store(tmp_path)
    assert store.settings().max_results==5
    assert store.history()[0]=="104"
    store.close()


async def test_concurrency_bound_and_cancel_cleanup(store):
    active=0
    peak=0
    cancelled=[]
    class Measured(Fake):
        async def search(self,*args):
            nonlocal active,peak
            active+=1
            peak=max(peak,active)
            try:
                await asyncio.sleep(.02)
                return await super().search(*args)
            finally:
                active-=1
                cancelled.append(self.id)
    async with httpx.AsyncClient() as client:
        engine=SearchEngine(store,client,{})
        engine.semaphore=asyncio.Semaphore(2)
        engine.sources={}
        for index in range(5):
            source=Measured(client,{})
            source.id=str(index)
            engine.sources[source.id]=source
        events=[event async for event in engine.events(SearchRequest(require_audio=False,query="Song"))]
        assert peak==2 and active==0
        assert len(events[-1]["tracks"])==5
        store.clear_cache()
        cancelled.clear()
        iterator=engine.events(SearchRequest(require_audio=False,query="Song"))
        assert (await anext(iterator))["type"]=="start"
        await asyncio.sleep(.005)
        await iterator.aclose()
        assert active==0 and len(cancelled)==2
