import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure src/ is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from services.score808 import Score808Scraper


class TestScore808Scraper(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.scraper = Score808Scraper()

    async def asyncTearDown(self):
        await self.scraper.close()

    def test_make_absolute(self):
        self.scraper.base_url = "https://score808.tv"

        # Test already absolute
        self.assertEqual(self.scraper._make_absolute("https://test.com/stream.m3u8"), "https://test.com/stream.m3u8")
        # Test protocol relative
        self.assertEqual(self.scraper._make_absolute("//test.com/stream.m3u8"), "https://test.com/stream.m3u8")
        # Test relative path
        self.assertEqual(self.scraper._make_absolute("/play.html"), "https://score808.tv/play.html")
        # Test relative directory path
        self.assertEqual(self.scraper._make_absolute("watch.html"), "https://score808.tv/watch.html")

    def test_extract_quality(self):
        self.assertEqual(self.scraper._extract_quality("Stream 4K", ""), "4K")
        self.assertEqual(self.scraper._extract_quality("FHD Stream", ""), "1080p")
        self.assertEqual(self.scraper._extract_quality("HD Stream 720p", ""), "720p")
        self.assertEqual(self.scraper._extract_quality("SD Stream", ""), "480p")
        self.assertEqual(self.scraper._extract_quality("Low 360", ""), "360p")
        self.assertEqual(self.scraper._extract_quality("Normal Stream", ""), "HD")

    def test_fallback_channels(self):
        fallbacks = self.scraper._get_fallback_channels()
        self.assertEqual(len(fallbacks), 3)
        self.assertTrue(any("Red Bull" in c.name for c in fallbacks))
        self.assertTrue(all(c.url.startswith("http") for c in fallbacks))

    @patch("services.score808.Score808Scraper._get_with_retry")
    async def test_get_streams_from_match_page_empty(self, mock_retry):
        # Empty mock response
        mock_response = MagicMock()
        mock_response.text = "<html><body>No streams here</body></html>"
        mock_retry.return_value = mock_response

        # Should fall back to mock streams since no parsed streams exist
        channels = await self.scraper.get_streams_from_match_page("https://score808.tv/match.html")
        self.assertEqual(len(channels), 3)  # Fallback length is 3
        self.assertEqual(channels[0].name, "Sports Live Stream 1 (Red Bull TV HD)")

    @patch("services.score808.Score808Scraper._get_with_retry")
    async def test_get_streams_from_match_page_parsed(self, mock_retry):
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <a href="/stream/1.html">Stream Link 1 1080p</a>
                <iframe src="/embed/2.html" title="Iframe Stream 720p"></iframe>
            </body>
        </html>
        """
        mock_retry.return_value = mock_response
        self.scraper.base_url = "https://score808.tv"

        channels = await self.scraper.get_streams_from_match_page("https://score808.tv/match.html")
        self.assertEqual(len(channels), 2)

        self.assertEqual(channels[0].name, "Stream Link 1 1080p")
        self.assertEqual(channels[0].url, "https://score808.tv/stream/1.html")
        self.assertEqual(channels[0].quality, "1080p")

        self.assertEqual(channels[1].name, "Iframe Stream 720p")
        self.assertEqual(channels[1].url, "https://score808.tv/embed/2.html")
        self.assertEqual(channels[1].quality, "720p")

    @patch("services.score808.Score808Scraper._get_with_retry")
    async def test_resolve_stream_url_m3u8(self, mock_retry):
        # M3U8 directly passed through without HTTP request
        url = "https://test.com/live.m3u8"
        resolved = await self.scraper.resolve_stream_url(url)
        self.assertEqual(resolved, url)
        mock_retry.assert_not_called()

    @patch("services.score808.Score808Scraper._get_with_retry")
    async def test_resolve_stream_url_scraped(self, mock_retry):
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <script>
                    var player = "https://livecdn.com/live/master.m3u8?token=123";
                </script>
            </body>
        </html>
        """
        mock_retry.return_value = mock_response

        resolved = await self.scraper.resolve_stream_url("https://score808.tv/stream/1.html")
        self.assertEqual(resolved, "https://livecdn.com/live/master.m3u8?token=123")

    def test_parse_matches_from_nuxt(self):
        html = """
        <html>
            <body>
                <script>
                    window.__NUXT__ = {
                        data: [
                            {
                                matchId: 12345,
                                homeName: "Arsenal",
                                awayName: "Chelsea",
                                state: 1
                            },
                            {
                                matchId: 67890,
                                homeName: "Man Utd",
                                awayName: "Liverpool",
                                state: 0
                            }
                        ]
                    };
                </script>
            </body>
        </html>
        """
        matches = self.scraper._parse_matches_from_nuxt(html)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["id"], "12345")
        self.assertEqual(matches[0]["home"], "Arsenal")
        self.assertEqual(matches[0]["away"], "Chelsea")
        self.assertEqual(matches[1]["id"], "67890")

    @patch("services.score808.Score808Scraper._get_with_retry")
    async def test_find_match_page(self, mock_retry):
        mock_response = MagicMock()
        mock_response.text = """
        <script>
            window.__NUXT__ = { matchId: 999, homeName: "Real Madrid", awayName: "Barcelona" };
        </script>
        """
        mock_retry.return_value = mock_response

        # Test exact match
        url = await self.scraper.find_match_page("Real Madrid", "Barcelona")
        self.assertEqual(url, "score808://match/999")

        # Test relaxed/substring match
        url = await self.scraper.find_match_page("Madrid", "Barca")
        self.assertEqual(url, "score808://match/999")

        # Test no match
        url = await self.scraper.find_match_page("Arsenal", "Chelsea")
        self.assertIsNone(url)

    @patch("services.score808.Score808Scraper._get_with_retry")
    async def test_get_streams_from_match_page_api(self, mock_retry):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "channels": [{"id": "4001", "label": "Stream 1 HD"}, {"id": "4002", "label": "Stream 2 1080p"}]
        }
        mock_retry.return_value = mock_response

        channels = await self.scraper.get_streams_from_match_page("score808://match/999")
        # 2 channels * 3 CDN servers = 6 stream channels total
        self.assertEqual(len(channels), 6)
        self.assertEqual(channels[0].name, "Stream 1 HD (CDN Backup 1)")
        self.assertEqual(channels[0].url, "https://saten1-m2bpb.forbbpplay.cyou/live/4001.m3u8")
        self.assertEqual(channels[0].quality, "720p")

        self.assertEqual(channels[5].name, "Stream 2 1080p (CDN Backup 3)")
        self.assertEqual(channels[5].url, "https://saten3-m2bpb.forbbpplay.cyou/live/4002.m3u8")
        self.assertEqual(channels[5].quality, "1080p")


if __name__ == "__main__":
    unittest.main()
