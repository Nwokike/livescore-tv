import flet as ft
import flet_video as fv
from core.theme import AppColors
from core.state import state


def build_player_view(
    page_obj: ft.Page,
    stream_url: str,
    on_back,
) -> ft.View:

    video = fv.Video(
        autoplay=True,
        expand=True,
        aspect_ratio=16 / 9,
        show_controls=True,
        wakelock=True,
        filter_quality=ft.FilterQuality.HIGH,
        pause_upon_entering_background_mode=True,
        resume_upon_entering_foreground_mode=True,
        on_error=lambda e: _on_error(e, page_obj),
        on_complete=lambda e: _on_ended(page_obj),
    )

    status_text = ft.Text(
        "Loading Stream...",
        size=16,
        color=ft.Colors.WHITE,
        weight=ft.FontWeight.W_500,
        text_align=ft.TextAlign.CENTER,
    )

    loading = ft.ProgressRing(width=40, height=40, stroke_width=4, color=AppColors.PRIMARY)

    overlay = ft.Container(
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                loading,
                ft.Container(height=24),
                status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )

    def _on_focus_btn(e):
        e.control.bgcolor = ft.Colors.with_opacity(0.5, ft.Colors.BLACK)
        try:
            e.control.update()
        except Exception:
            pass

    def _on_blur_btn(e):
        e.control.bgcolor = ft.Colors.with_opacity(0.3, ft.Colors.BLACK)
        try:
            e.control.update()
        except Exception:
            pass

    back_btn = ft.Container(
        left=24,
        top=40,
        content=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color=ft.Colors.WHITE,
            icon_size=24,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            on_click=lambda _: on_back(),
            tooltip="Back",
        ),
    )
    back_btn.tab_index = 1
    back_btn.on_focus = _on_focus_btn
    back_btn.on_blur = _on_blur_btn

    async def load_stream():
        try:
            video.playlist = [fv.VideoMedia(stream_url)]
            video.autoplay = True
            overlay.visible = False
            page_obj.update()
        except Exception:
            status_text.value = "Failed to load stream"
            loading.visible = False
            page_obj.update()

    view = ft.View(
        route="/play",
        controls=[
            ft.Stack(
                [
                    ft.Container(expand=True, bgcolor=ft.Colors.BLACK),
                    video,
                    overlay,
                    back_btn,
                ],
                expand=True,
            ),
        ],
        padding=0,
    )

    page_obj.run_task(load_stream)

    return view


def _on_error(e, page_obj: ft.Page):
    state.player_error = e.data
    try:
        page_obj.snack_bar = ft.SnackBar(
            ft.Text("Playback error", color=ft.Colors.WHITE),
            bgcolor=AppColors.ERROR,
            duration=3000,
        )
        page_obj.snack_bar.open = True
        page_obj.update()
    except Exception:
        pass


def _on_ended(page_obj: ft.Page):
    try:
        page_obj.snack_bar = ft.SnackBar(
            ft.Text("Playback ended", color=ft.Colors.WHITE),
            bgcolor=AppColors.SUCCESS,
            duration=3000,
        )
        page_obj.snack_bar.open = True
        page_obj.update()
    except Exception:
        pass
