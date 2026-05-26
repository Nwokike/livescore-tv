import flet as ft

from core.constants import LBL_LOADING
from core.theme import AppColors


def build_loading_indicator(size: int = 40, stroke_width: int = 4) -> ft.ProgressRing:
    return ft.ProgressRing(
        width=size,
        height=size,
        stroke_width=stroke_width,
        color=AppColors.PRIMARY,
    )


def build_loading_centered(message: str = LBL_LOADING) -> ft.Container:
    return ft.Container(
        height=200,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                build_loading_indicator(),
                ft.Container(height=16),
                ft.Text(message, color=ft.Colors.ON_SURFACE_VARIANT, size=14),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )


def build_empty_state(message: str, icon: ft.Icons = ft.Icons.INFO_OUTLINE_ROUNDED, size: int = 16) -> ft.Container:
    return ft.Container(
        height=200,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                ft.Icon(icon, size=48, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(height=8),
                ft.Text(message, color=ft.Colors.ON_SURFACE_VARIANT, size=size, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )


def build_error_state(message: str, on_retry=None) -> ft.Container:
    controls = [
        ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=48, color=AppColors.ERROR),
        ft.Container(height=8),
        ft.Text(message, color=ft.Colors.ON_SURFACE_VARIANT, size=14, text_align=ft.TextAlign.CENTER),
    ]
    if on_retry:
        controls.append(ft.Container(height=16))
        controls.append(
            ft.ElevatedButton(
                text="Retry",
                icon=ft.Icons.REFRESH_ROUNDED,
                on_click=on_retry,
                bgcolor=AppColors.PRIMARY,
                color=ft.Colors.WHITE,
            )
        )
    return ft.Container(
        height=200,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )
