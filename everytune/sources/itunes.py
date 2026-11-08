from .base import MusicSource, year
from ..models import SourcePage


class ITunes(MusicSource):
    id, name, category = "itunes", "iTunes / Apple", "Comercial"
    docs = "https://performance-partners.apple.com/search-api"
    interval, ttl = 3.1, 3600

    async def search_precise(self, terms, limit, cursor):
        return await self.search(terms.title or terms.artist or terms.text, limit, cursor,
                                 attribute="songTerm" if terms.title else "artistTerm" if terms.artist else None,
                                 requested_artist=terms.artist, country=terms.country)

    async def search(self, query, limit=20, cursor=None, *, attribute=None, requested_artist=None, country="BR"):
        params = {"term": query, "entity": "song", "media": "music", "limit": limit, "country": country}
        if attribute:
            params["attribute"] = attribute
        data = await self.request("https://itunes.apple.com/search", params=params)
        artists = {}
        ids = {str(r["artistId"]) for r in data["results"] if r.get("artistId") is not None}
        if requested_artist and ids:
            lookup = await self.request("https://itunes.apple.com/lookup", params={"id": ",".join(sorted(ids)), "entity": "musicArtist", "country": country})
            # Resolve credited names by ID; splitting commas would corrupt real band names.
            artists = {str(r["artistId"]): r["artistName"] for r in lookup["results"] if r.get("wrapperType") == "artist"}
        return SourcePage(tracks=[self.track(r["trackId"], r["trackName"], r["trackViewUrl"], artist=r.get("artistName"), album=r.get("collectionName"),
            artist_names=[artists[str(r["artistId"])]] if str(r.get("artistId")) in artists else None,
            artwork=r.get("artworkUrl100"), duration=r["trackTimeMillis"]/1000 if r.get("trackTimeMillis") else None,
            year=year(r.get("releaseDate")), license="Metadados promocionais Apple; áudio disponível na origem.") for r in data["results"] if r["kind"] == "song"])
