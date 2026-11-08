import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest

from everytune.sources import ADAPTERS
from everytune.sources.base import SourceError, retry_seconds

PAYLOADS = {
    "itunes": {"results":[{"kind":"song","trackId":1,"trackName":"Song","trackViewUrl":"https://music.apple.com/song","trackTimeMillis":123000}]},
    "musicbrainz": {"recordings":[{"id":"abc","title":"Song","artist-credit":[{"name":"Artist"}],"releases":[{"title":"Album"}]}],"count":30},
    "archive": {"response":{"docs":[{"identifier":"abc","title":"Song","creator":["Artist"]}],"numFound":30}},
    "audius": {"data":[{"id":"abc","title":"Song","user":{"name":"Artist","handle":"artist"},"slug":"song"}]},
    "openverse": {"results":[{"id":"abc","title":"Song","foreign_landing_url":"https://example.org/song","license":"by","url":"https://example.org/song.mp3"}],"page_count":2},
    "commons": {"query":{"pages":{"1":{"pageid":1,"title":"File:Song","imageinfo":[{"descriptionurl":"https://commons.wikimedia.org/song","extmetadata":{"LicenseShortName":{"value":"CC BY 4.0"}}}]}}},"continue":{"gsroffset":20}},
    "jamendo": {"headers":{"status":"success"},"results":[{"id":"abc","name":"Song","shareurl":"https://jamendo.com/song","audio":"https://example.org/song.mp3","audiodownload_allowed":False}]},
    "youtube": {"items":[{"id":{"videoId":"abc"},"snippet":{"title":"Song &amp; Title","channelTitle":"Uploader"}}],"nextPageToken":"next"},
    "spotify": {"tracks":{"items":[{"id":"abc","name":"Song","external_urls":{"spotify":"https://open.spotify.com/track/abc"},"artists":[{"name":"Artist"}]}],"next":"https://api.spotify.com/next"}},
    "soundcloud": {"collection":[{"id":1,"title":"Song","permalink_url":"https://soundcloud.com/artist/song","duration":123000}],"next_href":"https://api.soundcloud.com/next"},
    "applemusic": {"results":{"songs":{"data":[{"id":"abc","attributes":{"name":"Song","url":"https://music.apple.com/song","artistName":"Artist"}}],"next":"next"}}},
    "mixcloud": {"data":[{"key":"/user/song/","name":"Song","url":"https://www.mixcloud.com/user/song/"}],"paging":{"next":"next"}},
    "lastfm": {"results":{"trackmatches":{"track":[{"name":"Song","artist":"Artist","url":"http://www.last.fm/music/artist/song"}]},"opensearch:totalResults":"100"}},
}
EMPTY = {"itunes":{"results":[]},"musicbrainz":{"recordings":[],"count":0},"archive":{"response":{"docs":[],"numFound":0}},"audius":{"data":[]},"openverse":{"results":[],"page_count":0},"commons":{"batchcomplete":""},"jamendo":{"headers":{"status":"success"},"results":[]},"youtube":{"items":[]},"spotify":{"tracks":{"items":[]}},"soundcloud":{"collection":[]},"applemusic":{"results":{}}}
EMPTY.update(mixcloud={"data":[]},lastfm={"results":{"trackmatches":{"track":[]},"opensearch:totalResults":"0"}})


def mocked(source_cls, payload, statuses=None):
    calls = []
    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/api/token"):
            return httpx.Response(200,json={"access_token":"SECRET", "expires_in":3600})
        status = statuses.pop(0) if statuses else 200
        return httpx.Response(status,json=payload,headers={"Retry-After":"0"})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    source = source_cls(client,{k:"SECRET" for k in source_cls.credentials})
    source.interval = 0
    return client,source,calls


@pytest.mark.parametrize("source_cls",[cls for cls in ADAPTERS if cls.id in PAYLOADS],ids=lambda cls:cls.id)
async def test_each_adapter_normalizes_documented_shape(source_cls):
    client,source,calls = mocked(source_cls,PAYLOADS[source_cls.id])
    async with client:
        result = await source.search("Song",20)
    assert len(result.tracks) == 1
    track = result.tracks[0]
    assert track.source == source_cls.id
    assert track.title.startswith("Song")
    assert track.preview_url is None
    assert str(track.url).startswith("https://")
    if source_cls.id == "youtube":
        assert track.artist is None  # Uploading channel is not necessarily the performer.
    if source_cls.id in ("musicbrainz","archive","openverse","commons","youtube","spotify","soundcloud","applemusic"):
        assert result.next_cursor is not None


@pytest.mark.parametrize("source_cls",[cls for cls in ADAPTERS if cls.id in PAYLOADS],ids=lambda cls:cls.id)
async def test_empty_source_response(source_cls):
    client,source,_ = mocked(source_cls,EMPTY[source_cls.id])
    async with client:
        assert (await source.search("Nothing",20)).tracks == []


@pytest.mark.parametrize("code",[401,403,404,429,500])
async def test_http_errors_and_bounded_retries(code):
    client,source,calls=mocked(ADAPTERS[0],{},[code,code])
    async with client:
        with pytest.raises(SourceError) as error:
            await source.search("Song")
    assert error.value.status == ("rate_limit" if code==429 else "unavailable")
    assert len(calls)==(2 if code in (429,500) else 1)


async def test_retry_transient_failure():
    client,source,calls=mocked(ADAPTERS[0],EMPTY["itunes"],[500,200])
    async with client:
        assert not (await source.search("Song")).tracks
    assert len(calls)==2


async def test_retry_after_long_wait_is_not_ignored():
    def handler(request):
        return httpx.Response(429,headers={"Retry-After":"60"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=ADAPTERS[0](client,{})
        with pytest.raises(SourceError) as error:
            await source.search("Song")
        assert error.value.status=="rate_limit"
        assert source.blocked_until > 0
    assert retry_seconds("60")==60
    assert 1 <= retry_seconds(format_datetime(datetime.now(timezone.utc)+timedelta(seconds=3))) <= 3


async def test_network_failure_retries_once():
    calls=[]
    def handler(request):
        calls.append(request)
        raise httpx.ConnectError("offline",request=request)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=ADAPTERS[0](client,{})
        source.interval=0
        with pytest.raises(httpx.ConnectError):
            await source.search("Song")
    assert len(calls)==2


async def test_pagination_uses_cursor_without_following_upstream_url():
    cls=next(c for c in ADAPTERS if c.id=="musicbrainz")
    client,source,calls=mocked(cls,PAYLOADS[cls.id])
    async with client:
        await source.search("Águas: AND *",10,"20")
    assert calls[0].url.params["offset"]=="20"
    assert calls[0].url.params["query"]=='(recording:"Águas" OR artist:"Águas" OR release:"Águas") AND (recording:"AND" OR artist:"AND" OR release:"AND")'
