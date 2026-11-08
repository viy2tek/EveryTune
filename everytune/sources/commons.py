import html
import re

from .base import MusicSource, offset
from ..models import SourcePage


def plain(value):
    return html.unescape(re.sub("<[^>]*>", "", value or "")).strip() or None


class Commons(MusicSource):
    id, name, category = "commons", "Wikimedia Commons", "Licenças abertas"
    docs = "https://www.mediawiki.org/wiki/API:Imageinfo"
    interval, ttl = 1, 3600

    async def search(self, query, limit=20, cursor=None):
        start = offset(cursor)
        terms = " ".join(re.findall(r"\w+", query, re.UNICODE))
        data = await self.request("https://commons.wikimedia.org/w/api.php", params={"action": "query", "format": "json", "generator": "search",
            "gsrsearch": f"{terms} filetype:audio", "gsrnamespace": 6, "gsrlimit": limit, "gsroffset": start,
            "prop": "imageinfo", "iiprop": "url|extmetadata|mime"})
        if "error" in data:
            raise ValueError("MediaWiki error")
        tracks = []
        for r in data.get("query", {}).get("pages", {}).values():
            info = r["imageinfo"][0]
            meta = info.get("extmetadata") or {}
            license_name = plain(meta.get("LicenseShortName", {}).get("value"))
            tracks.append(self.track(r["pageid"], plain(meta.get("ObjectName", {}).get("value")) or r["title"].removeprefix("File:"), info["descriptionurl"],
                artist=plain(meta.get("Artist", {}).get("value")), license=license_name,
                playable=True if license_name else None, downloadable=True if license_name else None, kind="audio_file"))
        following = data.get("continue", {}).get("gsroffset")
        return SourcePage(tracks=tracks, next_cursor=str(following) if following is not None else None)
