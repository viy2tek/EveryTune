import httpx

from everytune.models import SearchRequest,rank
from everytune.sources.deezer import Deezer


async def test_deezer_credits_require_named_contributor_not_search_hit():
    def handler(req):
        if req.url.path=='/search':
            return httpx.Response(200,json={'data':[{'id':1,'title':'BODY','link':'https://www.deezer.com/track/1','artist':{'name':'Another artist'}}], 'total':1})
        return httpx.Response(200,json={'contributors':[{'id':42,'name':'viy2tek','role':'Featured'},{'id':9,'name':'Another artist','role':'Main'}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=Deezer(client,{})
        source.interval=0
        terms=SearchRequest(query='viy2tek',mode='credits').terms()
        page=await source.search_precise(terms,10,None)
        result=rank(page.tracks,terms)
        assert len(result)==1 and result[0].artist=='Another artist'
        assert any(c.name=='viy2tek' and c.role=='Featured' and c.person_id=='42' for c in result[0].credits)
        assert rank(page.tracks,SearchRequest(query='Unknown',mode='credits').terms())==[]
        assert rank(page.tracks,SearchRequest(query='viy2tek',mode='credits',identities={'deezer':'99'}).terms())==[]


async def test_deezer_homonyms_require_selection():
    def handler(req):
        if req.url.path=='/search':
            return httpx.Response(200,json={'data':[{'id':1,'title':'Song','link':'https://www.deezer.com/track/1','artist':{'name':'A'}}], 'total':1})
        return httpx.Response(200,json={'contributors':[{'id':1,'name':'Same Name','role':'Main'},{'id':2,'name':'Same Name','role':'Featured'}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=Deezer(client,{});source.interval=0
        page=await source.search_precise(SearchRequest(query='Same Name',mode='credits').terms(),10,None)
        assert len(page.people)==2 and page.tracks==[]
