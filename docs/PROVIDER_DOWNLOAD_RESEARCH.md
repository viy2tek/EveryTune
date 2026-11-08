# Provider and download research

Verified 2026-11-05. Read-only requests inspected official documentation, JSON metadata, and public HTML. No audio, PDF, MIDI, ZIP, torrent, or other media body was fetched; no login, signup, purchase, or access-control bypass occurred. Findings describe advertised metadata, not a guarantee that a binary will transfer successfully.

## Provider grouping and search scope

Implementation recommendation: keep provider identity separate from economic grouping. A useful UI split is **streaming services (paid/freemium)** versus **community/catalogue sources**; it must not imply that every streaming result requires payment or every community result permits downloading. SoundCloud and Audius can expose creator-authorized downloads; Spotify/Apple subscription offline listening is a separate capability. Offer both groups, either group, and individually selected source IDs. This grouping is a product recommendation, not provider-supplied metadata.

## Verified API schemas

### Internet Archive

`GET https://archive.org/metadata/{identifier}` returns `metadata` and `files[]`. Each advertised file can carry `name`, `format`, `source` (original/derivative/metadata), `size` as a string, and checksums. Missing items can return an empty array; errors can have `error`. Large lists support partial reads such as `/metadata/{identifier}/files?start=0&count=100`. Do not assume every 200 response contains usable files. [Official Metadata API](https://archive.org/developers/md-read.html).

Live sample `sam-torres-still` advertised three audio alternatives: `Sam Torres - Still.flac` (`Flac`, derivative, 190963454 bytes), `.mp3` (`VBR MP3`, derivative, 69352151), and `.wav` (`WAVE`, original, 612898362). Its metadata has no `licenseurl`; availability must preserve unknown rights. Other listed files include artwork, torrent, and metadata, which should not be confused with audio. [Observed JSON](https://archive.org/metadata/sam-torres-still).

Recommendation: enumerate advertised file rows and construct an Archive download link using separately encoded identifier and filename; keep the original filename/path, source role, size, and format. Treat explicit restricted/private indicators as unavailable. Do not synthesize formats or assume an entire item is downloadable because one file is listed. The existing public transport remains metadata-only.

### Wikimedia Commons

Request `action=query&format=json&prop=imageinfo&iiprop=url|mime|size|extmetadata&titles=File:Example.ogg` at `https://commons.wikimedia.org/w/api.php`. Response path is `query.pages.{pageid}.imageinfo[]`; `url` points to original file, `descriptionurl` to attribution/description, `mime` and `size` describe the file. `extmetadata` values may contain HTML, so render as sanitized text. Request this expensive property for few results. `iilimit` counts historical revisions, not alternate downloadable encodings. [Official Imageinfo documentation](https://www.mediawiki.org/wiki/API:Imageinfo).

Observed `File:Example.ogg` has MIME `application/ogg`, size 104793, original upload.wikimedia.org URL, and `extmetadata.LicenseShortName.value = CC BY-SA 3.0`, `LicenseUrl.value`, `Artist.value`, `AttributionRequired.value = "true"`. An `audio/*`-only filter would incorrectly reject this file. Keep the returned URL, including its query string, instead of rebuilding a CDN path. [Description page](https://commons.wikimedia.org/wiki/File:Example.ogg).

### Jamendo

`GET https://api.jamendo.com/v3.0/tracks/?client_id=OWN_CLIENT_ID&format=json&id=TRACK_ID` returns `results[]` with `id`, `name`, `audio` (stream), `audiodownload` (download), `audiodownload_allowed` (boolean), and `license_ccurl`. Download URL becomes empty when permission is false. Preserve permission independently of whether streaming exists. [Tracks API](https://developer.jamendo.com/v3.0/tracks).

`GET /v3.0/tracks/file/?client_id=OWN_CLIENT_ID&id=TRACK_ID&audioformat=FORMAT&action=download` redirects to a file rather than returning JSON. Documented formats: `mp31` (96 kbps), `mp32` (VBR), `ogg`, `flac`; default is `mp31`. Permission false produces 404. Build choices only when `audiodownload_allowed is True`, and revalidate on download. Do not send this binary endpoint through the metadata client. [File endpoint](https://developer.jamendo.com/v3.0/tracks/file).

No live authenticated Jamendo request was made; no client ID was borrowed. These formats are documented capabilities, not four separately tested files for any particular track.

### Audius

Official REST API base is `https://api.audius.co/v1`; most read endpoints work without credentials, API keys increase limits. `GET /tracks/{track_id}` / search records expose `is_downloadable`, `is_original_available`, `orig_filename`, `is_download_gated`, `download_conditions`, `access`, `download`; `/tracks/{track_id}/download` is the official original/MP3 download route. Keep gated downloads on the provider's authorization flow; CIDs are metadata and do not grant download permission. [Official REST reference](https://docs.audius.co/api/), [API endpoint index](https://api.audius.co/v1).

Live search returned `mWB22` (Ambient Snow): `is_downloadable:false`, `download:null`, `is_original_available:false`, yet `access.download:true`. Therefore **`access.download` alone is insufficient**. Require creator permission and a real advertised authorized download option. Do not infer a FLAC choice from an upload name or a stream URL. REST uses snake_case; SDK docs use camelCase, so avoid mixing their fields. [Live metadata query](https://api.audius.co/v1/tracks/search?query=ambient&limit=1&app_name=EveryTune), [SDK type reference](https://docs.audius.co/sdk/tracks/).

## Streaming access and download limits

| Service | Current integration eligibility | Download behavior |
| --- | --- | --- |
| Spotify | Development-mode owner needs Premium; maximum five authenticated allowlisted users. Extended mode is a partner application with organizational/scale requirements. | Premium offline storage stays in Spotify; this is not an advertised MP3/FLAC/ZIP export API. |
| Apple Music | Catalog API needs signed developer token and Apple Developer Program membership; user playback/library needs MusicKit authorization and applicable subscription. | Official offline instructions use Apple Music apps and a subscription; do not reinterpret catalogue URLs or previews as full-file downloads. |
| SoundCloud | Registered app and OAuth; public resources support client credentials, user resources require consent. Current guide recommends Artist Pro for API-key creation. | Only creator-enabled downloads of individual original uploads; playlist ZIP export is not supplied by that permission. |

Spotify sources: [Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes), [July 2026 update](https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates), [offline support](https://support.spotify.com/us/article/listen-offline/). July supersedes February's one-client-ID limit: up to **25 client IDs** now share a developer-account quota. Do not repeat the obsolete limit. Offline support describes 10,000 tracks per device across up to five devices and online reconnection every 30 days.

Apple sources: [Developer tokens](https://developer.apple.com/documentation/applemusicapi/generating-developer-tokens), [MusicKit](https://developer.apple.com/documentation/musickit), [offline support](https://support.apple.com/en-us/118288). These establish catalog/playback/offline mechanisms; this research found no public full-file export endpoint.

SoundCloud sources: [Current API guide](https://developers.soundcloud.com/docs/api/guide), [official OpenAPI JSON](https://developers.soundcloud.com/docs/api/explorer/api.json), [download support](https://help.soundcloud.com/hc/en-us/articles/115003448787-Downloading-tracks). Current `Track` schema exposes `downloadable:boolean`, `download_url:string|null` (omitted/null when unavailable), and `download_count`. The checked current OpenAPI does not advertise a dedicated `/download` path; consume only the actual `download_url` under supported authentication. Web original downloads require sign-in; Go/Go+ mobile offline caching is different. No SoundCloud credentials were used.

## Community item pages: actual offered formats and mirrors

| Source/item | Observed public HTML links | Resolver implication |
| --- | --- | --- |
| [OC ReMix OCR02572](https://ocremix.org/remix/OCR02572) | Three MP3 download anchors labeled Aplus, ocrmirror.org, BlueBlue.fr. | Group multiple mirrors of the same filename without fetching all of them. They are separate origins, requiring validation for every redirect. |
| [VGMRips Super Mario Bros. 3](https://vgmrips.net/packs/pack/super-mario-bros-3-nes) | 32 individual `.vgz` links and explicit `.zip` pack link. | Preserve chip-music format; expose explicit package, do not pretend it is MP3 or generate a ZIP URL. |
| [Mutopia piece 1](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1) | MIDI, A4 PDF, Letter PDF, LilyPond `.ly`; page labels this work public domain. | Include score/source formats alongside audio, preserving distinct variants. Other works may have different licenses. |

These observations establish that a single playable audio URL cannot represent all offered assets. Discovery should retain filename, extension/format, optional size, package flag, mirror label, original item page, and stated license/permission. Unknown formats should remain visible when they are actual explicit file anchors. Do not turn unrelated navigation, login, donation, or arbitrary extensionless links into downloads. This is implementation advice based on the observed pages, not a claim that all 70+ sources share a stable selector.

## Fixtures and implementation boundary

Reduced real responses are stored in `tests/fixtures/download_archive.json`, `download_commons.json`, `download_audius.json`, `download_community.json`. Audius signed stream URLs, wallet/profile data, scripts, and media bodies were omitted. Community fixtures retain selected visible anchors; VGMRips retains two track examples plus its package rather than all 32.

Recommended tests: Archive preserves multiple encodings and optional size; Commons accepts `application/ogg`; Jamendo false denies a URL; Audius false creator permission overrides optimistic `access.download`; community resolves relative URLs, preserves ZIP/MIDI/PDF/VGZ, and deduplicates exact anchors. A binary transfer service must separately enforce public DNS pinning, redirect validation, safe filenames, byte/time limits, and atomic writes. Do not weaken `PublicTransport` or reuse a JSON/HTML response-size cap as a media downloader. Actual transfers, credentials, provider-specific login gates, and exhaustive per-site download success remain untested.
