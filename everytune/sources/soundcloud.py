from .base import MusicSource, offset, year
from ..models import SourcePage


class SoundCloud(MusicSource):
    id, name, category = "soundcloud", "SoundCloud", "Independente"
    docs = "https://developers.soundcloud.com/docs/api/guide"
    credentials = ("soundcloud_access_token",)
    interval = 1

    async def search(self, query, limit=20, cursor=None):
        start = offset(cursor)
        data = await self.request("https://api.soundcloud.com/tracks", params={"q": query, "limit": limit, "offset": start, "linked_partitioning": "true"}, headers={"Authorization": f'OAuth {self.secrets["soundcloud_access_token"]}'})
        rows = data["collection"]
        return SourcePage(tracks=[self.track(r.get("urn", r.get("id")), r["title"], r["permalink_url"],
            artist=(r.get('user') or {}).get('username'),
            artwork=r.get("artwork_url"), duration=r["duration"]/1000 if r.get("duration") else None,
            year=year(r.get("release_year")), license=r.get("license"), downloadable=r.get('downloadable'), kind="track") for r in rows],
            next_cursor=str(start+limit) if data.get("next_href") else None)
