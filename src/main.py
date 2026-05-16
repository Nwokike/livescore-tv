import flet as ft
import asyncio
import base64
import urllib.parse

from core.theme import AppTheme, AppColors
from core.state import state
from core.config import USE_EXTERNAL_PLAYER, KTV_PLAY_STORE_URL, KTV_UPTODOWN_URL, KTV_DEEP_LINK_SCHEME, EXTERNAL_PLAYER_NAMES
from core.focus_manager import FocusManager
from services.livescore import LivescoreAPI
from services.score808 import Score808Scraper
from services.cache import Cache
from views.splash import build_splash_view
from views.home import build_home_view
from views.search import build_search_view
from views.match_detail import build_match_detail_view
from views.player import build_player_view


def show_ktv_install_dialog(page: ft.Page):
    def open_store(e):
        page.run_task(page.launch_url, KTV_PLAY_STORE_URL)

    def open_uptodown(e):
        page.run_task(page.launch_url, KTV_UPTODOWN_URL)

    def dismiss(e):
        try:
            page.close_dialog()
        except Exception:
            pass

    player_buttons = []
    for name in EXTERNAL_PLAYER_NAMES:
        player_buttons.append(
            ft.ElevatedButton(
                text=name,
                icon=ft.Icons.PLAY_CIRCLE_ROUNDED,
                on_click=open_store if name == "KTV Player" else open_store,
                style=ft.ButtonStyle(
                    bgcolor=AppColors.PRIMARY if name == "KTV Player" else AppColors.get_surface_variant(page),
                    color=ft.Colors.WHITE if name == "KTV Player" else ft.Colors.ON_SURFACE,
                ),
            )
        )

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Install a Player", weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                ft.Text(
                    "To stream this match, please install one of the following players. "
                    "We recommend KTV Player for the best experience.",
                    size=14,
                ),
                ft.Container(height=16),
                ft.Column(player_buttons, spacing=10),
            ],
            tight=True,
        ),
        actions=[
            ft.TextButton("Not now", on_click=dismiss),
            ft.TextButton("Download from Uptodown", on_click=open_uptodown),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    page.open(dlg)


async def main(page: ft.Page):
    page.title = "Score808 TV"
    page.padding = 0
    page.spacing = 0

    def global_error_handler(e):
        page.snack_bar = ft.SnackBar(
            ft.Text("Network error or stream unavailable."),
            bgcolor=AppColors.ERROR,
        )
        page.snack_bar.open = True
        page.update()

    page.on_error = global_error_handler

    page.fonts = {
        "Outfit": "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap"
    }
    page.theme = AppTheme.get_light_theme()
    page.dark_theme = AppTheme.get_dark_theme()
    page.theme.font_family = "Outfit"
    page.dark_theme.font_family = "Outfit"
    page.theme_mode = ft.ThemeMode.SYSTEM

    livescore = LivescoreAPI()
    scraper = Score808Scraper()
    cache = Cache()

    focus_manager = FocusManager(page)

    state.livescore = livescore
    state.scraper = scraper
    state.cache = cache

    def handle_global_back():
        if len(page.views) > 1:
            top_view = page.views[-1]
            route = getattr(top_view, "route", "")

            if route.startswith("/play"):
                page.run_task(navigate, "/match")
            elif route == "/match":
                page.run_task(navigate, "/home")
            elif route == "/search":
                page.run_task(navigate, "/home")
            else:
                page.run_task(navigate, "/home")

    focus_manager.set_back_handler(handle_global_back)

    async def navigate(route: str):
        await page.push_route(route)

    async def load_matches():
        state.is_loading = True
        if hasattr(page, "update_matches_list"):
            page.update_matches_list()
        page.update()

        matches = livescore.get_today_matches()

        by_league = {}
        for m in matches:
            if m.league not in by_league:
                by_league[m.league] = []
            by_league[m.league].append(m)

        state.matches_by_league = [
            {"league": league, "matches": matches_list}
            for league, matches_list in by_league.items()
        ]

        state.is_loading = False
        if hasattr(page, "update_matches_list"):
            page.update_matches_list()
        page.update()

    async def load_search(query: str):
        state.is_loading = True
        state.search_query = query
        if hasattr(page, "refresh_search_results"):
            page.refresh_search_results()
        page.update()

        matches = livescore.get_today_matches()
        query_lower = query.lower()
        results = [
            m for m in matches
            if query_lower in m.home_team.lower()
            or query_lower in m.away_team.lower()
            or query_lower in m.league.lower()
        ]

        state.search_results = results
        state.search_has_more = False
        state.is_loading = False
        if hasattr(page, "refresh_search_results"):
            page.refresh_search_results()
        page.update()

    async def load_streams(match):
        state.is_loading = True
        state.selected_match = match
        if hasattr(page, "update_channels_list"):
            page.update_channels_list()
        page.update()

        match_url = scraper.find_match_page(match.home_team, match.away_team)
        channels = []

        if match_url:
            channels = scraper.get_streams_from_match_page(match_url)

        state.match_channels = channels
        state.is_loading = False
        if hasattr(page, "update_channels_list"):
            page.update_channels_list()
        page.update()

    async def play_stream(channel):
        if USE_EXTERNAL_PLAYER:
            await play_stream_external(channel)
        else:
            await play_stream_internal(channel)

    async def play_stream_internal(channel):
        resolved_url = scraper.resolve_stream_url(channel.url)
        if not resolved_url:
            resolved_url = channel.url

        state.stream_url = resolved_url
        page.snack_bar = ft.SnackBar(ft.Text("Loading stream..."), bgcolor=AppColors.SUCCESS)
        page.snack_bar.open = True
        page.update()

        await navigate("/play")

    async def play_stream_external(channel):
        resolved_url = scraper.resolve_stream_url(channel.url)
        if not resolved_url:
            resolved_url = channel.url

        encoded_url = base64.urlsafe_b64encode(resolved_url.encode()).decode()
        deep_link = f"{KTV_DEEP_LINK_SCHEME}{encoded_url}"

        try:
            await page.launch_url(deep_link)
        except Exception:
            pass

        show_ktv_install_dialog(page)

    async def splash_complete():
        await asyncio.sleep(1.5)
        await navigate("/home")

    async def select_and_navigate(match):
        state.selected_match = match
        await navigate(f"/match?id={match.id}")

    async def route_change(e: ft.RouteChangeEvent | None = None):
        route = page.route
        parsed = urllib.parse.urlparse(route)

        if parsed.path in ["/", "/home", "/search"]:
            page.views.clear()

        if parsed.path == "/":
            page.views.append(build_splash_view())
            page.run_task(splash_complete)

        elif parsed.path == "/home":
            page.views.append(
                build_home_view(
                    page_obj=page,
                    on_load_matches=load_matches,
                    on_select_match=lambda m: page.run_task(select_and_navigate, m),
                    on_search_click=lambda: page.run_task(navigate, "/search"),
                )
            )

        elif parsed.path == "/search":
            page.views.append(
                build_search_view(
                    page_obj=page,
                    on_search=load_search,
                    on_select_match=lambda m: page.run_task(select_and_navigate, m),
                    on_back=lambda: page.run_task(navigate, "/home"),
                )
            )

        elif parsed.path == "/match":
            params = urllib.parse.parse_qs(parsed.query)
            match_id = params.get("id", [None])[0]
            if match_id and state.selected_match:
                page.views.append(
                    build_match_detail_view(
                        page_obj=page,
                        match=state.selected_match,
                        on_load_streams=load_streams,
                        on_play=play_stream,
                        on_back=lambda: page.run_task(navigate, "/home"),
                    )
                )
                page.run_task(load_streams, state.selected_match)

        elif parsed.path == "/play":
            if state.stream_url:
                page.views.append(
                    build_player_view(
                        page_obj=page,
                        stream_url=state.stream_url,
                        on_back=lambda: page.run_task(navigate, "/match"),
                    )
                )
            else:
                await navigate("/home")

        page.update()

    def view_pop(e: ft.ViewPopEvent):
        if len(page.views) > 1:
            top_view = page.views[-1]
            route = getattr(top_view, "route", "")
            if route.startswith("/play"):
                for control in top_view.controls:
                    if hasattr(control, "pause"):
                        try:
                            control.pause()
                        except Exception:
                            pass

            page.views.pop()
            previous_view = page.views[-1]
            page.run_task(navigate, previous_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    await route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
