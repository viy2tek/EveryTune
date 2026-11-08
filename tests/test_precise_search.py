import httpx
import pytest

from everytune.engine import SearchEngine
from everytune.models import SearchRequest, SourcePage, TrackResult, rank
from everytune.sources import ADAPTERS
from everytune.storage import Store


def song(title="Stolen Flowers", artist="Soft Pillow Kisses", **kwargs):
    return TrackResult(source="test",source_id=title+str(artist),platform="Test",category="Test",title=title,artist=artist,url="https://example.org/song",**kwargs)


def test_interpret_artist_title_and_explicit_fields():
    terms=SearchRequest(require_audio=False,query="Soft Pillow Kisses - Stolen Flowers").terms()
    assert terms.artist=="Soft Pillow Kisses" and terms.title=="Stolen Flowers"
    assert SearchRequest(require_audio=False,query="AC-DC – Thunderstruck").terms().artist=="AC-DC"
    terms=SearchRequest(require_audio=False,query="ignored",artist="Artist - Name",title="Song - Live").terms()
    assert terms.artist=="Artist - Name" and terms.title=="Song - Live"


def test_reject_irrelevant_result_from_reported_regression():
    result=rank([song("Tear in My Heart","twenty one pilots")],"Soft Pillow Kisses - Stolen Flowers")
    assert result==[]


def test_exclude_labelled_cover_even_when_it_is_also_a_remix():
    cover=song('XXXTENTACION - SAD COVER (WARET REMIX )','WARET')
    remix=song('SAD (Artist Remix)','XXXTENTACION')
    terms=SearchRequest(require_audio=False,query='xxxtentacion',mode='source').terms()
    assert rank([cover,remix],terms)==[remix]
    assert remix.recording_type=='remix'
    assert rank([cover],terms.model_copy(update={'exclude_covers':False}))==[cover]


def test_artist_search_does_not_return_works_by_other_people():
    terms=SearchRequest(require_audio=False,query='xxxtentacion').terms()
    original=song('SAD!','XXXTENTACION')
    unrelated=song('Rockstars (Instrumental) [Produced by Magic Juand]','Magic Juand')
    assert rank([original,unrelated,song('XXXTENTACION - SAD COVER (WARET REMIX )','WARET')],terms)==[original]
    assert rank([song('SAD! (Remix)','XXXTENTACION')],SearchRequest(require_audio=False,query='XXXTENTACION - SAD!').terms())==[]


def test_legitimate_cover_word_in_title_is_not_a_cover_marker():
    for title in ['Cover Me','Cover Me in Sunshine','Under Cover']:
        assert rank([song(title)],SearchRequest(require_audio=False,query=title).terms())


def test_pair_requires_both_fields_on_same_record():
    rows=[song(),song(artist="Another artist"),song(title="Another song"),song(artist=None),
          song(title="Stolen Flowers - Live"),song(title="Stolen Flowers - Remastered"),
          song(artist="Soft Pillow Kisses Tribute Band"),song(kind="mix")]
    result=rank(rows,"Soft Pillow Kisses - Stolen Flowers")
    assert result==[rows[0]]
    assert result[0].matched_on=="artist_title"


def test_normalization_is_not_fuzzy_matching():
    assert len(rank([song("Águas de Março","Tom Jobim")],"TOM JOBIM — aguas de marco"))==1
    assert rank([song("Stolen Flower")],"Soft Pillow Kisses - Stolen Flowers")==[]
    assert rank([song("Flower Stolen")],"Soft Pillow Kisses - Stolen Flowers")==[]


def test_only_explicit_credited_artist_names_are_accepted():
    item=song(artist="Soft Pillow Kisses & Guest",artist_names=["Soft Pillow Kisses","Guest"])
    assert rank([item],"Soft Pillow Kisses - Stolen Flowers")==[item]
    grouped=rank([item,song()],"Soft Pillow Kisses - Stolen Flowers")
    assert grouped[0].group==grouped[1].group
    assert rank([song(artist="Soft Pillow Kisses & Guest")],"Soft Pillow Kisses - Stolen Flowers")==[]


def test_without_separator_requires_exact_name_and_never_word_overlap():
    assert rank([song()],"Stolen")==[]
    assert rank([song()],"Stolen Flowers")[0].matched_on=="title"
    assert rank([song()],"Soft Pillow Kisses")[0].matched_on=="artist"
    assert rank([song()],"Soft Pillow Kisses Stolen Flowers")==[]


async def test_engine_rechecks_cached_candidates_and_reports_rejections(tmp_path):
    payload={"results":[{"kind":"song","trackId":1,"trackName":"Tear in My Heart","artistName":"twenty one pilots","trackViewUrl":"https://music.apple.com/song"}]}
    store=Store(tmp_path)
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req:httpx.Response(200,json=payload))) as client:
            engine=SearchEngine(store,client,{})
            request=SearchRequest(require_audio=False,query="Soft Pillow Kisses - Stolen Flowers",sources=["itunes"])
            for cached in (False,True):
                events=[e async for e in engine.events(request)]
                result=events[-1]
                assert result["tracks"]==[]
                assert result["sources"][0]["status"]=="no_match"
                assert result["sources"][0]["rejected_count"]==1
                assert result["sources"][0]["cached"]==cached
                assert events[0]["interpretation"]["artist"]=="Soft Pillow Kisses"
    finally:store.close()


@pytest.mark.parametrize("id",["spotify","musicbrainz","lastfm"])
async def test_provider_specific_field_queries(id):
    calls=[]
    def handler(req):
        calls.append(req)
        if req.url.path.endswith('/api/token'):return httpx.Response(200,json={"access_token":"SECRET","expires_in":3600})
        return httpx.Response(200,json={"tracks":{"items":[]},"recordings":[],"count":0,"results":{"trackmatches":{"track":[]},"opensearch:totalResults":"0"}})
    cls=next(cls for cls in ADAPTERS if cls.id==id)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=cls(client,{k:"SECRET" for k in cls.credentials})
        source.interval=0
        await source.search_precise(SearchRequest(require_audio=False,query="Soft Pillow Kisses - Stolen Flowers").terms(),10,None)
    params=calls[-1].url.params
    if id=="spotify":
        assert params["q"]=='artist:"Soft Pillow Kisses" track:"Stolen Flowers"'
        assert params["market"]=="BR"
    elif id=="musicbrainz":assert params["query"]=='artist:"Soft Pillow Kisses" AND recording:"Stolen Flowers"'
    else:assert params["track"]=="Stolen Flowers" and params["artist"]=="Soft Pillow Kisses"


async def test_itunes_resolves_primary_artist_id_without_splitting_band_names():
    cls=next(cls for cls in ADAPTERS if cls.id=="itunes")
    calls=[]
    def handler(req):
        calls.append(req)
        if req.url.path=="/lookup":return httpx.Response(200,json={"results":[{"wrapperType":"artist","artistId":5468295,"artistName":"Daft Punk"}]})
        return httpx.Response(200,json={"results":[{"kind":"song","trackId":1,"trackName":"Get Lucky","artistId":5468295,"artistName":"Daft Punk, Pharrell Williams & Nile Rodgers","trackViewUrl":"https://music.apple.com/song"}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=cls(client,{})
        source.interval=0
        terms=SearchRequest(require_audio=False,query="Daft Punk - Get Lucky").terms()
        page=await source.search_precise(terms,15,None)
        assert len(rank(page.tracks,terms))==1
        assert page.tracks[0].artist_names==["Daft Punk"]
        assert calls[1].url.path=="/lookup"
        assert calls[1].url.params['id']=='5468295'


async def test_explicit_fields_scope_cache_and_external_links(tmp_path):
    payload={"results":[{"kind":"song","trackId":1,"trackName":"Song","artistName":"Artist","trackViewUrl":"https://music.apple.com/song"}]}
    store=Store(tmp_path)
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req:httpx.Response(200,json=payload))) as client:
            engine=SearchEngine(store,client,{})
            engine.sources['itunes'].interval=0
            for artist,status in (("Artist","success"),("Other artist","no_match")):
                events=[e async for e in engine.events(SearchRequest(require_audio=False,query="ignored",artist=artist,title="Song",sources=["itunes","bandcamp"]))]
                assert events[-1]['sources'][0]['status']==status
                assert not events[-1]['sources'][0]['cached']
                assert 'ignored' not in events[-1]['external'][0]['url']
            assert store.history()[0]=='Other artist - Song'
    finally:store.close()
