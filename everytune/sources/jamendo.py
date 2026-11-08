from .base import MusicSource, SourceError, offset, year
from ..models import SourcePage


class Jamendo(MusicSource):
    id, name, category = "jamendo", "Jamendo", "Independente"
    docs = "https://developer.jamendo.com/v3.0/tracks"
    credentials = ("jamendo_client_id",)
    interval = 1

    async def search(self, query, limit=20, cursor=None):
        start = offset(cursor)
        data = await self.request("https://api.jamendo.com/v3.0/tracks/", params={"client_id": self.secrets["jamendo_client_id"], "format": "json", "search": query, "limit": limit, "offset": start})
        if data.get("headers", {}).get("status") != "success":
            raise SourceError("unavailable", "Jamendo recusou a consulta. Verifique o Client ID.")
        return SourcePage(tracks=[self.track(r["id"], r["name"], r["shareurl"], artist=r.get("artist_name"), album=r.get("album_name"),
            artwork=r.get("image"), duration=r.get("duration"), year=year(r.get("releasedate")), license=r.get("license_ccurl"),
            playable=bool(r.get("audio")), downloadable=r.get("audiodownload_allowed")) for r in data["results"]],
            next_cursor=str(start+limit) if len(data["results"]) == limit else None)
