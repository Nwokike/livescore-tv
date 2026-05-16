import httpx
from datetime import datetime
from core.state import Match
from core.config import LIVESCORE_API_URL


class LivescoreAPI:
    def __init__(self):
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
            timeout=15,
            follow_redirects=True,
        )

    def close(self):
        self.client.close()

    def get_today_matches(self) -> list[Match]:
        date_str = datetime.now().strftime("%Y%m%d")
        url = f"{LIVESCORE_API_URL}/{date_str}/0"

        try:
            resp = self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_response(data)
        except Exception:
            return []

    def get_matches_by_date(self, date: str) -> list[Match]:
        date_str = date.replace("-", "")
        url = f"{LIVESCORE_API_URL}/{date_str}/0"

        try:
            resp = self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_response(data)
        except Exception:
            return []

    def _parse_response(self, data: dict) -> list[Match]:
        matches = []
        stages = data.get("Stages", [])

        for stage in stages:
            league = stage.get("Cnm", "")
            events = stage.get("Events", [])

            for event in events:
                match = Match(
                    id=str(event.get("Eid", "")),
                    home_team=event.get("Tr1", ""),
                    away_team=event.get("Tr2", ""),
                    league=league,
                    time=self._format_time(event.get("Esd", 0)),
                    status=event.get("Eps", "NS"),
                    home_score=str(event.get("Tr1S", "")),
                    away_score=str(event.get("Tr2S", "")),
                )
                if match.home_team and match.away_team:
                    matches.append(match)

        return matches

    def _format_time(self, timestamp: int) -> str:
        if not timestamp:
            return ""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%H:%M")
        except Exception:
            return ""
