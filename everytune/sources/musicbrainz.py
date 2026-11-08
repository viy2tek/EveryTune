import re

from .base import MusicSource, offset, year
from ..models import SourcePage


class MusicBrainz(MusicSource):
    id, name, category = "musicbrainz", "MusicBrainz", "Metadados"
    docs = "https://musicbrainz.org/doc/MusicBrainz_API"
    interval, ttl = 1.1, 86400

    async def search_precise(self, terms, limit, cursor):
        if not (terms.artist or terms.title):
            return await self.search(terms.text, limit, cursor)
        fields = []
        for field, value in (("artist", terms.artist), ("recording", terms.title)):
            if value:
                phrase = " ".join(re.findall(r"\w+", value, re.UNICODE))
                fields.append(f'{field}:"{phrase}"')
        return await self._search(" AND ".join(fields), limit, cursor)

    async def search(self, query, limit=20, cursor=None):
        terms = re.findall(r"\w+", query, re.UNICODE)
        expression = " AND ".join(f'(recording:"{t}" OR artist:"{t}" OR release:"{t}")' for t in terms) or '""'
        return await self._search(expression, limit, cursor)

    async def _search(self, expression, limit, cursor):
        start = offset(cursor)
        data = await self.request("https://musicbrainz.org/ws/2/recording/", params={"query": expression, "fmt": "json", "limit": limit, "offset": start})
        return SourcePage(tracks=[self.track(r["id"], r["title"], f'https://musicbrainz.org/recording/{r["id"]}',
            artist="".join(a.get("name", a.get("artist", {}).get("name", "")) + a.get("joinphrase", "") for a in r.get("artist-credit", [])) or None,
            artist_names=[a["name"] for a in r.get("artist-credit", []) if a.get("name")],
            album=next(iter(r.get("releases", [])), {}).get("title"), duration=r["length"]/1000 if r.get("length") else None,
            year=year(r.get("first-release-date")), kind="track", license="Metadados MusicBrainz; sem autorização de áudio.") for r in data["recordings"]],
            next_cursor=str(start+limit) if start+limit < data["count"] else None)
