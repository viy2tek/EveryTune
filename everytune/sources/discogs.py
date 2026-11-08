import re

from .base import MusicSource, SourceError, offset, year
from ..models import Credit, PersonResult, SourcePage, normalize


class DiscogsCredits(MusicSource):
    id, name, category = "discogs", "Discogs", "Créditos"
    docs = "https://www.discogs.com/developers/"
    interval, ttl = 3.0, 3600
    supports_credits = True

    async def search(self, query, limit=20, cursor=None):
        return SourcePage(notices=["Use o modo de créditos e selecione uma identidade Discogs para consultar seus lançamentos."])

    async def search_precise(self, terms, limit, cursor):
        if terms.mode != "credits":
            return await self.search(terms.query_text, limit, cursor)
        page = offset(cursor) or 1
        person_id = terms.identities.get(self.id)
        if person_id is None:
            data = await self.request("https://api.discogs.com/database/search", params={
                "q": terms.text, "type": "artist", "per_page": limit, "page": page,
            })
            people = []
            seen = set()
            wanted = normalize(terms.text)
            for row in data["results"]:
                name = row["title"]
                base_name = re.sub(r" \([0-9]+\)$", "", name)
                if row.get("type") != "artist" or wanted not in {normalize(name), normalize(base_name)}:
                    continue
                identity = str(row["id"])
                if not re.fullmatch(r"[1-9][0-9]{0,11}", identity) or identity in seen:
                    continue
                seen.add(identity)
                people.append(PersonResult(source=self.id, id=identity, name=name,
                    url=f"https://www.discogs.com/artist/{identity}",
                    disambiguation="Homônimo numerado no catálogo." if name != base_name else "Confira a identidade na página da fonte."))
            return SourcePage(people=people, next_cursor=self._next_page(data, page), notices=[
                "Selecione uma pessoa para vincular os créditos ao ID correto; homônimos não são combinados."
                if people else "Nenhuma identidade correspondente apareceu nesta página do Discogs."
            ])
        if not re.fullmatch(r"[1-9][0-9]{0,11}", person_id):
            raise SourceError("unavailable", "Identidade Discogs inválida; selecione uma pessoa do catálogo.")
        artist = await self.request(f"https://api.discogs.com/artists/{person_id}")
        if str(artist["id"]) != person_id or normalize(artist["name"]) != normalize(terms.text):
            raise SourceError("unavailable", "O nome e a identidade Discogs não coincidem; selecione a pessoa novamente.")
        data = await self.request(f"https://api.discogs.com/artists/{person_id}/releases", params={"per_page": limit, "page": page})
        evidence_url = f"https://www.discogs.com/artist/{person_id}"
        tracks = []
        for row in data["releases"]:
            role = row.get("role")
            kind = row.get("type")
            identity = str(row["id"])
            if not role or kind not in {"master", "release"} or not re.fullmatch(r"[1-9][0-9]{0,11}", identity):
                continue
            tracks.append(self.track(f"{kind}:{identity}", row["title"], f"https://www.discogs.com/{kind}/{identity}",
                artist=row.get("artist"), year=year(row.get("year")), kind="album",
                artwork=row.get("thumb") if str(row.get("thumb", "")).startswith("https://") else None,
                credits=[Credit(name=artist["name"], role=role, person_id=person_id, evidence_url=evidence_url)]))
        return SourcePage(tracks=tracks, next_cursor=self._next_page(data, page), notices=[
            "Créditos resumidos por lançamento/master. Main, Remix e Producer mantêm os papéis informados pelo Discogs; não indicam todos o mesmo trabalho."
        ])

    @staticmethod
    def _next_page(data, page):
        return str(page + 1) if page < data["pagination"]["pages"] else None
