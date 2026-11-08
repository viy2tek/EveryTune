from .apple import AppleMusic
from .archive import InternetArchive
from .audius import Audius
from .commons import Commons
from .itunes import ITunes
from .jamendo import Jamendo
from .lastfm import LastFM
from .mixcloud import Mixcloud
from .musicbrainz import MusicBrainz
from .musicbrainz_credits import MusicBrainzCredits
from .discogs import DiscogsCredits
from .deezer import Deezer
from .openverse import Openverse
from .soundcloud import SoundCloud
from .spotify import Spotify
from .youtube import YouTube

ADAPTERS = (ITunes, MusicBrainz, InternetArchive, Audius, Openverse, Commons, Mixcloud,
            Jamendo, YouTube, Spotify, SoundCloud, AppleMusic, LastFM, MusicBrainzCredits, DiscogsCredits, Deezer)

# External searches are navigation links, never fabricated TrackResults.
EXTERNAL = (
    ("bandcamp", "Bandcamp", "Independente", "https://bandcamp.com/search?q={query}&item_type=t"),
    ("youtube_music", "YouTube Music", "Vídeos musicais", "https://music.youtube.com/search?q={query}"),
    ("free_music_archive", "Free Music Archive", "Licenças abertas", "https://freemusicarchive.org/search/?quicksearch={query}"),
    ("musopen", "Musopen", "Acervos", "https://musopen.org/music/?q={query}"),
    ("newgrounds", "Newgrounds Audio", "Independente", "https://www.newgrounds.com/search/conduct/audio?terms={query}"),
    ("audiomack", "Audiomack", "Independente", "https://audiomack.com/search?q={query}"),
    ("soundclick", "SoundClick", "Independente", "https://www.soundclick.com/search/default.cfm?searchTerm={query}"),
    ("loc", "Library of Congress", "Acervos", "https://www.loc.gov/audio/?q={query}"),
    ("setlistfm", "setlist.fm", "Apresentações", "https://www.setlist.fm/search?query={query}"),
    ("livearchive", "Live Music Archive", "Apresentações", "https://archive.org/search?query={query}+AND+collection%3Aetree"),
)
