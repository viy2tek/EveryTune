import re
from uuid import UUID

from .base import MusicSource, SourceError, offset, year
from ..models import Credit, PersonResult, SearchTerms, SourcePage, normalize


class MusicBrainzCredits(MusicSource):
    id, name, category = "musicbrainz_credits", "MusicBrainz · Créditos", "Créditos"
    docs = "https://musicbrainz.org/doc/MusicBrainz_API"
    interval, ttl = 1.1, 86400
    supports_credits = True

    async def search(self, query, limit=20, cursor=None):
        return await self.search_precise(SearchTerms(text=query, mode="credits"), limit, cursor)

    async def search_precise(self, terms, limit, cursor):
        if terms.mode != "credits":
            return SourcePage(notices=["Selecione a busca por pessoa/créditos para consultar relações MusicBrainz."])
        name = terms.artist or terms.text
        selected_id = terms.person_id or getattr(terms, "identities", {}).get(self.id)
        if selected_id:
            try:
                selected_id = str(UUID(selected_id))
            except (ValueError, TypeError, AttributeError):
                raise SourceError("unavailable", "Identidade MusicBrainz inválida; selecione novamente a pessoa.") from None
        else:
            start = offset(cursor.removeprefix("people:")) if cursor and cursor.startswith("people:") else 0
            phrase = " ".join(re.findall(r"\w+", name, re.UNICODE))
            data = await self.request("https://musicbrainz.org/ws/2/artist/", params={
                "query": f'artist:"{phrase}"', "limit": 100, "offset": start, "fmt": "json"})
            candidates = [a for a in data["artists"] if normalize(a["name"]) == normalize(name)]
            people = [self.person(a) for a in candidates]
            if not people:
                return SourcePage(notices=["Nenhuma identidade com esse nome exato encontrada no MusicBrainz. Isso não prova ausência de créditos em outras fontes."])
            more_people = start + len(data["artists"]) < data["count"]
            if len(people) != 1 or more_people or start:
                return SourcePage(people=people,
                    next_cursor=f"people:{start + 100}" if more_people else None,
                    notices=["Escolha a identidade correta antes de reunir créditos; nomes iguais podem pertencer a pessoas diferentes."])
            selected_id = people[0].id

        data = await self.request(f"https://musicbrainz.org/ws/2/artist/{selected_id}", params={
            "fmt": "json", "inc": "recording-rels+release-rels+work-rels"})
        if normalize(data["name"]) != normalize(name):
            raise SourceError("unavailable", "A identidade selecionada não corresponde ao nome pesquisado.")
        person = self.person(data)
        entries = {}
        evidence = f"https://musicbrainz.org/artist/{selected_id}/relationships"
        for relation in data["relations"]:
            target_type = relation.get("target-type")
            if target_type not in {"recording", "release", "work"}:
                continue
            target = relation[target_type]
            if terms.title and normalize(target["title"]) != normalize(terms.title):
                continue
            key = f'{target_type}:{target["id"]}'
            if key not in entries:
                entries[key] = self.track(key, target["title"], f'https://musicbrainz.org/{target_type}/{target["id"]}',
                    kind={"recording": "track", "release": "album", "work": "work"}[target_type],
                    duration=target["length"] / 1000 if target.get("length") is not None else None,
                    album=target["title"] if target_type == "release" else None,
                    year=year(target.get("date")), license="Metadados MusicBrainz; áudio e intérprete não presumidos.")
            role = relation["type"]
            if relation.get("attributes"):
                role += " (" + ", ".join(relation["attributes"]) + ")"
            credit = Credit(name=data["name"], role=role, person_id=selected_id, evidence_url=evidence)
            if credit not in entries[key].credits:
                entries[key].credits.append(credit)
        tracks = sorted(entries.values(), key=lambda t: (normalize(t.title), t.source_id))
        start = offset(cursor) if cursor and not cursor.startswith("people:") else 0
        return SourcePage(tracks=tracks[start:start + limit], people=[person],
            next_cursor=str(start + limit) if start + limit < len(tracks) else None,
            notices=[f"{len(tracks)} gravações, lançamentos e obras nas relações retornadas pelo MusicBrainz; paginação local deste conjunto. O catálogo é colaborativo e não garante todos os trabalhos da pessoa. O intérprete permanece desconhecido quando não informado."])

    def person(self, data):
        return PersonResult(source=self.id, id=data["id"], name=data["name"],
                            url=f'https://musicbrainz.org/artist/{data["id"]}',
                            disambiguation=data.get("disambiguation") or None)
