import flet as ft

from core.constants import CARD_HEIGHT
from core.focus_manager import make_focusable_card
from core.state import Match
from core.theme import AppColors


def _status_icon(status: str) -> tuple[str, str]:
    if status in ("LIVE", "1H", "2H"):
        return ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED, AppColors.LIVE
    if status == "HT":
        return ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED, AppColors.WARNING
    if status == "FT":
        return ft.Icons.CHECK_CIRCLE_ROUNDED, AppColors.DARK_TEXT_MUTED
    return ft.Icons.SCHEDULE_ROUNDED, AppColors.PRIMARY


def _format_score(home: str, away: str) -> str:
    h = home.strip() or "0"
    a = away.strip() or "0"
    return f"{h} - {a}"


def build_match_card(
    match: Match,
    on_click,
    page_obj: ft.Page,
    idx: int = 0,
    surface_variant: str | None = None,
) -> ft.Container:
    is_live = match.status in ("LIVE", "1H", "2H", "HT")
    icon, icon_color = _status_icon(match.status)

    score_display = ""
    if is_live and (match.home_score or match.away_score):
        score_display = _format_score(match.home_score, match.away_score)
    elif not is_live and match.status == "FT":
        score_display = _format_score(match.home_score, match.away_score)

    time_display = match.time if match.time else "TBD"

    left_badge = ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, color=icon_color, size=14),
                ft.Text(
                    "LIVE" if is_live else time_display,
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=icon_color,
                ),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.Padding(8, 4, 8, 4),
        bgcolor=ft.Colors.with_opacity(0.1, icon_color),
        border_radius=6,
    )

    home_logo = (
        ft.Image(src=match.home_logo, width=20, height=20, fit="contain")
        if match.home_logo
        else ft.Icon(ft.Icons.SHIELD_ROUNDED, size=20, color=ft.Colors.ON_SURFACE_VARIANT)
    )
    away_logo = (
        ft.Image(src=match.away_logo, width=20, height=20, fit="contain")
        if match.away_logo
        else ft.Icon(ft.Icons.SHIELD_ROUNDED, size=20, color=ft.Colors.ON_SURFACE_VARIANT)
    )

    teams_row = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Row(
                        [
                            home_logo,
                            ft.Text(match.home_team, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                        ],
                        spacing=8,
                        tight=True,
                    ),
                    ft.Row(
                        [
                            away_logo,
                            ft.Text(match.away_team, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                        ],
                        spacing=8,
                        tight=True,
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(width=12),
            ft.Column(
                controls=[
                    ft.Text(
                        score_display if score_display else "vs",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PRIMARY if is_live else ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        match.league,
                        size=10,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    card_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([left_badge], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=8),
                teams_row,
            ],
            spacing=0,
        ),
        padding=ft.Padding(16, 12, 16, 12),
        border_radius=14,
        bgcolor=surface_variant or AppColors.get_surface_variant(page_obj),
        border=ft.Border.all(0.5, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)),
        clip_behavior="antiAlias",
        animate_scale=300,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        ink=True,
        height=CARD_HEIGHT,
        key=f"match_{match.id}_{idx}",
        on_click=lambda _: on_click(match),
        tooltip=f"{match.home_team} vs {match.away_team}",
    )
    card_container.tab_index = idx + 3
    make_focusable_card(card_container)

    return card_container
