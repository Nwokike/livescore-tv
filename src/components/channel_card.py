import flet as ft

from core.focus_manager import make_focusable_card
from core.state import StreamChannel
from core.theme import AppColors


def build_channel_card(
    channel: StreamChannel,
    on_click,
    page_obj: ft.Page,
    idx: int = 0,
    surface_variant: str | None = None,
) -> ft.Container:
    quality_label = channel.quality or "HD"

    card = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINED, color=AppColors.PRIMARY, size=28),
                    padding=4,
                ),
                ft.Column(
                    controls=[
                        ft.Text(channel.name, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(quality_label, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    padding=ft.Padding(6, 2, 6, 2),
                                    bgcolor=AppColors.PRIMARY,
                                    border_radius=4,
                                ),
                                ft.Text("Stream", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                            ],
                            spacing=6,
                        ),
                    ],
                    spacing=4,
                ),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=ft.Colors.ON_SURFACE_VARIANT, size=18),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=16,
        border_radius=12,
        bgcolor=surface_variant or AppColors.get_surface_variant(page_obj),
        animate_scale=300,
        animate=300,
        ink=True,
        on_click=lambda _: on_click(channel),
        tooltip=f"Play {channel.name}",
    )
    card.tab_index = idx + 10
    make_focusable_card(card)
    return card
