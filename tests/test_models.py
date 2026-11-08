import pytest
from pydantic import ValidationError

from everytune.models import SearchRequest, TrackResult, normalize, rank


def track(source="one", title="Águas de Março", artist="Tom Jobim", **kw):
    return TrackResult(source=source, source_id="1", platform=source, category="test", title=title, artist=artist, url="https://example.org/song", **kw)


def test_normalization_ranking_and_preserved_links():
    assert normalize(" ÁGUAS—de Março! ") == "aguas de marco"
    tracks = rank([track("a"), track("b"), track("c", title="Other song")], "aguas de marco")
    assert tracks[0].match == "exact"
    assert tracks[0].group == tracks[1].group
    assert len(tracks) == 2
    assert track().preview_url is None


def test_unknown_artist_does_not_merge():
    rows = rank([track("a", artist=None), track("b", artist=None)], "aguas de marco")
    assert rows[0].group != rows[1].group


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "http://example.org", "https://token:secret@example.org"])
def test_reject_unsafe_links(url):
    with pytest.raises(ValidationError):
        TrackResult(source="x", source_id="x", platform="x", category="x", title="x", url=url)


@pytest.mark.parametrize("body", [{"query":" "},{"query":"a","limit":51},{"query":"a","cursors":{"x":"a"*501}}])
def test_validate_queries(body):
    with pytest.raises(ValidationError):
        SearchRequest(**body)
