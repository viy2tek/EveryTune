import httpx
import pytest

from everytune.models import SearchTerms
from everytune.sources.discogs import DiscogsCredits
from everytune.sources.base import SourceError


def client_for(payloads):
    calls = []

    def handler(request):
        calls.append(request)
        key = request.url.path
        payload = payloads[key]
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    source = DiscogsCredits(client, {})
    source.interval = 0
    return client, source, calls


async def test_discogs_is_credit_only_and_preserves_exact_track_mode():
    client, source, calls = client_for({})
    async with client:
        result = await source.search_precise(SearchTerms(text="Rick Rubin", mode="track"), 10, None)
    assert result.tracks == [] and result.notices
    assert calls == []


async def test_discogs_returns_distinct_people_before_loading_releases():
    client, source, calls = client_for({"/database/search": {
        "pagination": {"page": 1, "pages": 2},
        "results": [
            {"id": 68211, "type": "artist", "title": "Rick Rubin"},
            {"id": 5588899, "type": "artist", "title": "Rick Rubin (3)"},
            {"id": 3, "type": "artist", "title": "Rick Rubin Tribute Band"},
        ],
    }})
    async with client:
        result = await source.search_precise(SearchTerms(text="Rick Rubin", mode="credits"), 10, None)
    assert result.tracks == []
    assert [person.name for person in result.people] == ["Rick Rubin", "Rick Rubin (3)"]
    assert result.people[0].id != result.people[1].id
    assert result.next_cursor == "2"
    assert len(calls) == 1
    assert result.notices


async def test_discogs_credits_bind_the_selected_person_and_actual_roles():
    client, source, calls = client_for({
        "/artists/68211": {"id": 68211, "name": "Rick Rubin"},
        "/artists/68211/releases": {
            "pagination": {"page": 2, "pages": 3},
            "releases": [
                {"id": 100, "type": "master", "title": "A record", "artist": "Another Artist", "role": "Producer", "year": 2020},
                {"id": 101, "type": "release", "title": "Another record", "artist": "Rick Rubin", "role": "Main"},
                {"id": 102, "type": "release", "title": "No credit", "artist": "Another Artist"},
            ],
        },
    })
    async with client:
        result = await source.search_precise(SearchTerms(text="Rick Rubin", mode="credits", identities={"discogs": "68211"}), 10, "2")
    assert result.next_cursor == "3"
    assert [track.credits[0].role for track in result.tracks] == ["Producer", "Main"]
    assert all(track.credits[0].person_id == "68211" for track in result.tracks)
    assert all(track.credits[0].name == "Rick Rubin" for track in result.tracks)
    assert all(track.kind == "album" for track in result.tracks)
    assert str(result.tracks[0].url) == "https://www.discogs.com/master/100"
    assert str(result.tracks[1].url) == "https://www.discogs.com/release/101"
    assert calls[-1].url.params["page"] == "2"
    assert result.tracks[0].playable is None and result.tracks[0].downloadable is None


@pytest.mark.parametrize("identities", [{"discogs": "../../private"}, {"discogs": "https://evil.example"}, {"discogs": "0"}])
async def test_discogs_rejects_non_numeric_identity(identities):
    client, source, calls = client_for({})
    async with client:
        with pytest.raises(SourceError):
            await source.search_precise(SearchTerms(text="Rick Rubin", mode="credits", identities=identities), 10, None)
    assert not calls


async def test_discogs_does_not_silently_change_identity_for_same_query():
    client, source, calls = client_for({"/artists/5588899": {"id": 5588899, "name": "Rick Rubin (3)"}})
    async with client:
        with pytest.raises(SourceError):
            await source.search_precise(SearchTerms(text="Rick Rubin", mode="credits", identities={"discogs": "5588899"}), 10, None)
    assert len(calls) == 1


async def test_discogs_empty_results_are_not_invented():
    client, source, calls = client_for({"/database/search": {"pagination": {"page": 1, "pages": 1}, "results": []}})
    async with client:
        result = await source.search_precise(SearchTerms(text="viy2tek", mode="credits"), 10, None)
    assert result.people == [] and result.tracks == []
    assert result.next_cursor is None
