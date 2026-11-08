import json
import math
import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(re.sub(r"[^\w\s]", " ", "".join(c for c in value if not unicodedata.combining(c))).split())


def recording_type(title: str) -> str:
    # These are explicit version markers, not proof of who owns an upload.
    if re.search(r'[\[(][^\])]*\bcover\b[^\])]*[\])]|\bcover\s+(?:by|version)\b|\bcover\s*[\[(]|\b(?:piano|guitar|vocal|acoustic|instrumental)\s+cover\b', title, re.I):
        return 'cover'
    if re.search(r'\bremix\b',title,re.I):
        return 'remix'
    return 'unspecified'


class Credit(BaseModel):
    name: str = Field(min_length=1, max_length=1000)
    role: str = Field(min_length=1, max_length=200)
    person_id: str | None = None
    evidence_url: HttpUrl | None = None


class PersonResult(BaseModel):
    source: str
    id: str
    name: str
    url: HttpUrl
    disambiguation: str | None = None


class TrackResult(BaseModel):
    source: str
    source_id: str
    platform: str
    category: str
    title: str = Field(min_length=1, max_length=2000)
    artist: str | None = None
    artist_names: list[str] | None = None
    album: str | None = None
    artwork: HttpUrl | None = None
    duration: float | None = Field(default=None, ge=0)
    year: str | None = None
    url: HttpUrl
    preview_url: HttpUrl | None = None
    playable: bool | None = None
    downloadable: bool | None = None
    license: str | None = None
    kind: str = "track"
    score: float = 0
    match: Literal["exact", "partial", "related"] = "related"
    group: str | None = None
    recording_group: str | None = None
    audio_formats: list[str] = Field(default_factory=list)
    audio_file_count: int = 0
    matched_on: Literal["artist_title", "artist", "title", "album", "credit", "mention", "source"] | None = None
    credits: list[Credit] = Field(default_factory=list)
    provider_group: Literal['streaming','community'] = 'community'
    download_ref: str | None = None
    recording_type: Literal['cover','remix','unspecified'] = 'unspecified'
    file_access: Literal['catalogue','discover','offered'] = 'discover'
    audio_available: bool = False

    @field_validator("artwork", "url", "preview_url")
    @classmethod
    def safe_url(cls, value):
        if value and (value.scheme != "https" or value.username or value.password):
            raise ValueError("Only public HTTPS links without credentials are accepted")
        return value


class SourcePage(BaseModel):
    tracks: list[TrackResult] = Field(default_factory=list)
    next_cursor: str | None = None
    people: list[PersonResult] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)


class SearchTerms(BaseModel):
    text: str
    artist: str | None = None
    title: str | None = None
    mode: Literal["auto", "track", "credits", "source"] = "auto"
    person_id: str | None = None
    identities: dict[str, str] = Field(default_factory=dict)
    country: str = "BR"
    exclude_covers: bool = True

    @property
    def query_text(self) -> str:
        return " ".join(v for v in (self.artist, self.title) if v) if self.artist or self.title else self.text


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=300)
    artist: str | None = Field(default=None, min_length=1, max_length=300)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    mode: Literal["auto", "track", "credits", "source"] = "auto"
    exclude_covers: bool = True
    require_audio: bool = True
    provider_scope: Literal['both','streaming','community'] | None = None
    person_id: str | None = Field(default=None, pattern=r"^[a-fA-F0-9-]{36}$")
    identities: dict[str, str] = Field(default_factory=dict, max_length=100)
    sources: list[str] | None = Field(default=None, max_length=250)
    limit: int | None = Field(default=None, ge=1, le=50)
    cursors: dict[str, str] = Field(default_factory=dict, max_length=250)

    @field_validator("query", "artist", "title")
    @classmethod
    def trim(cls, value):
        if value is None:
            return None
        if not normalize(value):
            raise ValueError("Digite um nome para pesquisar")
        return value.strip()

    def terms(self) -> SearchTerms:
        options = dict(mode=self.mode, person_id=self.person_id, identities=self.identities,exclude_covers=self.exclude_covers)
        if self.mode == "source":
            return SearchTerms(text=self.query, **options)
        if self.mode == "credits":
            return SearchTerms(text=self.query, artist=self.artist, **options)
        if self.artist or self.title:
            return SearchTerms(text=self.query, artist=self.artist, title=self.title, **options)
        parts = re.split(r"\s+[-–—]\s+", self.query, maxsplit=1)
        if len(parts) == 2 and all(normalize(part) for part in parts):
            return SearchTerms(text=self.query, artist=parts[0].strip(), title=parts[1].strip(), **options)
        return SearchTerms(text=self.query, **options)

    @field_validator("cursors")
    @classmethod
    def cursor_bounds(cls, values):
        if any(len(v) > 500 or len(k) > 50 for k, v in values.items()):
            raise ValueError("Cursor muito longo")
        return values


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    disabled_sources: list[str] = Field(default_factory=list, max_length=250)
    provider_scope: Literal['both','streaming','community'] = 'both'
    download_max_mb: int = Field(default=2048, ge=10, le=32768)
    download_format: str = Field(default='', max_length=12, pattern=r'^[A-Z0-9]*$')
    download_pack: Literal['original','zip'] = 'zip'
    download_images: bool = False
    max_results: int = Field(default=15, ge=1, le=50)
    concurrency: int = Field(default=6, ge=1, le=12)
    timeout: float = Field(default=18, ge=2, le=60)
    theme: Literal["light", "dark", "system"] = "light"
    view: Literal["list", "grid"] = "list"
    country: str = Field(default="BR", pattern=r"^[A-Z]{2}$")
    show_artwork: bool = True
    show_credits: bool = True
    show_album: bool = True
    default_mode: Literal["auto", "track", "credits", "source"] = "auto"
    exclude_covers: bool = True


def rank(tracks: list[TrackResult], query: str | SearchTerms) -> list[TrackResult]:
    terms = SearchRequest(query=query).terms() if isinstance(query, str) else query
    q = normalize(terms.text)
    accepted = []
    for t in tracks:
        if t.recording_type=='unspecified':
            t.recording_type=recording_type(t.title)
        if terms.exclude_covers and t.recording_type=='cover':
            continue
        # Metadata grouping is not an acoustic identity check; never remove version markers.
        t.recording_group = json.dumps([normalize(t.title),normalize(t.artist or ''),t.kind,
            t.recording_type,round(t.duration) if t.duration and math.isfinite(t.duration) else None],ensure_ascii=False) if normalize(t.artist or '') and t.kind=='track' else f'{t.source}:{t.source_id}'
        if terms.mode == "source":
            t.matched_on, t.match, t.score, t.group = "source", "related", 0, f"{t.source}:{t.source_id}"
            accepted.append(t)
            continue
        title, artist, album = normalize(t.title), normalize(t.artist or ""), normalize(t.album or "")
        if t.kind == "catalogue_post":
            if terms.mode in {"credits","track"} or terms.artist or terms.title or f" {q} " not in f" {title} ":
                continue
            t.matched_on, t.match, t.score, t.group = "mention", "exact", 0.4, f"{t.source}:{t.source_id}"
            accepted.append(t)
            continue
        artists = {normalize(name) for name in (t.artist_names or []) if normalize(name)}
        if artist:
            artists.add(artist)
        if terms.mode == "credits":
            name = normalize(terms.artist or terms.text)
            person_id = terms.identities.get(t.source) or (terms.person_id if t.source == "musicbrainz_credits" else None)
            matching = [c for c in t.credits if normalize(c.name) == name and (not person_id or c.person_id == person_id)]
            if matching:
                t.matched_on = "credit"
            elif not person_id and name in artists:
                t.matched_on = "artist"
            else:
                continue
        elif terms.artist or terms.title:
            if terms.artist and normalize(terms.artist) not in artists:
                continue
            if terms.title and normalize(terms.title) != title:
                continue
            if terms.artist and terms.title and t.kind != "track":
                continue
            t.matched_on = "artist_title" if terms.artist and terms.title else "artist" if terms.artist else "title"
        elif q == title:
            t.matched_on = "title"
        elif q in artists and terms.mode != "track":
            t.matched_on = "artist"
        elif album and q == album and terms.mode != "track":
            t.matched_on = "album"
        else:
            continue
        t.match = "exact"
        t.score = {"artist_title": 1, "title": 1, "artist": 0.8, "album": 0.6, "credit": 1}[t.matched_on]
        # Unknown artists and archive items must not be merged on title alone.
        group_artist = normalize(terms.artist) if terms.artist else artist
        t.group = f"{title}|{group_artist}|{t.kind}" if group_artist and t.kind == "track" else f"{t.source}:{t.source_id}"
        accepted.append(t)
    return accepted if terms.mode == "source" else sorted(accepted, key=lambda t: (-t.score, normalize(t.title), t.source))
