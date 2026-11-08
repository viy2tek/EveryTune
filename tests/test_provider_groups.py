import httpx
from fastapi.testclient import TestClient
from everytune.app import create_app

HEADERS={'X-EveryTune':'1'}


def test_groups_include_credentialed_streaming_and_filter_backend(tmp_path):
    app=create_app(tmp_path,transport=httpx.MockTransport(lambda r:httpx.Response(200,json={})))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        sources={s['id']:s for s in client.get('/api/sources').json()}
        assert sources['spotify']['provider_group']=='streaming'
        assert sources['spotify']['requires_credentials']
        assert sources['musicbrainz']['provider_group']=='community'
        assert sources['custom_ccmixter']['provider_group']=='community'
        assert sources['youtube_music']['provider_group']=='streaming'
        for scope,expected in [('streaming',{'spotify'}),('community',{'musicbrainz_credits'}),('both',{'spotify','musicbrainz_credits'})]:
            data=client.post('/api/search',headers=HEADERS,json={'require_audio':False,'query':'Name','sources':['spotify','musicbrainz_credits'],'provider_scope':scope}).json()
            assert {s['source'] for s in data['sources']}==expected


def test_custom_group_and_preferences_round_trip(tmp_path):
    app=create_app(tmp_path)
    with TestClient(app,base_url='http://127.0.0.1') as client:
        definition={'id':'custom_stream','name':'My platform','endpoint':'https://example.org/search','provider_group':'streaming'}
        assert client.put('/api/custom-sources',headers=HEADERS,json=definition).status_code==200
        settings=client.get('/api/settings').json();settings['provider_scope']='community'
        assert client.put('/api/settings',headers=HEADERS,json=settings).status_code==200
        profile=client.get('/api/profile').json()
        assert profile['settings']['provider_scope']=='community'
        assert next(s for s in profile['sources'] if s['id']=='custom_stream')['provider_group']=='streaming'


def test_raw_streaming_search_preserves_text_and_country(tmp_path):
    seen=[]
    def handler(request):
        seen.append(request)
        return httpx.Response(200,json={'results':[]})
    app=create_app(tmp_path,transport=httpx.MockTransport(handler))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        settings=client.get('/api/settings').json();settings['country']='US'
        client.put('/api/settings',headers=HEADERS,json=settings)
        result=client.post('/api/search',headers=HEADERS,json={'require_audio':False,'query':'Artist - Song','sources':['itunes'],'mode':'source'}).json()
        assert seen[0].url.params['country']=='US' and seen[0].url.params['term']=='Artist - Song'
        assert result['interpretation']['artist'] is None
