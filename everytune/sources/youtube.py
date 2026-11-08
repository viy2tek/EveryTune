import html

from .base import MusicSource
from ..models import SourcePage


class YouTube(MusicSource):
    id, name, category = "youtube", "YouTube", "Vídeos musicais"
    docs = "https://developers.google.com/youtube/v3/docs/search/list"
    credentials = ("youtube_api_key",)
    ttl = 900

    async def search(self, query, limit=20, cursor=None):
        params = {"part": "snippet", "type": "video", "videoCategoryId": "10", "q": query, "maxResults": limit, "key": self.secrets["youtube_api_key"]}
        if cursor:
            params["pageToken"] = cursor
        data = await self.request("https://www.googleapis.com/youtube/v3/search", params=params)
        return SourcePage(tracks=[self.track(r["id"]["videoId"], html.unescape(r["snippet"]["title"]), f'https://www.youtube.com/watch?v={r["id"]["videoId"]}',
            artwork=(r["snippet"].get("thumbnails", {}).get("medium") or {}).get("url"), kind="video") for r in data["items"]], next_cursor=data.get("nextPageToken"))
