import flet as ft

from core.state import StreamChannel
from core.theme import AppColors


def _quality_badge(quality: str) -> ft.Container:
    color_map = {
        "4K": "#8B5CF6",
        "1080p": AppColors.PRIMARY,
        "720p": AppColors.SECONDARY,
        "480p": AppColors.WARNING,
        "360p": AppColors.DARK_TEXT_MUTED,
    }
    color = color_map.get(quality, AppColors.PRIMARY)
    return ft.Container(
        content=ft.Text(quality, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        padding=ft.Padding(6, 3, 6, 3),
        bgcolor=color,
        border_radius=4,
    )


def build_channel_card(
    channel: StreamChannel,
    on_click,
    page_obj: ft.Page,
    idx: int = 0,
    surface_variant: str | None = None,
    status_dot: ft.Container | None = None,
) -> ft.Container:
    quality = channel.quality or "HD"

    badge_row_controls = [_quality_badge(quality)]
    if status_dot:
        badge_row_controls.append(status_dot)
    badge_row_controls.append(ft.Text("Stream", size=11, color=ft.Colors.ON_SURFACE_VARIANT))

    card = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINED, color=AppColors.PRIMARY, size=24),
                    padding=8,
                    bgcolor=ft.Colors.with_opacity(0.08, AppColors.PRIMARY),
                    border_radius=10,
                ),
                ft.Container(width=12),
                ft.Column(
                    controls=[
                        ft.Text(channel.name, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                        ft.Row(
                            controls=badge_row_controls,
                            spacing=6,
                        ),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=ft.Colors.ON_SURFACE_VARIANT, size=16),
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.Padding(16, 12, 16, 12),
        border_radius=14,
        bgcolor=surface_variant or AppColors.get_surface_variant(page_obj),
        border=ft.Border.all(0.5, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)),
        animate_scale=300,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        ink=True,
        on_click=lambda _: page_obj.run_task(on_click, channel),
        tooltip=f"Play {channel.name}",
    )
    card.tab_index = idx + 10
    return card
