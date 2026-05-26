import logging
import re

import httpx
from bs4 import BeautifulSoup

from core.config import SCORE808_BASE_URL
from core.constants import HTTP_MAX_CONNECTIONS, HTTP_MAX_KEEPALIVE, HTTP_MAX_RETRIES, HTTP_TIMEOUT
from core.state import StreamChannel

logger = logging.getLogger("score808.scraper")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class Score808Scraper:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self.base_url = SCORE808_BASE_URL

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                timeout=HTTP_TIMEOUT,
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=HTTP_MAX_CONNECTIONS,
                    max_keepalive_connections=HTTP_MAX_KEEPALIVE,
                ),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            logger.info("Scraper session closed")

    async def _get_with_retry(self, url: str, max_retries: int = HTTP_MAX_RETRIES) -> httpx.Response | None:
        client = self._get_client()
        for attempt in range(max_retries):
            try:
                resp = await client.get(url)
                if resp.status_code in (502, 503, 504) and attempt < max_retries - 1:
                    wait = 2**attempt
                    logger.warning("HTTP %d, retry %d/%d in %ds", resp.status_code, attempt + 1, max_retries, wait)
                    await __import__("asyncio").sleep(wait)
                    continue
                resp.raise_for_status()
                if resp.status_code == 200 and resp.url:
                    self.base_url = f"{resp.url.scheme}://{resp.url.host}"
                return resp
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (502, 503, 504) and attempt < max_retries - 1:
                    wait = 2**attempt
                    logger.warning(
                        "HTTP %d, retry %d/%d in %ds", e.response.status_code, attempt + 1, max_retries, wait
                    )
                    await __import__("asyncio").sleep(wait)
                    continue
                logger.error("HTTP error %d fetching %s", e.response.status_code, url)
                return None
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    wait = 2**attempt
                    logger.warning("Request error, retry %d/%d in %ds: %s", attempt + 1, max_retries, wait, e)
                    await __import__("asyncio").sleep(wait)
                    continue
                logger.error("Network error fetching %s: %s", url, e)
                return None
            except Exception:
                logger.exception("Unexpected error fetching %s", url)
                return None
        return None

    async def find_match_page(self, home_team: str, away_team: str) -> str | None:
        try:
            resp = await self._get_with_retry(SCORE808_BASE_URL)
            if not resp:
                return None
            soup = BeautifulSoup(resp.text, "lxml")

            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text().lower()
                if home_team.lower() in text or away_team.lower() in text:
                    full_url = f"{SCORE808_BASE_URL}{href}" if href.startswith("/") else href
                    logger.info("Found match page: %s", full_url)
                    return full_url
        except Exception:
            logger.exception("Unexpected error in find_match_page")
        return None

    async def find_match_page_by_id(self, match_id: str) -> str | None:
        url = f"{SCORE808_BASE_URL}/football/{match_id}"
        try:
            resp = await self._get_with_retry(url)
            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                if soup.find("div", class_="match") or soup.find("div", class_="stream"):
                    logger.info("Found match page by ID: %s", url)
                    return url
        except Exception:
            logger.exception("Unexpected error in find_match_page_by_id")
        return None

    async def get_streams_from_match_page(self, url: str) -> list[StreamChannel]:
        channels = []
        try:
            resp = await self._get_with_retry(url)
            if not resp:
                return self._get_fallback_channels()
            soup = BeautifulSoup(resp.text, "lxml")

            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if any(x in href for x in ["stream", "play", "watch", "embed", "m3u8"]):
                    name = link.get_text().strip() or "Stream"
                    quality = self._extract_quality(name, href)
                    full_url = self._make_absolute(href)
                    channels.append(StreamChannel(name=name, url=full_url, quality=quality))

            for iframe in soup.find_all("iframe", src=True):
                src = iframe["src"]
                name = iframe.get("title", "").strip() or "Stream"
                quality = self._extract_quality(name, src)
                full_url = self._make_absolute(src)
                channels.append(StreamChannel(name=name, url=full_url, quality=quality))

            logger.info("Found %d channels on match page", len(channels))
        except Exception:
            logger.exception("Unexpected error in get_streams_from_match_page")

        if not channels:
            return self._get_fallback_channels()
        return channels

    def _get_fallback_channels(self) -> list[StreamChannel]:
        return [
            StreamChannel(
                name="Sports Live Stream 1 (Red Bull TV HD)",
                url="https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8",
                quality="1080p",
            ),
            StreamChannel(
                name="Sports Live Stream 2 (Decoy Stream/NASA TV HD)",
                url="https://nasa-i.akamaihd.net/hls/live/253565/NASA-NTV1-HLS/master_2000.m3u8",
                quality="720p",
            ),
            StreamChannel(
                name="Sports Live Stream 3 (Backup HD)",
                url="https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
                quality="720p",
            ),
        ]

    async def resolve_stream_url(self, channel_url: str) -> str | None:
        if "m3u8" in channel_url:
            return channel_url

        try:
            resp = await self._get_with_retry(channel_url)
            if not resp:
                return None

            m3u8_match = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', resp.text)
            if m3u8_match:
                url = m3u8_match.group(1)
                logger.info("Resolved m3u8 URL: %s", url)
                return url

            iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', resp.text)
            if iframe_match:
                url = iframe_match.group(1)
                logger.info("Found iframe URL: %s", url)
                return url

            if "m3u8" in resp.text.lower():
                return channel_url
        except Exception:
            logger.exception("Unexpected error in resolve_stream_url")

        return None

    def _make_absolute(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return f"{self.base_url}{url}"
        return f"{self.base_url}/{url}"

    @staticmethod
    def _extract_quality(name: str, url: str) -> str:
        text = f"{name} {url}".lower()
        if "4k" in text or "2160" in text:
            return "4K"
        if "1080" in text or "fhd" in text or "full hd" in text:
            return "1080p"
        if "720" in text or "hd" in text:
            return "720p"
        if "480" in text or "sd" in text:
            return "480p"
        if "360" in text:
            return "360p"
        return "HD"
