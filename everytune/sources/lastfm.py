from .base import MusicSource, SourceError, offset
from ..models import SourcePage


class LastFM(MusicSource):
    id, name, category = "lastfm", "Last.fm", "Metadados"
    docs = "https://www.last.fm/api/show/track.search"
    credentials = ("lastfm_api_key",)
    interval, ttl = 1, 3600

    async def search_precise(self, terms, limit, cursor):
        return await self.search(terms.title or terms.query_text, limit, cursor, artist=terms.artist)

    async def search(self, query, limit=20, cursor=None, *, artist=None):
        page = offset(cursor) or 1
        params = {"method":"track.search","track":query,"api_key":self.secrets["lastfm_api_key"],"format":"json","limit":limit,"page":page}
        if artist:
            params["artist"] = artist
        data = await self.request("https://ws.audioscrobbler.com/2.0/", params=params)
        if "error" in data:
            raise SourceError("rate_limit" if data["error"] == 29 else "unavailable", "Last.fm recusou a consulta; verifique chave e limites.")
        result = data["results"]
        tracks = []
        for r in result["trackmatches"]["track"]:
            url = r["url"].replace("http://www.last.fm/", "https://www.last.fm/", 1)
            tracks.append(self.track(r.get("mbid") or url, r["name"], url, artist=r.get("artist")))
        return SourcePage(tracks=tracks, next_cursor=str(page+1) if page*limit < int(result["opensearch:totalResults"]) else None)
