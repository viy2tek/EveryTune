"""Discover offered files and prepare selected originals/ZIPs without executing media."""
import asyncio
import hashlib
import logging
import mimetypes
from collections import OrderedDict
from email.message import Message
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import tempfile
import time
from urllib.parse import quote, unquote, urljoin, urlsplit
from urllib.robotparser import RobotFileParser
import zipfile

from bs4 import BeautifulSoup
import httpx

from .public_http import public_url
from .sources.base import SourceError
from .sources import EXTERNAL
from .sources.openverse import DOWNLOAD_LICENSES
from .models import TrackResult
from .audio_quality import declared_quality,inspect_audio,MAX_HEADER

logger=logging.getLogger('everytune')

AUDIO={'mp3','flac','wav','wave','ogg','opus','m4a','aac','aiff','aif','alac','ape','wv','wma','dsf','dff','mid','midi','vgz','vgm','mod','xm','it','s3m','spc','nsf','sid'}
ARCHIVES={'zip','7z','rar','gz','tar','bz2','xz'}
DOCUMENTS={'pdf','txt','nfo','cue','lrc','lyrics','ly','m3u','m3u8','pls','epub','musicxml','mxl','mscz','gp3','gp4','gp5','gpx','srt','ass'}
ARTWORK={'jpg','jpeg','png','webp','gif','tiff'}
MEDIA_AUDIO=AUDIO-{'mid','midi','vgz','vgm','mod','xm','it','s3m','spc','nsf','sid'}
FILE_TYPES=AUDIO|ARCHIVES|DOCUMENTS|ARTWORK|{'torrent','xml','json','sfv','md5','sha1','mp4','mkv','webm','mov','avi','sf2','sfz','flp','als','rpp','logicx'}
HOST_PAGES={'mega.nz','mega.io','mediafire.com','drive.google.com','docs.google.com','gofile.io','pixeldrain.com','1fichier.com','rapidgator.net','turbobit.net','katfile.com','ddownload.com','krakenfiles.com','workupload.com','send.cm','buzzheavier.com','nitroflare.com','uploadgig.com','fikper.com','filecrypt.cc','filecrypt.co','protected.to','dropbox.com','disk.yandex.com','disk.yandex.ru','yadi.sk'}
NO_EXPORT={'itunes','applemusic','spotify','deezer','youtube','youtube_music','mixcloud','lastfm','musicbrainz','musicbrainz_credits','discogs'}


def safe_filename(value):
    value=unquote(str(value)).replace('\\','/').rsplit('/',1)[-1]
    value=re.sub(r'[\x00-\x1f<>:"/\\|?*]','_',value).strip(' .')[:180] or 'arquivo'
    if value.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:
        value='_'+value
    return value


def file_kind(filename):
    extension=Path(filename).suffix.lower().lstrip('.')
    return 'audio' if extension in AUDIO else 'archive' if extension in ARCHIVES else 'document' if extension in DOCUMENTS else 'artwork' if extension in ARTWORK else 'other'


def media_kind(asset):
    extension=Path(asset.get('filename','')).suffix.lower().lstrip('.')
    if extension in MEDIA_AUDIO:return 'audio'
    if extension in ARTWORK:return 'artwork'
    return None


def media_mime(mime,kind):
    mime=mime.split(';',1)[0].strip().lower()
    return mime.startswith('audio/' if kind=='audio' else 'image/') or mime in (
        {'application/octet-stream','binary/octet-stream','application/ogg','application/x-flac'} if kind=='audio' else {'application/octet-stream','binary/octet-stream'})


def offered(url, filename=None, **values):
    public_url(url)
    filename=safe_filename(filename or unquote(urlsplit(url).path.rsplit('/',1)[-1]))
    return {'url':url,'filename':filename,'format':Path(filename).suffix.lstrip('.').upper() or None,'kind':file_kind(filename),'size':None,'delivery':'direct','label':filename,**values}


def page_assets(html, page_url, selector=None):
    soup=BeautifulSoup(html,'html.parser')
    for node in soup.select('script,style,template'):node.decompose()
    assets=[];seen=set()
    content=soup
    if not selector:
        post_id=next((c.removeprefix('postid-') for c in (soup.body.get('class',[]) if soup.body else []) if re.fullmatch(r'postid-\d+',c)),None)
        primary=soup.find(id='post-'+post_id) if post_id else None
        content=primary or next((node for css in ('article[id^="post-"]','.post[id^="post-"]','main','#dle-content','#content','.post-outer','article','.post-body','.entry-content') if (node:=soup.select_one(css)) is not None),soup)
    anchors=list(content.select(selector or 'a[href]'))
    if not selector:
        urls=re.findall(r'https://[^\s<>"\'\[\]]+',content.get_text(' ',strip=True))[:500]
        for button in content.select('[data-download],[data-url],[data-href]'):
            if button.has_attr('data-download') or re.search(r'download|baixar|mirror|espelho',button.get_text(' ',strip=True),re.I):
                urls.append(button.get('data-download') or button.get('data-url') or button.get('data-href'))
        for url in urls:
            if not url:continue
            anchor=soup.new_tag('a',href=url.rstrip('.,;'));anchor.string='Link publicado na origem';anchors.append(anchor)
    for anchor in anchors:
        if len(assets)>=500:break
        href=anchor.get('href','').strip()
        label=anchor.get_text(' ',strip=True)[:300]
        if href.startswith('magnet:?') and re.search(r'[?&]xt=urn:btih:',href,re.I):
            if href not in seen and len(href)<=5000:
                assets.append({'url':href,'label':label or 'Magnet','filename':'magnet','format':'MAGNET','kind':'other','size':None,'delivery':'external'})
                seen.add(href)
            continue
        url=urljoin(page_url,href)
        extension=Path(unquote(urlsplit(url).path)).suffix.lower().lstrip('.')
        host=urlsplit(url).hostname or ''
        host_page=any(host==h or host.endswith('.'+h) for h in HOST_PAGES)
        if not href or href.startswith('#') or url==page_url or url in seen:
            continue
        explicit=bool(re.search(r'download|baixar|mirror|espelho|magnet',label+' '+urlsplit(url).path,re.I))
        if extension not in FILE_TYPES and not anchor.has_attr('download') and not explicit and not selector and not host_page:
            continue
        try:
            host=public_url(url).host
            external=host_page
            declared_file=selector and extension and extension not in {'html','htm','php','aspx','asp','jsp'}
            delivery='external' if external or (extension not in FILE_TYPES and not anchor.has_attr('download') and not declared_file) else 'direct'
            asset=offered(url,anchor.get('download') or None,label=label or safe_filename(urlsplit(url).path),delivery=delivery)
            if delivery=='external' and extension not in FILE_TYPES:asset['format']=None
            if not asset['format']:
                label_format=re.search(r'\b(FLAC|MP3|WAV|OGG|OPUS|M4A|AAC|AIFF|ALAC|ZIP|RAR|7Z|PDF|MIDI|MID|VGZ|VGM)\b',label,re.I)
                if label_format:asset['format']=label_format.group(1).upper()
            assets.append(asset)
            seen.add(url)
        except ValueError:
            continue
        if len(assets)>=500:break
    return assets


def is_true(value):
    return value is True or str(value).lower() in {'true','1','yes'}


def archive_assets(payload, identifier):
    if is_true(payload.get('is_dark')) or is_true((payload.get('metadata') or {}).get('access-restricted-item')):
        return []
    assets=[]
    for file in payload.get('files',[]):
        name=file.get('name','')
        if not name or is_true(file.get('private')) or '..' in name.replace('\\','/').split('/'):
            continue
        size=str(file.get('size',''))
        assets.append(offered(f'https://archive.org/download/{quote(identifier,safe="")}/{quote(name,safe="/")}',name,
            format=file.get('format') or Path(name).suffix.lstrip('.').upper() or None,size=int(size) if size.isdecimal() else None))
        if len(assets)>=500:break
    return assets


def openverse_assets(payload, title):
    if payload.get('license') not in DOWNLOAD_LICENSES:
        return []
    alternatives=payload.get('alt_files') or []
    if isinstance(alternatives,dict):
        alternatives=[alternatives] if 'url' in alternatives else list(alternatives.values())
    assets=[]
    for item in [payload]+(alternatives[:499] if isinstance(alternatives,list) else []):
        if not isinstance(item,dict) or not item.get('url'):
            continue
        fmt=str(item.get('filetype') or '').lower().lstrip('.')
        extension={'mp31':'mp3','mp32':'mp3'}.get(fmt,fmt)
        if extension not in AUDIO:
            extension=Path(urlsplit(str(item['url'])).path).suffix.lstrip('.').lower()
        if extension not in AUDIO:
            continue
        try:
            assets.append(offered(item['url'],f'{title}.{extension}',format=extension.upper(),
                size=item.get('filesize'),label=f'{extension.upper()} oferecido pela origem',
                quality=declared_quality({k:item.get(k) for k in ('bit_rate','sample_rate')})))
        except (ValueError,TypeError):
            continue
    return assets


class DownloadManager:
    def __init__(self, metadata_client, transfer_client, store):
        self.metadata_client,self.transfer_client,self.store=metadata_client,transfer_client,store
        self.engine=None
        self.refs=OrderedDict();self.index={};self.jobs=OrderedDict();self.tasks={};self.robots={}
        self.semaphore=asyncio.Semaphore(2)
        self.temp=tempfile.TemporaryDirectory(prefix='everytune-downloads-',ignore_cleanup_errors=True)
        self.directory=Path(self.temp.name).resolve()
        self.resolve_locks={}
        self.page_locks={};self.page_times={};self.page_delays={}
        self.janitor=asyncio.create_task(self._cleanup_loop())

    def register(self, track):
        if track.source in NO_EXPORT:
            track.file_access='catalogue'
            return None
        track.file_access='offered' if track.downloadable is True else 'discover'
        key=(track.source,track.source_id,str(track.url))
        ref=self.index.get(key)
        if ref in self.refs:
            self.refs[ref]['at']=time.monotonic();self.refs.move_to_end(ref)
            return ref
        ref=secrets.token_urlsafe(24)
        self.refs[ref]={'track':track.model_copy(deep=True),'at':time.monotonic(),'assets':{},'notices':[],'resolved':False}
        self.index[key]=ref
        while len(self.refs)>2000:
            old,row=self.refs.popitem(last=False)
            self.index.pop((row['track'].source,row['track'].source_id,str(row['track'].url)),None)
            self.resolve_locks.pop(old,None)
        return ref

    def record(self, ref):
        if ref not in self.refs or time.monotonic()-self.refs[ref]['at']>7200:
            raise KeyError('Resultado expirado; faça a pesquisa novamente.')
        return self.refs[ref]

    def source_enabled(self, id):
        return not self.engine or any(s['id']==id and s['enabled'] for s in self.engine.catalogue())

    async def inspect(self, source_id, url):
        if not self.engine:raise ValueError('Catálogo indisponível.')
        source=next((s for s in self.engine.catalogue() if s['id']==source_id and s['enabled']),None)
        definition=self.engine.definitions.get(source_id)
        external=next((s for s in EXTERNAL if s[0]==source_id),None)
        native={'archive':'https://archive.org/','commons':'https://commons.wikimedia.org/'}
        if not source or not (definition or external or source_id in native):raise ValueError('Escolha uma fonte configurável, acervo ou pesquisa externa habilitada.')
        endpoint=definition.endpoint if definition else native[source_id] if source_id in native else external[3]
        expected=urlsplit(endpoint).hostname.removeprefix('www.')
        actual=public_url(url).host.removeprefix('www.')
        if actual!=expected and not actual.endswith('.'+expected):raise ValueError('O endereço precisa pertencer ao domínio da fonte escolhida.')
        identifier=hashlib.sha256(url.encode()).hexdigest()[:24]
        if source_id=='archive':
            match=re.fullmatch(r'/details/([^/]+)/?',urlsplit(url).path)
            if not match:raise ValueError('Use a página /details/identificador do item no Internet Archive.')
            identifier=unquote(match.group(1))
        if source_id=='commons':
            path=unquote(urlsplit(url).path)
            if not path.startswith('/wiki/File:'):raise ValueError('Use a página /wiki/File:Nome do Wikimedia Commons.')
            identifier=path.removeprefix('/wiki/')
        item=TrackResult(source=source_id,source_id=identifier,platform=source['name'],category=source['category'],title='Página na origem',url=url,provider_group=source['provider_group'],kind='catalogue_post')
        return await self.resolve(self.register(item))

    def set_assets(self, ref, assets, notices=None):
        record=self.record(ref);record['assets']={};seen=set()
        for asset in assets[:500]:
            url=asset['url']
            if asset.get('delivery')!='external' or not url.startswith('magnet:?'):
                public_url(url)
            if url in seen:continue
            seen.add(url)
            id=secrets.token_urlsafe(12)
            record['assets'][id]={'delivery':'direct','label':asset.get('filename','Arquivo'),'format':None,'size':None,'kind':'other',**asset,'filename':safe_filename(asset.get('filename') or asset.get('label') or 'arquivo')}
            stored=record['assets'][id]
            fmt=str(stored.get('format') or '').lower().split(' ',1)[0]
            fmt={'mp31':'mp3','mp32':'mp3','jpeg':'jpg'}.get(fmt,fmt)
            if not media_kind(stored) and fmt in MEDIA_AUDIO|ARTWORK:
                stored['filename']=safe_filename(stored['filename']+'.'+fmt)
            if type(record['assets'][id].get('size')) is not int or record['assets'][id]['size']<0:
                record['assets'][id]['size']=None
        record.update(notices=notices or [],resolved=True,resolved_at=time.monotonic())

    def manifest(self, ref):
        record=self.record(ref);track=record['track']
        options=[]
        for id,asset in record['assets'].items():
            if not media_kind(asset):continue
            item={k:asset.get(k) for k in ('label','filename','format','size','kind','delivery')}
            item['kind']=media_kind(asset)
            item['quality']=declared_quality(asset.get('quality') or {}) if item['kind']=='audio' else None
            options.append({'id':id,**item,'open_url':asset['url'] if asset['delivery']=='external' else None})
        return {'ref':ref,'source':track.platform,'title':track.title,'page_url':str(track.url),'license':track.license,'options':options,'notices':record['notices']}

    async def confirm_audio(self,ref):
        record=self.record(ref)
        if not record['resolved'] or time.monotonic()-record.get('resolved_at',0)>30:
            await self.resolve(ref)
        failure=None
        for id,asset in list(record['assets'].items()):
            if media_kind(asset)!='audio':continue
            try:
                if asset['delivery']=='external':
                    await self.probe(ref,id)
                if asset['delivery']!='direct':continue
                response=await self._get(self.transfer_client,asset['url'],headers=asset.get('headers'),stream=True,method='HEAD')
                try:
                    size=response.headers.get('content-length')
                    disposition=Message();disposition['content-disposition']=response.headers.get('content-disposition','')
                    filename=disposition.get_filename()
                    if filename and media_kind({'filename':safe_filename(filename)})!='audio':continue
                    if size=='0' or not media_mime(response.headers.get('content-type',''),'audio'):continue
                    asset['audio_verified']=True
                    return True
                finally:await response.aclose()
            except (SourceError,httpx.RequestError,ValueError) as error:
                failure=error
                continue
        if failure:raise failure
        return False

    async def _get(self, client, url, *, headers=None, stream=False, robots=False, allowed_status=(), method='GET'):
        headers=dict(headers or {})
        for _ in range(6):
            public_url(url)
            if robots:await self.check_robots(url)
            request=client.build_request(method,url,headers=headers)
            response=await client.send(request,stream=stream)
            if response.status_code in (301,302,303,307,308):
                following=urljoin(url,response.headers.get('location',''))
                await response.aclose()
                public_url(following)
                if urlsplit(following).netloc!=urlsplit(url).netloc:headers={}
                if following==url:break
                url=following
                continue
            if response.status_code>=300 and response.status_code not in allowed_status:
                await response.aclose()
                raise SourceError('rate_limit' if response.status_code==429 else 'unavailable',f'A origem recusou o arquivo/página (HTTP {response.status_code}).')
            return response
        raise SourceError('unavailable','Redirecionamentos demais na origem.')

    async def check_robots(self, url):
        origin=urlsplit(url)._replace(path='',query='',fragment='').geturl()
        rules=self.robots.get(origin)
        if rules is None:
            response=await self._get(self.metadata_client,origin+'/robots.txt',allowed_status=(404,410))
            rules=RobotFileParser();rules.parse(response.text.splitlines() if response.status_code==200 else [])
            self.robots[origin]=rules
        if not rules.can_fetch('EveryTune',url):
            raise SourceError('unavailable','A origem restringe a leitura automatizada desta página.')
        delay=max(rules.crawl_delay('EveryTune') or rules.crawl_delay('*') or 1,self.page_delays.get(origin,0))
        async with self.page_locks.setdefault(origin,asyncio.Lock()):
            remaining=max(0,delay-(time.monotonic()-self.page_times.get(origin,0)))
            if remaining>30:raise SourceError('rate_limit',f'Aguarde {int(remaining)+1} segundos antes de consultar outra página desta origem.')
            await asyncio.sleep(remaining)
            self.page_times[origin]=time.monotonic()

    async def resolve(self, ref):
        async with self.resolve_locks.setdefault(ref,asyncio.Lock()):
            record=self.record(ref);track=record['track'];assets=[];notices=[]
            source=self.engine.sources.get(track.source) if self.engine else None
            if not self.source_enabled(track.source):
                raise ValueError('A fonte foi removida ou desativada.')
            if track.source=='archive':
                response=await self._get(self.metadata_client,f'https://archive.org/metadata/{quote(track.source_id,safe="")}')
                data=response.json();assets=archive_assets(data,track.source_id)
                metadata=data.get('metadata') or {}
                if metadata.get('title'):track.title=str(metadata['title'])[:2000]
                if isinstance(metadata.get('licenseurl'),str):track.license=metadata['licenseurl']
                if len(data.get('files',[]))>500:notices.append('A origem lista mais de 500 arquivos; mostrando os primeiros 500 públicos.')
            elif track.source=='openverse':
                response=await self._get(self.metadata_client,f'https://api.openverse.org/v1/audio/{quote(track.source_id,safe="")}/')
                data=response.json()
                if str(data.get('id'))!=track.source_id:
                    raise ValueError('O Openverse devolveu outro registro; refaça a pesquisa.')
                assets=openverse_assets(data,track.title)
                track.license=data.get('license_url') or data.get('license')
                notices.append('Arquivos informados pela API do Openverse; acesso será conferido durante a transferência. A licença informada não comprova upload oficial.')
                if data.get('creator'):
                    notices.append(f'Crédito informado na origem: {str(data["creator"])[:1000]}. Preserve a atribuição e as condições da licença ao usar o arquivo.')
            elif track.source=='commons':
                url=httpx.URL('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json','pageids' if track.source_id.isdecimal() else 'titles':track.source_id,'prop':'imageinfo','iiprop':'url|mime|size|extmetadata'})
                response=await self._get(self.metadata_client,str(url))
                for page in response.json().get('query',{}).get('pages',{}).values():
                    for info in page.get('imageinfo',[]):
                        if info.get('url'):assets.append(offered(info['url'],size=info.get('size'),label='Arquivo original'))
            elif track.source=='jamendo' and source and source.ready():
                data=await source.request('https://api.jamendo.com/v3.0/tracks/',params={'id':track.source_id,'client_id':source.secrets['jamendo_client_id'],'format':'json'})
                if data.get('headers',{}).get('status')!='success':raise SourceError('unavailable','Jamendo não confirmou o acesso. Verifique o Client ID e tente novamente.')
                for item in data.get('results',[]):
                    if item.get('audiodownload_allowed') is True:
                        for fmt,label,extension in [('mp31','MP3 96 kbps','mp3'),('mp32','MP3 VBR','mp3'),('ogg','OGG','ogg'),('flac','FLAC','flac')]:
                            url=str(httpx.URL('https://api.jamendo.com/v3.0/tracks/file/',params={'client_id':source.secrets['jamendo_client_id'],'id':track.source_id,'audioformat':fmt,'action':'download'}))
                            assets.append(offered(url,f'{track.title}.{extension}',format=label,label=label))
                if not assets:notices.append('O artista não disponibilizou download desta faixa no Jamendo.')
            elif track.source=='soundcloud' and source and source.ready():
                headers={'Authorization':f'OAuth {source.secrets["soundcloud_access_token"]}'}
                data=await source.request(f'https://api.soundcloud.com/tracks/{quote(track.source_id,safe="")}',headers=headers)
                url=data.get('download_url')
                if data.get('downloadable') is True and url and public_url(url).host=='api.soundcloud.com':
                    fmt=data.get('original_format')
                    assets.append(offered(url,track.title+('.'+fmt if fmt else ''),format=fmt,label='Original oferecido pelo artista',headers=headers))
                else:notices.append('A API não ofereceu um arquivo original para download com este acesso.')
            elif track.source=='audius':
                response=await self._get(self.metadata_client,f'https://api.audius.co/v1/tracks/{quote(track.source_id,safe="")}?app_name=EveryTune')
                item=response.json().get('data') or {}
                if isinstance(item,list):item=item[0] if item else {}
                if item.get('is_downloadable') is True and item.get('is_original_available') is True and not item.get('is_download_gated') and (item.get('access') or {}).get('download') is True and item.get('download'):
                    assets.append(offered(f'https://api.audius.co/v1/tracks/{quote(track.source_id,safe="")}/download?app_name=EveryTune',item.get('orig_filename') or track.title,label='Original disponibilizado pelo artista'))
                else:notices.append('A faixa não informou todas as permissões necessárias para baixar o original. Abra a origem para verificar acessos adicionais; o stream não foi convertido em arquivo.')
            elif track.source in {'jamendo','soundcloud'}:
                notices.append('Configure as credenciais próprias desta fonte para consultar as permissões e os arquivos de download.')
            elif track.source in NO_EXPORT:
                notices.append('Este conector oferece catálogo/metadados. Não foi disponibilizado um arquivo exportável pela integração. Reprodução offline de uma assinatura é diferente de download de arquivo.')
            else:
                definition=getattr(source,'definition',None)
                if definition and urlsplit(definition.endpoint).hostname==urlsplit(str(track.url)).hostname:
                    origin=urlsplit(str(track.url))._replace(path='',query='',fragment='').geturl()
                    self.page_times[origin]=max(self.page_times.get(origin,0),source.last_request)
                    self.page_delays[origin]=source.interval
                response=await self._get(self.metadata_client,str(track.url),robots=True)
                if 'html' not in response.headers.get('content-type','').lower():
                    raise SourceError('unavailable','A página de origem não retornou HTML para verificar os links.')
                assets=page_assets(response.text,str(response.url),definition.download_selector if definition else None)
                notices.append('Links identificados na página da origem. Formato vem do nome/metadados; disponibilidade será conferida ao preparar o arquivo. Espelhos externos podem exigir interação na origem.')
            if not assets:notices.append('Nenhuma opção de arquivo foi confirmada por este conector. Você ainda pode abrir a página de origem.')
            self.set_assets(ref,assets,notices)
            return self.manifest(ref)

    async def probe(self, ref, option_id):
        record=self.record(ref)
        if not self.source_enabled(record['track'].source):raise ValueError('A fonte foi removida ou desativada.')
        asset=record['assets'].get(option_id)
        if not asset or asset['delivery']!='external' or not asset['url'].startswith('https:'):
            raise ValueError('Escolha um link externo HTTPS identificado nesta página.')
        response=await self._get(self.transfer_client,asset['url'],stream=True,method='HEAD')
        try:
            mime=response.headers.get('content-type','').split(';',1)[0].lower()
            disposition=Message();disposition['content-disposition']=response.headers.get('content-disposition','')
            filename=disposition.get_filename()
            if not filename and mime!='application/octet-stream':filename=record['track'].title+(mimetypes.guess_extension(mime) or '')
            kind=media_kind({'filename':filename or ''})
            if kind and media_mime(mime,kind):
                size=response.headers.get('content-length','')
                asset.update(delivery='direct',filename=safe_filename(filename),format=Path(filename).suffix.lstrip('.').upper() or asset.get('format'),kind=file_kind(filename),size=int(size) if size.isdecimal() else None)
                record['notices'].append('O destino informou um arquivo nos cabeçalhos HTTP. A disponibilidade será conferida novamente ao transferir.')
            else:record['notices'].append('Este destino continua sendo uma página de acesso ou não confirmou um arquivo. Use Abrir origem / espelho.')
            return self.manifest(ref)
        finally:await response.aclose()

    def cleanup(self):
        for id,row in list(self.jobs.items()):
            if row['status'] not in {'queued','running'} and not row.get('serving') and time.monotonic()-row['updated']>1800:
                if self._remove_file(id):self.jobs.pop(id,None);self.tasks.pop(id,None)

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            self.cleanup()

    async def invalidate(self, sources):
        for ref,record in list(self.refs.items()):
            if record['track'].source in sources:
                track=record['track']
                self.refs.pop(ref)
                self.index.pop((track.source,track.source_id,str(track.url)),None)
                self.resolve_locks.pop(ref,None)
        for id,row in list(self.jobs.items()):
            if row['source'] in sources and row['status'] in {'queued','running'}:
                await self.cancel(id)

    def _remove_file(self, id):
        path=self.directory/id
        if path.resolve().parent!=self.directory:raise ValueError('Diretório temporário inválido')
        if path.exists():shutil.rmtree(path,ignore_errors=True)
        return not path.exists()

    def prepare(self, ref, option_ids, *, pack):
        self.cleanup();record=self.record(ref)
        if not self.source_enabled(record['track'].source):
            raise ValueError('A fonte foi removida ou desativada.')
        ids=list(dict.fromkeys(option_ids))
        if not ids or len(ids)>500 or any(id not in record['assets'] for id in ids):raise ValueError('Seleção de arquivos inválida ou expirada.')
        assets=[record['assets'][id].copy() for id in ids]
        if any(not media_kind(a) for a in assets):raise ValueError('Selecione somente arquivos de áudio ou imagem.')
        if any(a['delivery']!='direct' for a in assets):raise ValueError('Espelhos externos devem ser abertos na origem.')
        if pack not in {'original','zip'} or pack=='original' and len(assets)!=1:raise ValueError('Selecione um arquivo ou escolha ZIP.')
        if len(self.jobs)>=20:raise ValueError('Há 20 preparações recentes. Remova uma delas antes de continuar.')
        limit=self.store.settings().download_max_mb*1024*1024
        known=sum(a.get('size') or 0 for a in assets)
        if known>limit:raise ValueError('A seleção excede o limite de tamanho dos ajustes.')
        id=secrets.token_urlsafe(24)
        self.jobs[id]={'id':id,'source':record['track'].source,'title':record['track'].title,'filename':safe_filename(record['track'].title)+'.zip' if pack=='zip' else assets[0]['filename'],'status':'queued','bytes':0,'total_bytes':known if all(a.get('size') is not None for a in assets) else None,'files_done':0,'files_total':len(assets),'message':None,'pack':pack,'updated':time.monotonic()}
        self.tasks[id]=asyncio.create_task(self._run(id,assets,limit))
        return self.job(id)

    def job(self, id):
        if id not in self.jobs:raise KeyError('Preparação não encontrada ou expirada.')
        return {k:v for k,v in self.jobs[id].items() if k not in {'updated','serving'}}

    def artifact(self, id):
        if self.job(id)['status']!='ready':raise ValueError('O arquivo ainda não está pronto.')
        self.jobs[id]['updated']=time.monotonic()
        return self.directory/id/'artifact'

    def begin_serving(self, id):
        self.artifact(id)
        self.jobs[id]['serving']=self.jobs[id].get('serving',0)+1

    def end_serving(self, id):
        if id in self.jobs:
            self.jobs[id]['serving']=max(0,self.jobs[id].get('serving',0)-1)
            self.jobs[id]['updated']=time.monotonic()

    async def _write(self, asset, output, row, limit, quality_name=None):
        response=await self._get(self.transfer_client,asset['url'],headers=asset.get('headers'),stream=True)
        try:
            size=response.headers.get('content-length','')
            if size.isdecimal() and int(size)+row['bytes']>limit:raise ValueError('Arquivo excede o limite de tamanho dos ajustes.')
            content_type=response.headers.get('content-type','').lower()
            extension=Path(asset['filename']).suffix.lower()
            kind=media_kind(asset)
            if not kind or not media_mime(content_type,kind):
                raise ValueError('A origem não confirmou um arquivo de áudio ou imagem compatível.')
            if ('text/html' in content_type and extension not in {'.html','.htm'}) or ('json' in content_type and extension!='.json'):
                raise ValueError('A origem devolveu uma página/metadados em vez do arquivo. Abra o link na origem.')
            prefix=bytearray()
            async for chunk in response.aiter_bytes(1024*1024):
                row['bytes']+=len(chunk)
                if row['bytes']>limit:raise ValueError('Transferência excedeu o limite de tamanho dos ajustes.')
                output.write(chunk);row['updated']=time.monotonic()
                if row['pack']=='zip' and kind=='audio' and len(prefix)<MAX_HEADER:
                    prefix.extend(chunk[:MAX_HEADER-len(prefix)])
            row['files_done']+=1
            if row['pack']=='original' and response.headers.get('content-disposition'):
                message=Message();message['content-disposition']=response.headers['content-disposition']
                if message.get_filename():
                    filename=safe_filename(message.get_filename())
                    if media_kind({'filename':filename})!=kind:
                        raise ValueError('O nome do arquivo devolvido não corresponde ao áudio/imagem selecionado.')
                    row['filename']=filename
            if row['pack']=='zip' and kind=='audio':
                try:
                    with tempfile.TemporaryDirectory(dir=self.directory,prefix='quality-') as directory:
                        header=Path(directory)/'header';header.write_bytes(prefix)
                        quality=await inspect_audio(header,asset['filename'])
                except OSError:quality=None
                row.setdefault('quality_files',[]).append({'filename':quality_name or asset['filename'],
                    'declared':declared_quality(asset.get('quality') or {}),'measured':quality,'basis':'header'})
        finally:await response.aclose()

    async def _run(self, id, assets, limit):
        row=self.jobs[id]
        try:
            async with self.semaphore,asyncio.timeout(1800):
                row['status']='running'
                if shutil.disk_usage(self.directory).free<max(row['total_bytes'] or 0,10*1024*1024):raise ValueError('Espaço temporário insuficiente para preparar os arquivos.')
                path=self.directory/id;path.mkdir()
                if row['pack']=='zip':
                    used=set()
                    with zipfile.ZipFile(path/'artifact','w',compression=zipfile.ZIP_STORED,allowZip64=True) as bundle:
                        for asset in assets:
                            name=safe_filename(asset['filename']);original=name;index=1
                            while name.casefold() in used:
                                index+=1;name=f'{Path(original).stem}_{index}{Path(original).suffix}'
                            used.add(name.casefold())
                            with bundle.open(name,'w',force_zip64=True) as output:await self._write(asset,output,row,limit,quality_name=name)
                else:
                    with (path/'artifact').open('wb') as output:await self._write(assets[0],output,row,limit)
                    if media_kind(assets[0])=='audio':
                        quality=await inspect_audio(path/'artifact',row['filename'])
                        row['quality_files']=[{'filename':row['filename'],'declared':declared_quality(assets[0].get('quality') or {}),
                            'measured':quality,'basis':'file'}]
                row['status']='ready'
        except asyncio.CancelledError:row.update(status='cancelled',message='Preparação cancelada.')
        except (ValueError,SourceError) as error:row.update(status='failed',message=getattr(error,'message',str(error)))
        except Exception:row.update(status='failed',message='Não foi possível preparar os arquivos. A origem pode ter mudado, exigido acesso ou interrompido a conexão.')
        finally:
            row['updated']=time.monotonic()
            if row['status']!='ready':self._remove_file(id)
            try:self.store.measure('download',{'source':row['source'],'status':row['status']})
            except sqlite3.Error:logger.warning('Local preparation counters could not be saved')

    async def cancel(self, id):
        self.job(id)
        if self.jobs[id].get('serving'):raise ValueError('O navegador está salvando este arquivo. Aguarde ou cancele o download no navegador antes de remover.')
        task=self.tasks.get(id)
        if task and not task.done():task.cancel();await asyncio.gather(task,return_exceptions=True)
        if self._remove_file(id):self.jobs.pop(id,None);self.tasks.pop(id,None)

    async def aclose(self):
        self.janitor.cancel()
        for task in self.tasks.values():
            if not task.done():task.cancel()
        await asyncio.gather(self.janitor,*self.tasks.values(),return_exceptions=True)
        self.temp.cleanup()
