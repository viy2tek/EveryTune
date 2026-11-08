import httpx
from fastapi.testclient import TestClient
from everytune.app import create_app

HEADERS={'X-EveryTune':'1'}


def test_changing_source_destination_or_importing_profile_clears_session_key(tmp_path):
    app=create_app(tmp_path,transport=httpx.MockTransport(lambda req:httpx.Response(200,json={})))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        definition={'id':'custom_private','name':'User source','endpoint':'https://original.example/search','auth':'header'}
        assert client.put('/api/custom-sources',headers=HEADERS,json=definition).status_code==200
        client.put('/api/credentials',headers=HEADERS,json={'values':{'custom_private_token':'SECRET'}})
        definition['endpoint']='https://different.example/search'
        assert client.put('/api/custom-sources',headers=HEADERS,json=definition).status_code==200
        assert 'custom_private_token' not in app.state.engine.secrets
        client.put('/api/credentials',headers=HEADERS,json={'values':{'custom_private_token':'SECRET'}})
        profile=client.get('/api/profile').json()
        assert 'SECRET' not in str(profile)
        assert client.put('/api/profile',headers=HEADERS,json=profile).status_code==200
        assert 'custom_private_token' not in app.state.engine.secrets


def test_credentialed_streaming_is_available_but_not_queried_without_own_credentials(tmp_path):
    app=create_app(tmp_path,transport=httpx.MockTransport(lambda req: (_ for _ in ()).throw(AssertionError('Paid source must not be queried'))))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        ids={s['id'] for s in client.get('/api/sources').json()}
        assert {'spotify','applemusic','soundcloud'}<=ids
        result=client.post('/api/search',headers=HEADERS,json={'query':'Song','sources':['spotify','applemusic','soundcloud']}).json()
        assert result['tracks']==[] and all(s['status']=='missing_credentials' for s in result['sources'])
