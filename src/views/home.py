import flet as ft

from components.loading_state import build_empty_state, build_loading_centered
from components.match_card import build_match_card
from core.constants import APP_NAME, LBL_NO_MATCHES_TODAY
from core.focus_manager import make_focusable_button
from core.state import state
from core.theme import AppColors


def build_home_view(
    page_obj: ft.Page,
    controller,
    on_select_match,
    on_search_click,
) -> ft.View:

    leagues_column = ft.Column(spacing=12)
    surface_variant = AppColors.get_surface_variant(page_obj)

    def update_list():
        leagues_column.controls.clear()

        if state.is_loading and not state.matches_by_league:
            leagues_column.controls.append(build_loading_centered("Loading matches..."))
        elif state.error_message and not state.matches_by_league:
            leagues_column.controls.append(
                build_empty_state(
                    state.error_message,
                    icon=ft.Icons.WIFI_OFF_ROUNDED,
                )
            )
        elif state.matches_by_league:
            live_groups = []
            other_groups = []

            for group in state.matches_by_league:
                league = group.get("league", "")
                league_matches = group.get("matches", [])
                if not league_matches:
                    continue

                has_live = any(m.status in ("LIVE", "1H", "2H") for m in league_matches)
                group_data = {"league": league, "matches": league_matches, "has_live": has_live}

                if has_live:
                    live_groups.append(group_data)
                else:
                    other_groups.append(group_data)

            ordered = live_groups + other_groups

            for group_idx, group in enumerate(ordered):
                league = group["league"]
                league_matches = group["matches"]
                has_live = group["has_live"]

                tile_controls = []
                for i, match in enumerate(league_matches):
                    tile_controls.append(
                        build_match_card(match, on_select_match, page_obj, i, surface_variant)
                    )

                live_indicator = ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                width=8, height=8, border_radius=4, bgcolor=AppColors.LIVE,
                                animate_scale=500,
                            ),
                            ft.Text("LIVE", size=10, weight=ft.FontWeight.BOLD, color=AppColors.LIVE),
                        ],
                        spacing=4,
                    ),
                    visible=has_live,
                )

                exp_tile = ft.ExpansionTile(
                    title=ft.Row(
                        [
                            ft.Text(
                                league,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE,
                                size=14,
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                str(len(league_matches)),
                                size=12,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
                                padding=ft.Padding(8, 2, 8, 2),
                                border_radius=10,
                            ),
                            ft.Container(width=4),
                            live_indicator,
                        ],
                    ),
                    expanded=(group_idx == 0),
                    collapsed_bgcolor=ft.Colors.TRANSPARENT,
                    bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.ON_SURFACE),
                    controls=tile_controls,
                    shape=ft.BorderRadius(12, 12, 12, 12),
                )

                leagues_column.controls.append(exp_tile)
        else:
            leagues_column.controls.append(build_empty_state(LBL_NO_MATCHES_TODAY))

        page_obj.update()

    def handle_theme_toggle(e):
        theme_btn.disabled = True
        page_obj.update()
        page_obj.theme_mode = ft.ThemeMode.LIGHT if page_obj.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        theme_btn.content = ft.Icon(
            ft.Icons.LIGHT_MODE_ROUNDED if page_obj.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE_ROUNDED,
            color=ft.Colors.ON_SURFACE,
        )
        theme_btn.disabled = False
        page_obj.update()

    def handle_refresh(e):
        refresh_btn.disabled = True
        refresh_btn.content = ft.ProgressRing(
            color=ft.Colors.ON_SURFACE, stroke_width=2, width=18, height=18
        )
        page_obj.update()
        state.matches_by_league = []
        state.is_loading = True
        update_list()
        page_obj.run_task(controller.load_matches)

    search_btn = ft.Container(
        content=ft.Icon(ft.Icons.SEARCH_ROUNDED, color=ft.Colors.ON_SURFACE),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=lambda _: on_search_click(),
        tooltip="Search",
    )
    search_btn.tab_index = 1
    make_focusable_button(search_btn)

    theme_btn = ft.Container(
        content=ft.Icon(
            ft.Icons.LIGHT_MODE_ROUNDED if page_obj.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE_ROUNDED,
            color=ft.Colors.ON_SURFACE,
        ),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=handle_theme_toggle,
        tooltip="Toggle theme",
    )
    theme_btn.tab_index = 2
    make_focusable_button(theme_btn)

    refresh_btn = ft.Container(
        content=ft.Icon(ft.Icons.REFRESH_ROUNDED, color=ft.Colors.ON_SURFACE),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=handle_refresh,
        tooltip="Refresh",
    )
    refresh_btn.tab_index = 3
    make_focusable_button(refresh_btn)

    header = ft.Container(
        padding=ft.Padding.only(left=20, right=20, top=20, bottom=12),
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Image(src="icon.png", width=28, height=28, fit="contain"),
                        ft.Text(APP_NAME, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ],
                    spacing=10,
                ),
                ft.Row(
                    controls=[refresh_btn, search_btn, theme_btn],
                    spacing=2,
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
    )

    scroll_content = ft.Column(
        controls=[header, leagues_column],
        expand=False,
        spacing=0,
    )

    scrollable = ft.ListView(
        expand=True,
        controls=[scroll_content],
        padding=0,
        spacing=0,
        auto_scroll=True,
    )

    view = ft.View(
        route="/home",
        controls=[
            ft.SafeArea(
                ft.Container(
                    content=scrollable,
                    expand=True,
                    bgcolor=ft.Colors.SURFACE,
                ),
                expand=True,
            )
        ],
        padding=0,
    )

    state.on_matches_loaded = update_list
    page_obj.update_matches_list = update_list

    if not state.matches_by_league and not state.is_loading:
        state.is_loading = True
        update_list()
        page_obj.run_task(controller.load_matches)
    else:
        update_list()

    return view
