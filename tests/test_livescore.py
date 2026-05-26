import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Ensure src/ is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.errors import NetworkError
from services.livescore import LivescoreAPI


class TestLivescoreAPI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.api = LivescoreAPI()

    async def asyncTearDown(self):
        await self.api.close()

    def test_format_time(self):
        # Esd format: YYYYMMDDHHMMSS
        # 2026-05-26 13:00:00 UTC
        timestamp = 20260526130000
        formatted = self.api._format_time(timestamp)
        self.assertNotEqual(formatted, "")

        # Test UTC to local timezone formatting
        dt = datetime.strptime("20260526130000", "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        expected = dt.astimezone().strftime("%H:%M")
        self.assertEqual(formatted, expected)

        # Test invalid inputs
        self.assertEqual(self.api._format_time(0), "")
        self.assertEqual(self.api._format_time(12345), "")

    def test_parse_response(self):
        mock_data = {
            "Stages": [
                {
                    "Cnm": "Premier League",
                    "Events": [
                        {
                            "Eid": "12345",
                            "Eps": "FT",
                            "Esd": 20260526150000,
                            "T1": [{"Nm": "Arsenal", "Img": "enet/123.png"}],
                            "T2": [{"Nm": "Chelsea", "Img": "teambadge/456.png"}],
                            "Tr1": 2,
                            "Tr2": 1,
                        }
                    ],
                }
            ]
        }

        matches = self.api._parse_response(mock_data)
        self.assertEqual(len(matches), 1)

        match = matches[0]
        self.assertEqual(match.id, "12345")
        self.assertEqual(match.home_team, "Arsenal")
        self.assertEqual(match.away_team, "Chelsea")
        self.assertEqual(match.league, "Premier League")
        self.assertEqual(match.status, "FT")
        self.assertEqual(match.home_score, "2")
        self.assertEqual(match.away_score, "1")
        self.assertEqual(match.home_logo, "https://lsm-static-prod.livescore.com/medium/enet/123.png")
        self.assertEqual(match.away_logo, "https://lsm-static-prod.livescore.com/medium/teambadge/456.png")

    @patch("httpx.AsyncClient.get")
    async def test_get_matches_by_date_success(self, mock_get):
        # Mock responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "Stages": [
                {
                    "Cnm": "La Liga",
                    "Events": [
                        {
                            "Eid": "999",
                            "Eps": "NS",
                            "Esd": 20260526180000,
                            "T1": [{"Nm": "Real Madrid", "Img": "enet/789.png"}],
                            "T2": [{"Nm": "Barcelona", "Img": "enet/999.png"}],
                        }
                    ],
                }
            ]
        }
        mock_get.return_value = mock_response

        matches = await self.api.get_matches_by_date("2026-05-26")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].home_team, "Real Madrid")
        self.assertEqual(matches[0].away_team, "Barcelona")
        self.assertEqual(matches[0].status, "NS")
        self.assertEqual(matches[0].home_score, "")
        self.assertEqual(matches[0].away_score, "")

    @patch("httpx.AsyncClient.get")
    async def test_get_matches_by_date_network_error(self, mock_get):
        mock_get.side_effect = Exception("Connection Refused")

        with self.assertRaises(NetworkError):
            await self.api.get_matches_by_date("2026-05-26")


if __name__ == "__main__":
    unittest.main()
