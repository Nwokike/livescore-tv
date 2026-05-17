import flet as ft

from core.constants import CARD_HEIGHT
from core.focus_manager import make_focusable_card
from core.state import Match
from core.theme import AppColors


def build_match_card(
    match: Match,
    on_click,
    page_obj: ft.Page,
    idx: int = 0,
    surface_variant: str | None = None,
) -> ft.Container:
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
                ft.Row(
                    [time_badge, ft.Text(match.league, size=12, color=ft.Colors.ON_SURFACE_VARIANT)],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
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
        bgcolor=surface_variant or AppColors.get_surface_variant(page_obj),
        clip_behavior="antiAlias",
        animate_scale=300,
        animate=300,
        ink=True,
        height=CARD_HEIGHT,
        key=f"match_{match.id}_{idx}",
        on_click=lambda _: on_click(match),
        tooltip=f"{match.home_team} vs {match.away_team}",
    )
    card_container.tab_index = idx + 3
    make_focusable_card(card_container)

    return card_container
