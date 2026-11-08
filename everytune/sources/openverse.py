from .base import MusicSource, offset
from ..models import SourcePage

DOWNLOAD_LICENSES = {'by','by-sa','by-nc','by-nd','by-nc-sa','by-nc-nd','cc0','pdm'}


def offers_file(item):
    # public_http also loads adapter errors during package initialization.
    from ..public_http import public_url
    if item.get('license') not in DOWNLOAD_LICENSES or not item.get('url'):
        return False
    try:
        public_url(item['url'])
    except (ValueError,TypeError):
        return False
    return True


class Openverse(MusicSource):
    id, name, category = "openverse", "Openverse", "Licenças abertas"
    docs = "https://api.openverse.org/v1/"
    interval, ttl = 1.5, 3600

    async def search(self, query, limit=20, cursor=None):
        page = offset(cursor) or 1
        data = await self.request("https://api.openverse.org/v1/audio/", params={"q": query, "page_size": limit, "page": page, "category": "music"})
        return SourcePage(tracks=[self.track(r["id"], r["title"], r["foreign_landing_url"], artist=r.get("creator"),
            album=(r.get("audio_set") or {}).get("title"), duration=r["duration"]/1000 if r.get("duration") else None,
            artwork=r.get("thumbnail"), license=r.get("license_url") or r.get("license"),
            playable=True if offers_file(r) else None,
            downloadable=True if offers_file(r) else None)
            for r in data["results"] if r.get("foreign_landing_url", "").startswith("https://")],
            next_cursor=str(page+1) if page < data["page_count"] else None)
