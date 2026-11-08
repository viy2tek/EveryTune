from scripts.verify_free_sites import mapping_for_html, targets_from_html
from everytune.models import SearchRequest, TrackResult, rank


def post(title):
    return TrackResult(source='web',source_id='1',platform='Site',category='Catalogues',title=title,url='https://example.org/post',kind='catalogue_post')


def test_site_mentions_are_exact_phrases_not_verified_music():
    result=rank([post('The Beatles - Abbey Road (1969)'),post('Tommy - An album')],'Beatles')
    assert len(result)==1 and result[0].matched_on=='mention'
    assert rank([post('Tommy - An album')],'Tom')==[]
    assert rank([post('Daft Punk - Get Lucky (Live)')],'Daft Punk - Get Lucky')==[]
    assert rank([post('The Beatles - Abbey Road')],SearchRequest(query='Beatles',mode='track').terms())==[]
    assert rank([post('The Beatles - Abbey Road')],SearchRequest(query='Beatles',mode='credits').terms())==[]


def test_html_mapping_does_not_accept_homepage_articles_as_search_matches():
    html='<article><h2><a href="/album">Other artist</a></h2></article>'
    assert mapping_for_html(html,'Beatles') is None
    assert mapping_for_html(html.replace('Other artist','The Beatles - Album'),'Beatles') is not None


def test_fmhy_section_boundary_and_deduplication():
    html='<h3 id="download-sites">Download</h3><ul><li><a href="https://site.example">Site</a> - rock</li></ul><h3 id="genre-specific-ripping">Genre</h3><ul><li><a href="https://site.example">Site</a></li></ul><h3>Other</h3><a href="https://excluded.example">No</a>'
    rows=targets_from_html(html)
    assert len(rows)==1 and len(rows[0]['sections'])==2


async def test_custom_page_does_not_lose_rows_beyond_user_limit():
    import httpx
    from everytune.source_config import SourceDefinition
    from everytune.sources.custom import CustomSource
    rows=[{'title':f'Beatles - Album {i}','url':f'https://example.org/{i}'} for i in range(5)]
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req:httpx.Response(200,json={'results':rows}))) as client:
        source=CustomSource(client,{},SourceDefinition(id='custom_test',name='Test',endpoint='https://example.org/search',kind='catalogue_post'))
        source.interval=0
        first=await source.search('Beatles',3,None)
        assert len(first.tracks)==3 and first.next_cursor=='1:3'
        second=await source.search('Beatles',3,first.next_cursor)
        assert len(second.tracks)==2 and second.next_cursor is None
