import flet as ft
from core.state import state, Match
from core.theme import AppColors


def build_search_view(
    page_obj: ft.Page,
    on_search,
    on_select_match,
    on_back,
) -> ft.View:

    search_field = ft.TextField(
        hint_text="Search teams or leagues...",
        border=ft.InputBorder.OUTLINE,
        border_radius=12,
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        on_submit=lambda e: page_obj.run_task(on_search, e.control.value.strip()),
        autofocus=True,
        expand=True,
    )

    results_list = ft.Column(spacing=12)

    def build_match_card(match: Match, idx: int):
        is_live = match.status in ("LIVE", "1H", "2H", "HT")

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

        card_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([time_badge, ft.Text(match.league, size=12, color=ft.Colors.ON_SURFACE_VARIANT)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Text(match.home_team, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE, expand=True),
                            ft.Text(score_text, size=14, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY if is_live else ft.Colors.ON_SURFACE),
                            ft.Text(match.away_team, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE, expand=True, text_align=ft.TextAlign.RIGHT),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=0,
            ),
            padding=16,
            border_radius=12,
            bgcolor=AppColors.get_surface_variant(page_obj),
            clip_behavior="antiAlias",
            animate=300,
            ink=True,
            on_click=lambda _: on_select_match(match),
        )

        return card_container

    def update_results():
        results_list.controls.clear()

        if state.is_loading:
            results_list.controls.append(
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.ProgressRing(color=AppColors.PRIMARY),
                    padding=40,
                )
            )
        elif state.search_results:
            for i, match in enumerate(state.search_results):
                results_list.controls.append(build_match_card(match, i))
        elif state.search_query:
            results_list.controls.append(
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("No matches found", color=ft.Colors.ON_SURFACE_VARIANT),
                    padding=40,
                )
            )

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

    back_btn = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, color=ft.Colors.ON_SURFACE),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=lambda _: on_back(),
    )
    back_btn.tab_index = 0
    back_btn.on_focus = _on_focus_btn
    back_btn.on_blur = _on_blur_btn

    header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=16),
        content=ft.Row(
            controls=[
                back_btn,
                search_field,
            ],
            spacing=12,
        )
    )

    scroll_content = ft.Column(
        controls=[header, results_list],
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

    page_obj.refresh_search_results = update_results

    return ft.View(
        route="/search",
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
