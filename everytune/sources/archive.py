import re
from urllib.parse import quote

from .base import MusicSource, offset, text, year
from ..models import SourcePage


class InternetArchive(MusicSource):
    id, name, category = "archive", "Internet Archive", "Acervos"
    docs = "https://archive.org/advancedsearch.php"
    interval, ttl = 1, 3600

    async def search(self, query, limit=20, cursor=None):
        page = offset(cursor) or 1
        terms = " AND ".join(f'"{t}"' for t in re.findall(r"\w+", query, re.UNICODE)) or '""'
        data = await self.request("https://archive.org/advancedsearch.php", params={"q": f"({terms}) AND mediatype:audio", "output": "json", "rows": limit, "page": page,
            "fl[]": ["identifier", "title", "creator", "date", "licenseurl"]})
        rows = data["response"]["docs"]
        return SourcePage(tracks=[self.track(r["identifier"], text(r.get("title")) or r["identifier"], f'https://archive.org/details/{quote(r["identifier"], safe="")}',
            artist=text(r.get("creator")), year=year(r.get("date")), license=text(r.get("licenseurl")), kind="archive_item") for r in rows],
            next_cursor=str(page+1) if page*limit < data["response"]["numFound"] else None)
