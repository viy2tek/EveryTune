from .base import MusicSource, offset, year
from ..models import SourcePage


class Audius(MusicSource):
    id, name, category = "audius", "Audius", "Independente"
    docs = "https://api.audius.co/v1"
    interval = 1

    async def search(self, query, limit=20, cursor=None):
        start = offset(cursor)
        data = await self.request("https://api.audius.co/v1/tracks/search", params={"query": query, "limit": limit, "offset": start, "app_name": "EveryTune"})
        tracks = []
        for r in data["data"]:
            user = r.get("user") or {}
            path = r.get("permalink") or (f'/{user["handle"]}/{r["slug"]}' if user.get("handle") and r.get("slug") else None)
            if not path:
                continue
            tracks.append(self.track(r["id"], r["title"], "https://audius.co" + path if path.startswith("/") else path,
                artist=user.get("name"), artwork=(r.get("artwork") or {}).get("150x150"), duration=r.get("duration"), year=year(r.get("release_date")),
                playable=r.get("is_streamable"), downloadable=r.get("is_downloadable"), license=r.get("license")))
        return SourcePage(tracks=tracks, next_cursor=str(start+limit) if len(data["data"]) == limit else None)
