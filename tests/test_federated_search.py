import httpx
import pytest

from everytune.models import SearchRequest, TrackResult, rank
from everytune.source_config import SourceDefinition
from everytune.sources.custom import CustomSource


def test_source_mode_preserves_query_and_candidate_order_without_verifying_names():
    terms = SearchRequest(query='Artist - Song', mode='source').terms()
    assert terms.artist is None and terms.title is None
    assert terms.query_text == 'Artist - Song'
    tracks = [TrackResult(source='fixture',source_id=str(i),platform='Fixture',category='Music',
        title=title,url=f'https://example.org/{i}') for i,title in enumerate(['Zebra remix','A different artist'])]
    results = rank(tracks, terms)
    assert [t.title for t in results] == ['Zebra remix','A different artist']
    assert all(t.matched_on == 'source' and t.match != 'exact' for t in results)
    assert rank(tracks, SearchRequest(query='Artist - Song').terms()) == []


@pytest.mark.asyncio
async def test_post_source_returns_origin_candidates_without_title_filter():
    seen = []
    def handler(request):
        seen.append(request)
        if request.url.path == '/robots.txt':
            return httpx.Response(200,text='User-agent: *\nAllow: /')
        return httpx.Response(200,text='<article><a href="/one">A different title</a></article><article><a href="/two">Second result</a></article>',headers={'Content-Type':'text/html'})
    config = SourceDefinition(id='custom_post', name='POST website', format='html',
        endpoint='https://example.org/', method='POST', query_param='story', params={'do':'search'},
        results_path='article',fields={'title':'a','url':'a@href'},kind='catalogue_post',limit_param=None)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=CustomSource(client,{},config)
        page=await source.search_precise(SearchRequest(query='Exact input & accents é',mode='source').terms(),1,None)
        next_page=await source.search_precise(SearchRequest(query='Exact input & accents é',mode='source').terms(),1,page.next_cursor)
    assert [t.title for t in page.tracks+next_page.tracks]==['A different title','Second result']
    request=seen[1]
    assert request.method=='POST' and request.url.query==b''
    assert b'story=Exact+input+%26+accents+%C3%A9' in request.content and b'do=search' in request.content


def test_post_external_shortcut_is_rejected():
    with pytest.raises(ValueError):
        SourceDefinition(id='custom_post',name='Unsafe shortcut',format='external',method='POST',endpoint='https://example.org/')


@pytest.mark.asyncio
async def test_json_feed_alternate_links_missing_entries_and_one_based_pagination():
    seen=[]
    def handler(request):
        seen.append(request)
        if request.url.path=='/robots.txt':
            return httpx.Response(200,text='User-agent: *\nDisallow: /search\nAllow: /feeds/')
        if request.url.params['q']=='missing':
            return httpx.Response(200,json={'feed':{}})
        return httpx.Response(200,json={'feed':{'entry':[{'title':{'$t':title},'link':[{'rel':'edit','href':'https://example.org/api'},{'rel':'alternate','href':f'https://example.org/{i}'}]} for i,title in enumerate(['First','Second'])]}})
    config=SourceDefinition(id='custom_feed',name='Feed',format='json',endpoint='https://example.org/feeds/posts/default',
        respect_robots=True,results_path='feed.entry',results_optional=True,
        fields={'title':'title.$t','url':'link[rel=alternate].href'},page_param='start-index',page_mode='index',limit_param='max-results')
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=CustomSource(client,{},config)
        page=await source.search('query',2)
        empty=await source.search('missing',2)
    assert [str(t.url) for t in page.tracks]==['https://example.org/0','https://example.org/1']
    assert page.next_cursor=='3' and seen[1].url.params['start-index']=='1'
    assert empty.tracks==[] and empty.next_cursor is None


@pytest.mark.asyncio
async def test_json_post_encoding_and_path_query_boundaries():
    seen=[]
    def handler(request):
        seen.append(request)
        return httpx.Response(200,json={'data':[{'title':'One','url':'https://example.org/song'}]})
    config=SourceDefinition(id='custom_json_post',name='JSON POST',endpoint='https://example.org/search/',method='POST',request_encoding='json',
        query_in_path=True,params={'type':'1'},results_path='data')
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await CustomSource(client,{},config).search('AC/DC ? #é',3)
    assert seen[0].url.raw_path.startswith(b'/search/AC%2FDC%20%3F%20%23%C3%A9')
    assert seen[0].headers['content-type']=='application/json'
    assert seen[0].url.query==b''


@pytest.mark.asyncio
async def test_robots_checks_search_query_not_only_homepage():
    from everytune.sources.base import SourceError
    seen=[]
    def handler(request):
        seen.append(request)
        return httpx.Response(200,text='User-agent: *\nDisallow: /?s=')
    config=SourceDefinition(id='custom_robots',name='Search',format='html',endpoint='https://example.org/',query_param='s',results_path='article')
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SourceError):
            await CustomSource(client,{},config).search('test')
    assert len(seen)==1


def test_new_pack_migration_preserves_existing_edits_and_removals(tmp_path):
    from everytune.storage import Store
    store=Store(tmp_path)
    old=SourceDefinition(id='custom_old',name='Edited',endpoint='https://example.org/old')
    new=SourceDefinition(id='custom_new',name='New',endpoint='https://example.org/new')
    store.initialize_sources([old])
    store.delete_source(old.id)
    store.initialize_sources([new],key='source_federated_v1')
    assert [s.id for s in store.source_definitions()]==[new.id]
    store.delete_source(new.id)
    store.initialize_sources([new],key='source_federated_v1')
    assert store.source_definitions()==[]
    store.close()


@pytest.mark.asyncio
async def test_long_source_interval_returns_status_without_blocking_other_searches():
    import time
    from everytune.sources.base import SourceError
    config=SourceDefinition(id='custom_slow',name='Slow site',endpoint='https://example.org/',interval=60)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:(_ for _ in ()).throw(AssertionError('No network before interval')))) as client:
        source=CustomSource(client,{},config)
        source.last_request=time.monotonic()
        with pytest.raises(SourceError) as error:
            await source.search('test')
    assert error.value.status=='rate_limit'
