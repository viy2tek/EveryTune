from .base import MusicSource, offset, year
from ..models import SourcePage


class AppleMusic(MusicSource):
    id, name, category = "applemusic", "Apple Music API", "Comercial"
    docs = "https://developer.apple.com/documentation/applemusicapi"
    credentials = ("apple_developer_token",)
    ttl = 3600

    async def search_precise(self, terms, limit, cursor):
        return await self.search(terms.query_text,limit,cursor,country=terms.country)

    async def search(self, query, limit=20, cursor=None, *, country="BR"):
        start = offset(cursor)
        data = await self.request(f"https://api.music.apple.com/v1/catalog/{country.lower()}/search", params={"term": query, "types": "songs", "limit": min(limit, 25), "offset": start}, headers={"Authorization": f'Bearer {self.secrets["apple_developer_token"]}'})
        songs = data["results"].get("songs", {"data": []})
        tracks = []
        for r in songs["data"]:
            a = r["attributes"]
            art = (a.get("artwork") or {}).get("url")
            tracks.append(self.track(r["id"], a["name"], a["url"], artist=a.get("artistName"), album=a.get("albumName"),
                artwork=art.replace("{w}", "160").replace("{h}", "160") if art else None,
                duration=a["durationInMillis"]/1000 if a.get("durationInMillis") else None, year=year(a.get("releaseDate"))))
        return SourcePage(tracks=tracks, next_cursor=str(start+min(limit, 25)) if songs.get("next") else None)
