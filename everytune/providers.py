"""Product groups are independent of a provider's pricing or download permissions."""

STREAMING_IDS = {
    'itunes','applemusic','spotify','soundcloud','deezer','youtube','audius','jamendo','mixcloud',
    'youtube_music','bandcamp','audiomack','soundclick',
}


def provider_group(id, definitions):
    return definitions[id].provider_group if id in definitions else 'streaming' if id in STREAMING_IDS else 'community'
