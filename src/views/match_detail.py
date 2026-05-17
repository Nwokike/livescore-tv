import flet as ft

from components.channel_card import build_channel_card
from components.loading_state import build_empty_state, build_loading_centered
from core.constants import LBL_AVAILABLE_STREAMS, LBL_NO_STREAMS
from core.focus_manager import make_focusable_button
from core.state import Match, state
from core.theme import AppColors


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
        channels_list.controls.clear()

        if state.is_loading:
            channels_list.controls.append(build_loading_centered("Loading streams..."))
        elif state.error_message:
            channels_list.controls.append(build_empty_state(state.error_message, icon=ft.Icons.ERROR_OUTLINE_ROUNDED))
        elif state.match_channels:
            for i, ch in enumerate(state.match_channels):
                channels_list.controls.append(
                    build_channel_card(ch, controller.play_stream, page_obj, i, surface_variant)
                )
        else:
            channels_list.controls.append(build_empty_state(LBL_NO_STREAMS, icon=ft.Icons.STREAM_ROUNDED))

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
    make_focusable_button(back_btn)

    score_text = ""
    if is_live and (match.home_score or match.away_score):
        score_text = f"{match.home_score} - {match.away_score}"

    status_badge = ft.Container(
        content=ft.Text(
            "LIVE" if is_live else match.time,
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        ),
        padding=ft.Padding(12, 6, 12, 6),
        bgcolor=AppColors.LIVE if is_live else AppColors.PRIMARY,
        border_radius=8,
    )

    header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=24),
        content=ft.Column(
            controls=[
                ft.Row(controls=[back_btn]),
                ft.Container(height=16),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=status_badge,
                ),
                ft.Container(height=16),
                ft.Text(match.home_team, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, text_align=ft.TextAlign.CENTER),
                ft.Text(score_text, size=28, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY if is_live else ft.Colors.ON_SURFACE, text_align=ft.TextAlign.CENTER),
                ft.Text(match.away_team, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.Text(match.league, size=14, color=ft.Colors.ON_SURFACE_VARIANT, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )
    )

    channels_header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=16, bottom=8),
        content=ft.Row(
            [
                ft.Icon(ft.Icons.STREAM_ROUNDED, color=AppColors.PRIMARY, size=20),
                ft.Text(
                    LBL_AVAILABLE_STREAMS,
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ON_SURFACE,
                ),
            ],
            spacing=8,
        ),
    )

    scroll_content = ft.Column(
        controls=[header, channels_header, channels_list],
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
