import asyncio
import base64
import logging
import urllib.parse

import flet as ft
import httpx

from components.ktv_dialog import show_ktv_install_dialog
from core.config import KTV_DEEP_LINK_SCHEME, SPLASH_DURATION_SEC, USE_EXTERNAL_PLAYER
from core.constants import (
    APP_NAME,
    CACHE_TTL_MATCHES,
    CACHE_TTL_SEARCH,
    CACHE_TTL_STREAMS,
    ERR_NETWORK,
    RATE_LIMIT_MAX_CALLS,
    RATE_LIMIT_WINDOW,
)
from core.errors import NetworkError
from core.state import Match, StreamChannel, state
from core.theme import AppColors, AppTheme
from views.home import build_home_view
from views.match_detail import build_match_detail_view
from views.search import build_search_view
from views.splash import build_splash_view

logger = logging.getLogger("score808.controller")


def _dict_to_match(d: dict | Match) -> Match:
    if isinstance(d, Match):
        return d
    return Match(
        id=str(d.get("id", "")),
        home_team=d.get("home_team", ""),
        away_team=d.get("away_team", ""),
        league=d.get("league", ""),
        time=d.get("time", ""),
        status=d.get("status", "NS"),
        home_score=str(d.get("home_score", "")),
        away_score=str(d.get("away_score", "")),
        poster=d.get("poster", ""),
        home_logo=d.get("home_logo", ""),
        away_logo=d.get("away_logo", ""),
    )


def _dict_to_channel(d: dict | StreamChannel) -> StreamChannel:
    if isinstance(d, StreamChannel):
        return d
    return StreamChannel(
        name=d.get("name", ""),
        url=d.get("url", ""),
        quality=d.get("quality", ""),
    )


def _restore_matches(cached: list[dict]) -> list[dict]:
    return [
        {
            "league": group.get("league", ""),
            "matches": [_dict_to_match(m) for m in group.get("matches", [])],
        }
        for group in cached
    ]


def _restore_channels(cached: list[dict]) -> list[StreamChannel]:
    return [_dict_to_channel(c) for c in cached]


class RateLimiter:
    def __init__(self, max_calls: int = RATE_LIMIT_MAX_CALLS, window_seconds: int = RATE_LIMIT_WINDOW):
        self.calls: list[float] = []
        self.max_calls = max_calls
        self.window = window_seconds

    async def wait_if_needed(self):
        now = asyncio.get_running_loop().time()
        self.calls = [t for t in self.calls if now - t < self.window]
        if len(self.calls) >= self.max_calls:
            wait_time = self.window - (now - self.calls[0])
            if wait_time > 0:
                logger.warning("Rate limit reached, waiting %.1fs", wait_time)
                await asyncio.sleep(wait_time)
        self.calls.append(asyncio.get_running_loop().time())


class AppController:
    def __init__(self, page, livescore, scraper, cache):
        self.page = page
        self.livescore = livescore
        self.scraper = scraper
        self.cache = cache
        self._loading_locks: dict[str, asyncio.Lock] = {}
        self._rate_limiter = RateLimiter()

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._loading_locks:
            self._loading_locks[key] = asyncio.Lock()
        return self._loading_locks[key]

    async def init(self):
        self.page.title = APP_NAME
        self.page.padding = 0
        self.page.spacing = 0

        self.page.fonts = {"Outfit": "assets/outfit.css"}
        self.page.theme = AppTheme.get_light_theme()
        self.page.dark_theme = AppTheme.get_dark_theme()
        self.page.theme.font_family = "Outfit"
        self.page.dark_theme.font_family = "Outfit"
        self.page.theme_mode = ft.ThemeMode.SYSTEM

        self.page.on_error = lambda e: self._show_error_snackbar()

        await self.cache._get_db()
        await self.cache.start_sweep()
        logger.info("AppController initialized")

    async def cleanup(self):
        if self.livescore:
            await self.livescore.close()
        if self.scraper:
            await self.scraper.close()
        if self.cache:
            await self.cache.close()
        logger.info("AppController cleaned up")

    def _show_error_snackbar(self):
        try:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(ERR_NETWORK),
                bgcolor=AppColors.ERROR,
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            pass

    def handle_global_back(self):
        if len(self.page.views) > 1:
            self.page.views.pop()
            if self.page.views:
                self.page.route = self.page.views[-1].route
            self.page.update()

    async def navigate(self, route: str):
        await self.page.push_route(route)

    async def load_matches(self):
        lock = self._get_lock("matches")
        if lock.locked():
            return
        async with lock:
            await self._rate_limiter.wait_if_needed()

            date_clean = state.selected_date.replace("-", "")
            cache_key = f"matches_{date_clean}"
            try:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    state.matches_by_league = _restore_matches(cached)
                    state.error_message = None
                    state.is_loading = False
                    self._update_matches_list()
                    logger.info("Loaded %d leagues from cache for %s", len(cached), state.selected_date)
                    return
            except Exception as e:
                logger.error("Error reading cache for matches: %s", e)

            state.is_loading = True
            state.error_message = None
            self._update_matches_list()

            try:
                matches = await self.livescore.get_matches_by_date(state.selected_date)
                by_league = {}
                for m in matches:
                    if m.league not in by_league:
                        by_league[m.league] = []
                    by_league[m.league].append(m)

                state.matches_by_league = [
                    {"league": league, "matches": matches_list} for league, matches_list in by_league.items()
                ]

                try:
                    await self.cache.set_json(cache_key, state.matches_by_league, ttl=CACHE_TTL_MATCHES)
                except Exception as e:
                    logger.error("Error setting cache for matches: %s", e)

                if not state.matches_by_league:
                    state.error_message = f"No matches scheduled for {state.selected_date}"
                else:
                    state.error_message = None

                logger.info("Loaded %d matches (%d leagues) for %s", len(matches), len(by_league), state.selected_date)
            except NetworkError as e:
                state.error_message = str(e)
                state.matches_by_league = []
            except Exception as e:
                logger.exception("Unexpected error in load_matches")
                state.error_message = f"An unexpected error occurred: {e}"
                state.matches_by_league = []
            finally:
                state.is_loading = False
                self._update_matches_list()

    async def load_search(self, query: str):
        lock = self._get_lock("search")
        if lock.locked():
            return
        async with lock:
            state.is_loading = True
            state.search_query = query
            state.error_message = None
            self._refresh_search_results()

            cache_key = f"search_{query.lower()}"
            try:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    state.search_results = [_dict_to_match(m) if not isinstance(m, Match) else m for m in cached]
                    state.search_has_more = False
                    state.is_loading = False
                    self._refresh_search_results()
                    return
            except Exception as e:
                logger.error("Error reading cache for search: %s", e)

            try:
                matches = await self.livescore.get_today_matches()
                query_lower = query.lower()
                results = [
                    m
                    for m in matches
                    if query_lower in m.home_team.lower()
                    or query_lower in m.away_team.lower()
                    or query_lower in m.league.lower()
                ]

                state.search_results = results
                state.search_has_more = False

                try:
                    await self.cache.set_json(cache_key, results, ttl=CACHE_TTL_SEARCH)
                except Exception as e:
                    logger.error("Error setting cache for search: %s", e)

                logger.info("Search '%s' returned %d results", query, len(results))
            except NetworkError as e:
                state.error_message = str(e)
                state.search_results = []
            except Exception as e:
                logger.exception("Unexpected error in load_search")
                state.error_message = f"Search failed: {e}"
                state.search_results = []
            finally:
                state.is_loading = False
                self._refresh_search_results()

    async def load_streams(self, match: Match):
        lock = self._get_lock(f"streams_{match.id}")
        if lock.locked():
            return
        async with lock:
            await self._rate_limiter.wait_if_needed()

            state.is_loading = True
            state.error_message = None
            self._update_channels_list()

            cache_key = f"streams_{match.id}"
            try:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    state.match_channels = _restore_channels(cached)
                    state.is_loading = False
                    self._update_channels_list()
                    logger.info("Loaded %d streams from cache for match %s", len(cached), match.id)
                    return
            except Exception as e:
                logger.error("Error reading cache for streams: %s", e)

            try:
                match_url = await self.scraper.find_match_page_by_id(match.id)
                if not match_url:
                    match_url = await self.scraper.find_match_page(match.home_team, match.away_team)

                channels: list[StreamChannel] = []
                if match_url:
                    channels = await self.scraper.get_streams_from_match_page(match_url)

                if not channels:
                    channels = self.scraper._get_fallback_channels()

                state.match_channels = channels
                try:
                    await self.cache.set_json(cache_key, channels, ttl=CACHE_TTL_STREAMS)
                except Exception as e:
                    logger.error("Error setting cache for streams: %s", e)

                logger.info("Loaded %d streams for match %s", len(channels), match.id)
            except Exception:
                logger.exception("Unexpected error loading streams")
                try:
                    state.match_channels = self.scraper._get_fallback_channels()
                except Exception:
                    state.match_channels = []
                state.error_message = None
            finally:
                state.is_loading = False
                self._update_channels_list()

    async def play_stream(self, channel: StreamChannel):
        if USE_EXTERNAL_PLAYER:
            await self._play_stream_external(channel)
        else:
            await self._play_stream_internal(channel)

    async def _play_stream_internal(self, channel: StreamChannel):
        resolved_url = await self.scraper.resolve_stream_url(channel.url)
        if not resolved_url:
            resolved_url = channel.url

        state.stream_url = resolved_url
        await self.navigate("/play")

    async def _play_stream_external(self, channel: StreamChannel):
        resolved_url = await self.scraper.resolve_stream_url(channel.url)
        if not resolved_url:
            resolved_url = channel.url

        encoded_url = base64.urlsafe_b64encode(resolved_url.encode()).decode()
        deep_link = f"{KTV_DEEP_LINK_SCHEME}{encoded_url}"

        launcher = ft.UrlLauncher()
        try:
            if await launcher.can_launch_url(deep_link):
                await launcher.launch_url(deep_link)
                return
        except Exception:
            pass

        show_ktv_install_dialog(self.page)

    async def select_and_navigate(self, match):
        state.selected_match = match
        await self.navigate(f"/match?id={match.id}")

    async def splash_complete(self):
        await asyncio.sleep(SPLASH_DURATION_SEC)
        await self.navigate("/home")

    async def route_change(self, e: ft.RouteChangeEvent | None = None):
        route = self.page.route
        parsed = urllib.parse.urlparse(route)

        if parsed.path in ["/", "/home", "/search"]:
            self.page.views.clear()

        if parsed.path == "/":
            self.page.views.append(build_splash_view())
            self.page.run_task(self.splash_complete)

        elif parsed.path == "/home":
            self.page.views.append(
                build_home_view(
                    page_obj=self.page,
                    controller=self,
                    on_select_match=lambda m: self.page.run_task(self.select_and_navigate, m),
                    on_search_click=lambda: self.page.run_task(self.navigate, "/search"),
                )
            )

        elif parsed.path == "/search":
            state.reset_search()
            self.page.views.append(
                build_search_view(
                    page_obj=self.page,
                    controller=self,
                    on_select_match=lambda m: self.page.run_task(self.select_and_navigate, m),
                    on_back=lambda: self.page.run_task(self.navigate, "/home"),
                )
            )

        elif parsed.path == "/match":
            params = urllib.parse.parse_qs(parsed.query)
            match_id = params.get("id", [None])[0]
            if match_id and state.selected_match:
                state.reset_player()
                self.page.views.append(
                    build_match_detail_view(
                        page_obj=self.page,
                        match=state.selected_match,
                        controller=self,
                        on_back=lambda: self.page.run_task(self.navigate, "/home"),
                    )
                )
                self.page.run_task(self.load_streams, state.selected_match)

        elif parsed.path == "/play":
            try:
                self.page.pop_dialog()
            except Exception:
                pass
            if state.stream_url:
                self.page.views.append(
                    build_player_view(
                        page_obj=self.page,
                        stream_url=state.stream_url,
                        on_back=lambda: self.page.run_task(self.navigate, "/match"),
                    )
                )
            else:
                await self.navigate("/home")

        self.page.update()

    def view_pop(self, e: ft.ViewPopEvent):
        if len(self.page.views) > 1:
            top_view = self.page.views[-1]
            route = getattr(top_view, "route", "")
            if route.startswith("/play"):
                for control in top_view.controls:
                    if hasattr(control, "pause"):
                        try:
                            control.pause()
                        except Exception:
                            pass
                state.reset_player()

            self.page.views.pop()
            self.page.update()

    def _update_matches_list(self):
        if hasattr(self.page, "update_matches_list"):
            self.page.update_matches_list()
        else:
            self.page.update()

    def _refresh_search_results(self):
        if hasattr(self.page, "refresh_search_results"):
            self.page.refresh_search_results()
        else:
            self.page.update()

    def _update_channels_list(self):
        if hasattr(self.page, "update_channels_list"):
            self.page.update_channels_list()
        else:
            self.page.update()

    async def check_channel_liveliness(self, channel: StreamChannel, indicator: ft.Container):
        is_live = False
        try:
            resolved_url = await self.scraper.resolve_stream_url(channel.url)
            if not resolved_url:
                resolved_url = channel.url

            async with httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                timeout=5.0,
                follow_redirects=True,
            ) as client:
                try:
                    resp = await client.head(resolved_url)
                    if resp.status_code in (200, 206):
                        is_live = True
                except Exception:
                    pass

                if not is_live:
                    try:
                        resp = await client.get(resolved_url, headers={"Range": "bytes=0-1023"})
                        if resp.status_code in (200, 206):
                            is_live = True
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("Error checking channel liveliness for %s: %s", channel.name, e)

        if is_live:
            indicator.bgcolor = AppColors.SUCCESS
        else:
            indicator.bgcolor = AppColors.ERROR

        try:
            indicator.update()
        except Exception:
            pass
