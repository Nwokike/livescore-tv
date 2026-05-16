import flet as ft
from core.state import state, Match, StreamChannel
from core.theme import AppColors


def build_match_detail_view(
    page_obj: ft.Page,
    match: Match,
    on_load_streams,
    on_play_stream,
    on_back,
) -> ft.View:

    is_live = match.status in ("LIVE", "1H", "2H", "HT")

    channels_list = ft.Column(spacing=10)

    def build_channel_card(channel: StreamChannel, idx: int):
        card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINED, color=AppColors.PRIMARY, size=28),
                    ft.Column(
                        controls=[
                            ft.Text(channel.name, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                            ft.Text(channel.quality or "HD Stream", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=2,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=16,
            border_radius=12,
            bgcolor=AppColors.get_surface_variant(page_obj),
            animate=300,
            ink=True,
            on_click=lambda _: on_play_stream(channel),
        )
        card.tab_index = idx + 10
        card.on_focus = lambda e: _on_focus_card(e, card)
        card.on_blur = lambda e: _on_blur_card(e, card)
        return card

    def _on_focus_card(e, ctrl):
        ctrl.scale = 1.02
        ctrl.border = ft.Border.all(2, AppColors.PRIMARY)
        try:
            ctrl.update()
        except Exception:
            pass

    def _on_blur_card(e, ctrl):
        ctrl.scale = 1.0
        ctrl.border = ft.Border.all(0, ft.Colors.TRANSPARENT)
        try:
            ctrl.update()
        except Exception:
            pass

    def update_channels():
        channels_list.controls.clear()

        if state.is_loading:
            channels_list.controls.append(
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.ProgressRing(color=AppColors.PRIMARY),
                    padding=40,
                )
            )
        elif state.match_channels:
            for i, ch in enumerate(state.match_channels):
                channels_list.controls.append(build_channel_card(ch, i))
        else:
            channels_list.controls.append(
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("No streams available", color=ft.Colors.ON_SURFACE_VARIANT),
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

    score_text = ""
    if is_live and (match.home_score or match.away_score):
        score_text = f"{match.home_score} - {match.away_score}"

    header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=24),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[back_btn],
                ),
                ft.Container(height=16),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.Container(
                        content=ft.Text(
                            "LIVE" if is_live else match.time,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        padding=ft.Padding(12, 6, 12, 6),
                        bgcolor=AppColors.LIVE if is_live else AppColors.PRIMARY,
                        border_radius=8,
                    ),
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
        content=ft.Text(
            "Available Streams",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ON_SURFACE,
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

    page_obj.update_channels_list = update_channels

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
