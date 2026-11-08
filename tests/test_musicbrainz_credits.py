import httpx
import pytest

from everytune.models import SearchTerms
from everytune.sources.base import SourceError
from everytune.sources.musicbrainz_credits import MusicBrainzCredits

PERSON = "ba30915c-4d33-43c5-8c37-ead0b8061517"
OTHER = "86b53bb4-4b3c-4fe7-a91c-78e3bc9e0721"


def relation(type, id, title, role):
    return {"target-type": type, type: {"id": id, "title": title}, "type": role, "attributes": []}


def source_client(artists=None, relations=None, name="Butch Vig", count=None):
    calls = []
    artists = [{"id": PERSON, "name": name}] if artists is None else artists
    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/artist/"):
            return httpx.Response(200, json={"artists": artists, "count": len(artists) if count is None else count})
        return httpx.Response(200, json={"id": PERSON, "name": name, "relations": relations or []})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    source = MusicBrainzCredits(client, {})
    source.interval = 0
    return source, client, calls


async def test_explicit_roles_and_no_invented_performer():
    rows = [relation("recording", "song", "Song", "producer"), relation("recording", "song", "Song", "engineer"),
            relation("release", "album", "Album", "mix"), relation("work", "work", "Work", "writer")]
    source, client, calls = source_client(relations=rows)
    async with client:
        result = await source.search_precise(SearchTerms(text="Butch Vig", mode="credits"), 20, None)
    assert len(result.tracks) == 3
    assert all(track.artist is None for track in result.tracks)
    song = next(track for track in result.tracks if track.title == "Song")
    assert {credit.role for credit in song.credits} == {"producer", "engineer"}
    assert all(credit.person_id == PERSON for track in result.tracks for credit in track.credits)
    assert str(song.credits[0].evidence_url).endswith("/relationships")
    assert calls[1].url.params["inc"] == "recording-rels+release-rels+work-rels"


async def test_ambiguous_people_require_selection():
    source, client, calls = source_client(artists=[{"id": PERSON, "name": "Name", "disambiguation": "producer"}, {"id": OTHER, "name": "Name", "disambiguation": "drummer"}])
    async with client:
        result = await source.search_precise(SearchTerms(text="Name", mode="credits"), 10, None)
    assert len(result.people) == 2 and result.tracks == []
    assert result.people[0].disambiguation == "producer"
    assert len(calls) == 1


async def test_selected_identity_is_verified_and_invalid_id_never_requested():
    source, client, calls = source_client(name="Another Name")
    async with client:
        with pytest.raises(SourceError):
            await source.search_precise(SearchTerms(text="Butch Vig", mode="credits", person_id=PERSON), 10, None)
        with pytest.raises(SourceError):
            await source.search_precise(SearchTerms(text="Butch Vig", mode="credits", person_id="https://evil.example"), 10, None)
    assert len(calls) == 1


async def test_local_pagination_preserves_entity_types_and_roles():
    rows = [relation("recording", str(i), name, "producer") for i, name in enumerate(("C", "A", "B"))]
    source, client, _ = source_client(relations=rows)
    terms = SearchTerms(text="Butch Vig", mode="credits", person_id=PERSON)
    async with client:
        first = await source.search_precise(terms, 2, None)
        second = await source.search_precise(terms, 2, first.next_cursor)
    assert [t.title for t in first.tracks] == ["A", "B"]
    assert [t.title for t in second.tracks] == ["C"]
    assert second.next_cursor is None


async def test_exact_identity_search_no_fuzzy_and_track_mode_does_not_request():
    source, client, calls = source_client(artists=[{"id": PERSON, "name": "Butch Vig Tribute"}])
    async with client:
        result = await source.search_precise(SearchTerms(text="Butch Vig", mode="credits"), 10, None)
        skipped = await source.search_precise(SearchTerms(text="Butch Vig", mode="track"), 10, None)
    assert result.tracks == [] and result.people == [] and result.notices
    assert skipped.tracks == [] and skipped.notices
    assert len(calls) == 1


async def test_partial_identity_page_does_not_assume_unique_person():
    source, client, calls = source_client(artists=[{"id": PERSON, "name": "Butch Vig"}], count=101)
    async with client:
        page = await source.search_precise(SearchTerms(text="Butch Vig", mode="credits"), 10, None)
    assert page.tracks == [] and page.next_cursor == "people:100"
    assert len(calls) == 1


async def test_source_specific_identity_skips_artist_search():
    source, client, calls = source_client(relations=[relation("recording", "song", "Song", "producer")])
    async with client:
        page = await source.search_precise(SearchTerms(text="Butch Vig", mode="credits", identities={source.id: PERSON}), 10, None)
    assert len(calls) == 1 and calls[0].url.path.endswith(PERSON)
    assert page.tracks[0].credits[0].role == "producer"
