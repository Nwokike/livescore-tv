import httpx
import re
from bs4 import BeautifulSoup
from core.state import StreamChannel
from core.config import SCORE808_BASE_URL


class Score808Scraper:
    def __init__(self):
        self.session = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=15,
            follow_redirects=True,
        )

    def close(self):
        self.session.close()

    def find_match_page(self, home_team: str, away_team: str) -> str | None:
        try:
            resp = self.session.get(SCORE808_BASE_URL)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text().lower()
                if home_team.lower() in text or away_team.lower() in text:
                    if href.startswith("/"):
                        return f"{SCORE808_BASE_URL}{href}"
                    return href
        except Exception:
            pass
        return None

    def get_streams_from_match_page(self, url: str) -> list[StreamChannel]:
        channels = []
        try:
            resp = self.session.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if any(x in href for x in ["stream", "play", "watch", "embed", "m3u8"]):
                    name = link.get_text().strip() or "Channel"
                    channels.append(StreamChannel(name=name, url=href))

            for iframe in soup.find_all("iframe", src=True):
                src = iframe["src"]
                name = iframe.get("title", "").strip() or "Stream"
                channels.append(StreamChannel(name=name, url=src))
        except Exception:
            pass

        return channels

    def resolve_stream_url(self, channel_url: str) -> str | None:
        if "m3u8" in channel_url:
            return channel_url

        try:
            resp = self.session.get(channel_url)
            resp.raise_for_status()

            m3u8_match = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', resp.text)
            if m3u8_match:
                return m3u8_match.group(1)

            iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', resp.text)
            if iframe_match:
                return iframe_match.group(1)

            if "m3u8" in resp.text.lower():
                return channel_url
        except Exception:
            pass

        return None

    def search_match_by_id(self, match_id: str) -> str | None:
        url = f"{SCORE808_BASE_URL}/football/{match_id}"
        try:
            resp = self.session.get(url)
            if resp.status_code == 200:
                return url
        except Exception:
            pass
        return None
