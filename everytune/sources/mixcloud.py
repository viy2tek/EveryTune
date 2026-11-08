from .base import MusicSource, offset
from ..models import SourcePage


class Mixcloud(MusicSource):
    id, name, category = "mixcloud", "Mixcloud", "Mixes e rádio"
    docs = "https://www.mixcloud.com/developers/"
    interval, ttl = 1, 3600

    async def search(self, query, limit=20, cursor=None):
        start = offset(cursor)
        data = await self.request("https://api.mixcloud.com/search/", params={"q":query,"type":"cloudcast","limit":limit,"offset":start})
        return SourcePage(tracks=[self.track(r["key"], r["name"], r["url"],
            artwork=(r.get("pictures") or {}).get("medium"), duration=r.get("audio_length"), kind="mix") for r in data["data"]],
            next_cursor=str(start+limit) if data.get("paging", {}).get("next") else None)
