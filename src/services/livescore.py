import logging
from datetime import datetime, timezone

import httpx

from core.config import LIVESCORE_API_URL
from core.constants import HTTP_MAX_CONNECTIONS, HTTP_MAX_KEEPALIVE, HTTP_MAX_RETRIES, HTTP_TIMEOUT
from core.errors import NetworkError
from core.state import Match

logger = logging.getLogger("score808.livescore")


class LivescoreAPI:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
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
            logger.info("Livescore API client closed")

    async def get_today_matches(self) -> list[Match]:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        url = f"{LIVESCORE_API_URL}/{date_str}/0"
        return await self._fetch_matches(url)

    async def get_matches_by_date(self, date: str) -> list[Match]:
        date_str = date.replace("-", "")
        url = f"{LIVESCORE_API_URL}/{date_str}/0"
        return await self._fetch_matches(url)

    async def _fetch_matches(self, url: str) -> list[Match]:
        client = self._get_client()
        for attempt in range(HTTP_MAX_RETRIES):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                if "application/json" not in content_type:
                    logger.error("Unexpected content-type: %s", content_type)
                    raise NetworkError("API returned non-JSON response")
                data = resp.json()
                matches = self._parse_response(data)
                logger.info("Fetched %d matches from %s", len(matches), url)
                return matches
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (502, 503, 504) and attempt < HTTP_MAX_RETRIES - 1:
                    wait = 2**attempt
                    logger.warning(
                        "HTTP %d, retry %d/%d in %ds", e.response.status_code, attempt + 1, HTTP_MAX_RETRIES, wait
                    )
                    await __import__("asyncio").sleep(wait)
                    continue
                logger.error("HTTP error %d for %s", e.response.status_code, url)
                raise NetworkError(f"API returned {e.response.status_code}") from e
            except httpx.RequestError as e:
                if attempt < HTTP_MAX_RETRIES - 1:
                    wait = 2**attempt
                    logger.warning("Request error, retry %d/%d in %ds: %s", attempt + 1, HTTP_MAX_RETRIES, wait, e)
                    await __import__("asyncio").sleep(wait)
                    continue
                logger.error("Network error fetching %s: %s", url, e)
                raise NetworkError(f"Network error: {e}") from e
            except NetworkError:
                raise
            except Exception as e:
                logger.exception("Unexpected error fetching matches from %s", url)
                raise NetworkError(f"Failed to fetch matches: {e}") from e
        raise NetworkError("All retries exhausted")

    def _parse_response(self, data: dict) -> list[Match]:
        matches = []
        stages = data.get("Stages", [])

        for stage in stages:
            league = stage.get("Cnm", "")
            events = stage.get("Events", [])

            for event in events:
                t1_list = event.get("T1", [])
                t2_list = event.get("T2", [])
                if not t1_list or not t2_list:
                    continue
                t1 = t1_list[0]
                t2 = t2_list[0]

                home_team = t1.get("Nm", "")
                away_team = t2.get("Nm", "")

                home_img = t1.get("Img", "")
                away_img = t2.get("Img", "")

                home_logo = f"https://lsm-static-prod.livescore.com/medium/{home_img}" if home_img else ""
                away_logo = f"https://lsm-static-prod.livescore.com/medium/{away_img}" if away_img else ""

                tr1 = event.get("Tr1")
                tr2 = event.get("Tr2")
                home_score = str(tr1) if tr1 is not None else ""
                away_score = str(tr2) if tr2 is not None else ""

                match = Match(
                    id=str(event.get("Eid", "")),
                    home_team=home_team,
                    away_team=away_team,
                    league=league,
                    time=self._format_time(event.get("Esd", 0)),
                    status=event.get("Eps", "NS"),
                    home_score=home_score,
                    away_score=away_score,
                    home_logo=home_logo,
                    away_logo=away_logo,
                )
                if match.home_team and match.away_team:
                    matches.append(match)

        return matches

    def _format_time(self, timestamp: int) -> str:
        if not timestamp:
            return ""
        try:
            ts_str = str(timestamp)
            if len(ts_str) == 14:
                # Parse YYYYMMDDHHMMSS as UTC
                dt = datetime.strptime(ts_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                # Convert to local timezone
                local_dt = dt.astimezone()
                return local_dt.strftime("%H:%M")
        except Exception:
            pass
        return ""
