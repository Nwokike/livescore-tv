import flet as ft
from core.state import state, Match
from core.theme import AppColors


def build_home_view(
    page_obj: ft.Page,
    on_load_matches,
    on_select_match,
    on_search_click,
) -> ft.View:

    CARD_HEIGHT = 100

    matches_list = ft.Column(spacing=12)

    def on_hover_card(e, container):
        if e.data == "true":
            container.scale = 1.02
            container.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY),
                offset=ft.Offset(0, 4),
            )
        else:
            container.scale = 1.0
            container.shadow = None
        container.update()

    def build_match_card(match: Match, idx: int):
        is_live = match.status == "LIVE" or (match.status == "1H" or match.status == "2H" or match.status == "HT")

        score_text = ""
        if is_live and (match.home_score or match.away_score):
            score_text = f"{match.home_score} - {match.away_score}"

        time_badge = ft.Container(
            content=ft.Text(
                "LIVE" if is_live else match.time,
                size=11,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            padding=ft.Padding(8, 4, 8, 4),
            bgcolor=AppColors.LIVE if is_live else AppColors.PRIMARY,
            border_radius=6,
        )

        teams_row = ft.Row(
            controls=[
                ft.Text(match.home_team, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE, expand=True),
                ft.Text(score_text, size=14, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY if is_live else ft.Colors.ON_SURFACE),
                ft.Text(match.away_team, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE, expand=True, text_align=ft.TextAlign.RIGHT),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        card_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([time_badge, ft.Text(match.league, size=12, color=ft.Colors.ON_SURFACE_VARIANT)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=8),
                    teams_row,
                ],
                spacing=0,
            ),
            padding=16,
            border_radius=12,
            bgcolor=AppColors.get_surface_variant(page_obj),
            clip_behavior="antiAlias",
            animate_scale=300,
            animate=300,
            ink=True,
            height=CARD_HEIGHT,
            key=f"match_{idx}",
            on_click=lambda _: on_select_match(match),
            on_hover=lambda e: on_hover_card(e, card_container),
        )
        card_container.tab_index = idx + 3
        card_container.on_focus = lambda e: _on_focus_card(e, card_container)
        card_container.on_blur = lambda e: _on_blur_card(e, card_container)

        return card_container

    def _on_focus_card(e, ctrl):
        ctrl.scale = 1.02
        ctrl.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY),
            offset=ft.Offset(0, 4),
        )
        ctrl.border = ft.Border.all(2, AppColors.PRIMARY)
        try:
            ctrl.update()
        except Exception:
            pass

    def _on_blur_card(e, ctrl):
        ctrl.scale = 1.0
        ctrl.shadow = None
        ctrl.border = ft.Border.all(0, ft.Colors.TRANSPARENT)
        try:
            ctrl.update()
        except Exception:
            pass

    def update_list():
        matches_list.controls.clear()

        for group in state.matches_by_league:
            league = group.get("league", "")
            matches = group.get("matches", [])

            if not matches:
                continue

            league_header = ft.Container(
                padding=ft.Padding.only(top=16, bottom=8),
                content=ft.Text(
                    league,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.PRIMARY,
                ),
            )
            matches_list.controls.append(league_header)

            for i, match in enumerate(matches):
                matches_list.controls.append(build_match_card(match, i))

        if state.is_loading and not state.matches_by_league:
            scroll_content.controls = [
                header,
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.ProgressRing(color=AppColors.PRIMARY, stroke_width=4)
                )
            ]
        elif not state.matches_by_league:
            scroll_content.controls = [
                header,
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("No matches found for today", color=ft.Colors.ON_SURFACE_VARIANT, size=16)
                )
            ]
        else:
            scroll_content.controls = [header, matches_list]

        page_obj.update()

    def handle_theme_toggle(e):
        page_obj.theme_mode = ft.ThemeMode.LIGHT if page_obj.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        page_obj.update()

    def _on_focus_btn(e):
        e.control.bgcolor = ft.Colors.with_opacity(0.1, AppColors.PRIMARY)
        try:
            e.control.update()
        except Exception:
            pass

    def _on_blur_btn(e):
        e.control.bgcolor = None
        try:
            e.control.update()
        except Exception:
            pass

    search_btn = ft.Container(
        content=ft.Icon(ft.Icons.SEARCH_ROUNDED, color=ft.Colors.ON_SURFACE),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=lambda _: on_search_click(),
    )
    search_btn.tab_index = 1
    search_btn.on_focus = _on_focus_btn
    search_btn.on_blur = _on_blur_btn

    theme_btn = ft.Container(
        content=ft.Icon(
            ft.Icons.LIGHT_MODE_ROUNDED if page_obj.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE_ROUNDED,
            color=ft.Colors.ON_SURFACE,
        ),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=handle_theme_toggle,
    )
    theme_btn.tab_index = 2
    theme_btn.on_focus = _on_focus_btn
    theme_btn.on_blur = _on_blur_btn

    header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=8),
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Image(src="icon.png", width=32, height=32, fit="contain"),
                        ft.Text("Score808 TV", size=24, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    controls=[search_btn, theme_btn],
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
    )

    scroll_content = ft.Column(
        controls=[header, matches_list],
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

    if not state.matches_by_league and not state.is_loading:
        page_obj.run_task(on_load_matches)

    page_obj.update_matches_list = update_list
    update_list()

    return view
