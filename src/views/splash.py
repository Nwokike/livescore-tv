import flet as ft

from core.constants import APP_NAME, LBL_SPLASH_TAGLINE
from core.theme import AppColors


def build_splash_view() -> ft.View:
    return ft.View(
        route="/",
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.SURFACE,
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Image(
                                src="icon.png",
                                width=96,
                                height=96,
                                border_radius=22,
                                fit="contain",
                            ),
                            bgcolor=ft.Colors.with_opacity(0.04, AppColors.PRIMARY),
                            padding=20,
                            border_radius=28,
                        ),
                        ft.Container(height=24),
                        ft.Text(
                            APP_NAME,
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            LBL_SPLASH_TAGLINE,
                            size=13,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=32),
                        ft.ProgressRing(
                            width=22,
                            height=22,
                            stroke_width=3,
                            color=AppColors.PRIMARY,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
            )
        ],
        padding=0,
    )
