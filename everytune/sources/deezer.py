from .base import MusicSource,SourceError,offset,year
from ..models import Credit,PersonResult,SourcePage,normalize


class Deezer(MusicSource):
    id,name,category='deezer','Deezer · Catálogo público','Comercial'
    docs='https://api.deezer.com'
    interval,ttl=0.4,3600
    supports_credits=True

    async def search(self,query,limit=20,cursor=None):
        start=offset(cursor)
        size=min(limit,10)
        data=await self.request('https://api.deezer.com/search',params={'q':query,'limit':size,'index':start})
        if 'error' in data:
            raise SourceError('unavailable','Deezer recusou a pesquisa do catálogo público.')
        tracks=[]
        for row in data['data']:
            title=row['title']
            version=row.get('title_version')
            if version and normalize(version) not in normalize(title):
                title+=' '+version
            tracks.append(self.track(row['id'],title,row['link'],artist=(row.get('artist') or {}).get('name'),
                album=(row.get('album') or {}).get('title'),artwork=(row.get('album') or {}).get('cover_medium'),duration=row.get('duration'),year=year(row.get('release_date'))))
        return SourcePage(tracks=tracks,next_cursor=str(start+size) if start+size<data.get('total',0) else None,
            notices=['Catálogo público consultado sem chave; disponibilidade observada, documentação atual do portal ainda não acessível.'])

    async def search_precise(self,terms,limit,cursor):
        page=await self.search(terms.query_text,limit,cursor)
        if terms.mode!='credits' and not terms.artist:
            return page
        people={}
        selected=terms.identities.get(self.id)
        for track in page.tracks:
            if not track.source_id.isdecimal():
                continue
            detail=await self.request('https://api.deezer.com/track/'+track.source_id)
            names=[]
            credits=[]
            for person in detail.get('contributors',[]):
                name=person.get('name');identity=str(person.get('id',''));role=person.get('role')
                if not name or not identity.isdecimal() or not role:
                    continue
                names.append(name)
                credits.append(Credit(name=name,role=role,person_id=identity,evidence_url=track.url))
                if normalize(name)==normalize(terms.artist or terms.text):
                    people[identity]=PersonResult(source=self.id,id=identity,name=name,url=f'https://www.deezer.com/artist/{identity}',disambiguation='Identidade informada em contributors; o papel é preservado como consta na fonte.')
            track.artist_names=names or None
            track.credits=credits
        if terms.mode=='credits' and len(people)>1 and not selected:
            return SourcePage(people=list(people.values()),notices=['Há identidades diferentes com este nome; escolha antes de reunir participações.'])
        page.people=list(people.values())
        page.notices.append('Main/Featured são papéis do catálogo; não significam automaticamente produção ou engenharia. Créditos ausentes não são inferidos.')
        return page
