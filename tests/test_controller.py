import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft

# Ensure src/ is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.controller import AppController
from core.state import Match, StreamChannel, state
from services.cache import Cache
from services.livescore import LivescoreAPI


class FakePage:
    def __init__(self):
        self.title = ""
        self.padding = 0
        self.spacing = 0
        self.fonts = {}
        self.theme = MagicMock()
        self.dark_theme = MagicMock()
        self.theme_mode = None
        self.views = []
        self.route = "/home"
        self.update_called = 0
        self.update_matches_list_called = 0
        self.update_channels_list_called = 0

    def update(self):
        self.update_called += 1

    def update_matches_list(self):
        self.update_matches_list_called += 1

    def update_channels_list(self):
        self.update_channels_list_called += 1


class TestAppController(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Reset state parameters
        state.is_loading = False
        state.search_query = ""
        state.matches_by_league = []
        state.search_results = []
        state.selected_match = None
        state.match_channels = []
        state.stream_url = None
        state.error_message = None

        self.page = FakePage()
        self.livescore = MagicMock(spec=LivescoreAPI)
        self.livescore.close = AsyncMock()
        self.scraper = MagicMock()
        self.scraper.close = AsyncMock()
        self.cache = Cache(db_path="storage/data/test_controller.db")
        self.controller = AppController(self.page, self.livescore, self.scraper, self.cache)

    async def asyncTearDown(self):
        await self.controller.cleanup()
        if os.path.exists("storage/data/test_controller.db"):
            try:
                os.remove("storage/data/test_controller.db")
            except Exception:
                pass

    async def test_init(self):
        await self.controller.init()
        self.assertEqual(self.page.title, "Livescore TV")
        self.assertEqual(self.page.theme_mode.value, "system")

    async def test_load_matches_api_success(self):
        # Clear cache first
        await self.cache.clear()

        # Setup API mock matches
        mock_match = Match(
            id="1",
            home_team="Arsenal",
            away_team="Chelsea",
            league="EPL",
            time="15:00",
            status="NS",
            home_logo="home.png",
            away_logo="away.png",
        )
        self.livescore.get_matches_by_date = AsyncMock(return_value=[mock_match])

        # Execute load_matches
        await self.controller.load_matches()

        self.assertFalse(state.is_loading)
        self.assertEqual(len(state.matches_by_league), 1)
        self.assertEqual(state.matches_by_league[0]["league"], "EPL")
        self.assertEqual(state.matches_by_league[0]["matches"][0].home_team, "Arsenal")
        self.assertIsNone(state.error_message)

    async def test_load_matches_from_cache(self):
        await self.controller.init()

        # Manually save matches in cache
        date_clean = state.selected_date.replace("-", "")
        cache_key = f"matches_{date_clean}"
        cached_list = [
            {
                "league": "La Liga",
                "matches": [
                    {
                        "id": "2",
                        "home_team": "Barca",
                        "away_team": "Madrid",
                        "league": "La Liga",
                        "time": "20:00",
                        "status": "LIVE",
                        "home_logo": "b.png",
                        "away_logo": "m.png",
                        "home_score": "1",
                        "away_score": "0",
                    }
                ],
            }
        ]
        await self.cache.set_json(cache_key, cached_list, ttl=100)

        # load_matches should hit cache and NOT call the API
        self.livescore.get_matches_by_date = AsyncMock()  # Should not be called
        await self.controller.load_matches()

        self.livescore.get_matches_by_date.assert_not_called()
        self.assertEqual(len(state.matches_by_league), 1)
        self.assertEqual(state.matches_by_league[0]["league"], "La Liga")

        match = state.matches_by_league[0]["matches"][0]
        self.assertEqual(match.home_team, "Barca")
        self.assertEqual(match.away_team, "Madrid")
        self.assertEqual(match.home_logo, "b.png")

    async def test_load_search(self):
        # Setup pre-loaded matches
        mock_matches = [
            Match(id="1", home_team="Arsenal", away_team="Chelsea", league="EPL", time="15:00", status="NS"),
            Match(id="2", home_team="Milan", away_team="Inter", league="Serie A", time="19:00", status="LIVE"),
        ]
        self.livescore.get_today_matches = AsyncMock(return_value=mock_matches)

        # Search for "Inter"
        await self.controller.load_search("Inter")

        self.assertEqual(len(state.search_results), 1)
        self.assertEqual(state.search_results[0].home_team, "Milan")
        self.assertEqual(state.search_results[0].away_team, "Inter")

    async def test_load_streams(self):
        match = Match(id="123", home_team="A", away_team="B", league="L", time="12:00", status="LIVE")
        self.scraper.find_match_page_by_id = AsyncMock(return_value="https://score808.tv/match-123.html")

        mock_channels = [StreamChannel(name="Stream 1", url="https://stream.com/live.m3u8", quality="720p")]
        self.scraper.get_streams_from_match_page = AsyncMock(return_value=mock_channels)

        await self.controller.load_streams(match)

        self.assertEqual(len(state.match_channels), 1)
        self.assertEqual(state.match_channels[0].name, "Stream 1")
        self.assertEqual(state.match_channels[0].url, "https://stream.com/live.m3u8")

    @patch("core.controller.httpx.AsyncClient")
    async def test_check_channel_liveliness_live(self, mock_client_class):
        self.scraper.resolve_stream_url = AsyncMock(return_value="https://test.com/live.m3u8")

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client.head = AsyncMock(return_value=mock_resp)
        mock_client_class.return_value = mock_client

        channel = StreamChannel(name="Test Stream", url="https://test.com/live.m3u8", quality="720p")
        indicator = ft.Container()
        indicator.update = MagicMock()

        await self.controller.check_channel_liveliness(channel, indicator)

        from core.theme import AppColors

        self.assertEqual(indicator.bgcolor, AppColors.SUCCESS)
        indicator.update.assert_called_once()

    @patch("core.controller.httpx.AsyncClient")
    async def test_check_channel_liveliness_offline(self, mock_client_class):
        self.scraper.resolve_stream_url = AsyncMock(return_value="https://test.com/live.m3u8")

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        mock_client.head = AsyncMock(side_effect=Exception("HEAD failed"))

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_client.get = AsyncMock(return_value=mock_resp)

        mock_client_class.return_value = mock_client

        channel = StreamChannel(name="Test Stream", url="https://test.com/live.m3u8", quality="720p")
        indicator = ft.Container()
        indicator.update = MagicMock()

        await self.controller.check_channel_liveliness(channel, indicator)

        from core.theme import AppColors

        self.assertEqual(indicator.bgcolor, AppColors.ERROR)
        indicator.update.assert_called_once()


if __name__ == "__main__":
    unittest.main()
