import asyncio
import re
import time

from .base import MusicSource, offset, year
from ..models import SourcePage


class Spotify(MusicSource):
    id, name, category = "spotify", "Spotify", "Comercial"
    docs = "https://developer.spotify.com/documentation/web-api/reference/search"
    credentials = ("spotify_client_id", "spotify_client_secret")
    interval, ttl = 0.4, 900

    def __init__(self, client, secrets):
        super().__init__(client, secrets)
        self.token, self.expires = "", 0
        self.token_lock = asyncio.Lock()

    async def search_precise(self, terms, limit, cursor):
        if not (terms.artist or terms.title):
            return await self.search(terms.text, limit, cursor, country=terms.country)
        fields = []
        for field, value in (("artist", terms.artist), ("track", terms.title)):
            if value:
                phrase = " ".join(re.findall(r"\w+", value, re.UNICODE))
                fields.append(f'{field}:"{phrase}"')
        return await self.search(" ".join(fields), limit, cursor, country=terms.country)

    async def search(self, query, limit=20, cursor=None, *, country="BR"):
        async with self.token_lock:
            if time.monotonic() >= self.expires:
                data = await self.request("https://accounts.spotify.com/api/token", method="POST", data={"grant_type": "client_credentials", "client_id": self.secrets["spotify_client_id"], "client_secret": self.secrets["spotify_client_secret"]})
                self.token, self.expires = data["access_token"], time.monotonic()+max(0, data["expires_in"]-60)
        start = offset(cursor)
        # Spotify's development access may cap search pages at 10 items.
        size = min(limit, 10)
        data = await self.request("https://api.spotify.com/v1/search", params={"q": query, "type": "track", "limit": size, "offset": start, "market": country}, headers={"Authorization": f"Bearer {self.token}"})
        page = data["tracks"]
        tracks = []
        for r in page["items"]:
            if not r:
                continue
            album = r.get("album") or {}
            tracks.append(self.track(r["id"], r["name"], r["external_urls"]["spotify"], artist=", ".join(a["name"] for a in r.get("artists", [])) or None,
                artist_names=[a["name"] for a in r.get("artists", [])],
                album=album.get("name"), artwork=next(iter(album.get("images", [])), {}).get("url"), duration=r["duration_ms"]/1000 if r.get("duration_ms") else None,
                year=year(album.get("release_date")), license="Metadados Spotify; reprodução na plataforma."))
        return SourcePage(tracks=tracks, next_cursor=str(start+size) if page.get("next") else None)
