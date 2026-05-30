import flet as ft

from components.channel_card import build_channel_card
from components.loading_state import build_empty_state, build_loading_centered
from core.constants import LBL_AVAILABLE_STREAMS, LBL_NO_STREAMS
from core.state import Match, state
from core.theme import AppColors


def _status_badge(status: str, time: str) -> ft.Container:
    is_live = status in ("LIVE", "1H", "2H", "HT")
    color = AppColors.LIVE if is_live else AppColors.PRIMARY
    label = "LIVE" if is_live else (time if time else "TBD")

    if is_live:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=8,
                        height=8,
                        border_radius=4,
                        bgcolor=ft.Colors.WHITE,
                        animate_scale=500,
                    ),
                    ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                spacing=6,
                tight=True,
            ),
            padding=ft.Padding(14, 7, 14, 7),
            bgcolor=color,
            border_radius=8,
        )
    return ft.Container(
        content=ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        padding=ft.Padding(14, 7, 14, 7),
        bgcolor=color,
        border_radius=8,
    )


def build_match_detail_view(
    page_obj: ft.Page,
    match: Match,
    controller,
    on_back,
) -> ft.View:

    is_live = match.status in ("LIVE", "1H", "2H", "HT")
    surface_variant = AppColors.get_surface_variant(page_obj)

    channels_list = ft.Column(spacing=10)

    def update_channels():
        if state.is_loading:
            scroll_content.controls = [
                header,
                channels_header,
                build_loading_centered("Loading streams..."),
            ]
        elif state.error_message:
            scroll_content.controls = [
                header,
                channels_header,
                build_empty_state(state.error_message, icon=ft.Icons.ERROR_OUTLINE_ROUNDED),
            ]
        elif state.match_channels:
            channels_list.controls.clear()
            for i, ch in enumerate(state.match_channels):
                status_dot = ft.Container(
                    width=8,
                    height=8,
                    border_radius=4,
                    bgcolor="#6B7280",
                )
                channels_list.controls.append(
                    build_channel_card(ch, controller.play_stream, page_obj, i, surface_variant, status_dot)
                )
                page_obj.run_task(controller.check_channel_liveliness, ch, status_dot)
            scroll_content.controls = [header, channels_header, channels_list]
        else:
            scroll_content.controls = [
                header,
                channels_header,
                build_empty_state(LBL_NO_STREAMS, icon=ft.Icons.STREAM_ROUNDED),
            ]

        page_obj.update()

    back_btn = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, color=ft.Colors.ON_SURFACE),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=lambda _: on_back(),
        tooltip="Back",
    )
    back_btn.tab_index = 0

    score_text = ""
    if is_live and (match.home_score or match.away_score):
        score_text = f"{match.home_score} - {match.away_score}"
    elif match.status == "FT":
        score_text = f"{match.home_score} - {match.away_score}"

    home_logo_control = (
        ft.Image(src=match.home_logo, width=64, height=64, fit="contain")
        if match.home_logo
        else ft.Icon(ft.Icons.SHIELD_ROUNDED, size=64, color=ft.Colors.ON_SURFACE_VARIANT)
    )
    away_logo_control = (
        ft.Image(src=match.away_logo, width=64, height=64, fit="contain")
        if match.away_logo
        else ft.Icon(ft.Icons.SHIELD_ROUNDED, size=64, color=ft.Colors.ON_SURFACE_VARIANT)
    )

    dashboard_row = ft.Row(
        controls=[
            # Home Team Column
            ft.Column(
                controls=[
                    home_logo_control,
                    ft.Container(height=8),
                    ft.Text(
                        match.home_team,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
            ),
            # Score Column
            ft.Column(
                controls=[
                    _status_badge(match.status, match.time),
                    ft.Container(height=12),
                    ft.Text(
                        score_text if score_text else "vs",
                        size=32,
                        weight=ft.FontWeight.W_800,
                        color=AppColors.PRIMARY if is_live else ft.Colors.ON_SURFACE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                width=120,
            ),
            # Away Team Column
            ft.Column(
                controls=[
                    away_logo_control,
                    ft.Container(height=8),
                    ft.Text(
                        match.away_team,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    header = ft.Container(
        padding=ft.Padding.only(left=20, right=20, top=20, bottom=24),
        content=ft.Column(
            controls=[
                ft.Row(controls=[back_btn]),
                ft.Container(height=20),
                dashboard_row,
                ft.Container(height=16),
                ft.Text(match.league, size=13, color=ft.Colors.ON_SURFACE_VARIANT, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
    )

    channels_header = ft.Container(
        padding=ft.Padding.only(left=20, right=20, top=16, bottom=12),
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.STREAM_ROUNDED, color=AppColors.PRIMARY, size=18),
                    padding=8,
                    bgcolor=ft.Colors.with_opacity(0.08, AppColors.PRIMARY),
                    border_radius=8,
                ),
                ft.Text(
                    LBL_AVAILABLE_STREAMS,
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE,
                ),
            ],
            spacing=10,
        ),
    )

    scroll_content = ft.Column(
        controls=[header, channels_header],
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

    state.on_channels_loaded = update_channels
    page_obj.update_channels_list = update_channels

    update_channels()

    return ft.View(
        route="/match",
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
