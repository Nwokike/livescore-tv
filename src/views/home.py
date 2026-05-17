import flet as ft

from components.loading_state import build_empty_state, build_loading_centered
from components.match_card import build_match_card
from core.constants import APP_NAME, LBL_NO_MATCHES_TODAY, LBL_REFRESH
from core.focus_manager import make_focusable_button
from core.state import state
from core.theme import AppColors


def build_home_view(
    page_obj: ft.Page,
    controller,
    on_select_match,
    on_search_click,
) -> ft.View:

    leagues_column = ft.Column(spacing=8)
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
            for group_idx, group in enumerate(state.matches_by_league):
                league = group.get("league", "")
                league_matches = group.get("matches", [])

                if not league_matches:
                    continue

                tile_controls = []
                for i, match in enumerate(league_matches):
                    tile_controls.append(
                        build_match_card(match, on_select_match, page_obj, i, surface_variant)
                    )

                exp_tile = ft.ExpansionTile(
                    title=ft.Text(
                        f"{league} ({len(league_matches)})",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    expanded=(group_idx == 0),
                    collapsed_bgcolor=ft.Colors.TRANSPARENT,
                    bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE),
                    controls=tile_controls,
                )
                exp_tile.on_focus = lambda e, ctrl=exp_tile: _on_tile_focus(ctrl, True)
                exp_tile.on_blur = lambda e, ctrl=exp_tile: _on_tile_focus(ctrl, False)

                leagues_column.controls.append(exp_tile)
        else:
            leagues_column.controls.append(build_empty_state(LBL_NO_MATCHES_TODAY))

        page_obj.update()

    def _on_tile_focus(control: ft.Container, focused: bool):
        if focused:
            control.collapsed_bgcolor = ft.Colors.with_opacity(0.12, AppColors.PRIMARY)
            control.bgcolor = ft.Colors.with_opacity(0.12, AppColors.PRIMARY)
        else:
            control.collapsed_bgcolor = ft.Colors.TRANSPARENT
            control.bgcolor = ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE)
        try:
            control.update()
        except Exception:
            pass

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
            color=ft.Colors.ON_SURFACE, stroke_width=2, width=20, height=20
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
        tooltip=LBL_REFRESH,
    )
    refresh_btn.tab_index = 3
    make_focusable_button(refresh_btn)

    header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=8),
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Image(src="icon.png", width=32, height=32, fit="contain"),
                        ft.Text(APP_NAME, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    controls=[refresh_btn, search_btn, theme_btn],
                    spacing=4,
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

    if not state.matches_by_league and not state.is_loading:
        state.is_loading = True
        update_list()
        page_obj.run_task(controller.load_matches)
    else:
        update_list()

    return view
