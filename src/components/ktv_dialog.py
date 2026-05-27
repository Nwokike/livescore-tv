import flet as ft

from core.config import EXTERNAL_PLAYER_NAMES, KTV_PLAY_STORE_URL
from core.constants import LBL_INSTALL_PLAYER, LBL_INSTALL_PLAYER_DESC, LBL_NOT_NOW
from core.theme import AppTheme


def show_ktv_install_dialog(page: ft.Page):
    def open_store(e):
        page.run_task(page.launch_url, KTV_PLAY_STORE_URL)

    def dismiss(e):
        try:
            page.pop_dialog()
        except Exception:
            pass

    player_buttons = []
    for name in EXTERNAL_PLAYER_NAMES:
        player_buttons.append(
            ft.Button(
                content=ft.Text(name),
                icon=ft.Icons.PLAY_CIRCLE_ROUNDED,
                on_click=open_store,
                style=AppTheme.theme_button_style(is_primary=(name == "KTV Player")),
            )
        )

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(LBL_INSTALL_PLAYER, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                ft.Text(LBL_INSTALL_PLAYER_DESC, size=14),
                ft.Container(height=16),
                ft.Column(player_buttons, spacing=10),
            ],
            tight=True,
        ),
        actions=[
            ft.Button(content=ft.Text(LBL_NOT_NOW), on_click=dismiss),
            ft.Button(
                content=ft.Text("Download from Play Store"),
                on_click=open_store,
                style=AppTheme.theme_button_style(is_primary=True),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    page.show_dialog(dlg)
