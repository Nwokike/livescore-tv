import flet as ft

from core.constants import LBL_LOADING_STREAM, LBL_PLAYBACK_ENDED, LBL_PLAYBACK_ERROR, LBL_STREAM_FAILED
from core.state import state
from core.theme import AppColors


def build_player_view(
    page_obj: ft.Page,
    stream_url: str,
    on_back,
) -> ft.View:

    import flet_video as fv

    video = fv.Video(
        autoplay=True,
        expand=True,
        show_controls=True,
        wakelock=True,
        filter_quality=ft.FilterQuality.MEDIUM,
        pause_upon_entering_background_mode=True,
        resume_upon_entering_foreground_mode=True,
        on_error=lambda e: _on_error(e, page_obj),
        on_complete=lambda e: _on_ended(page_obj),
    )

    status_text = ft.Text(
        LBL_LOADING_STREAM,
        size=16,
        color=ft.Colors.WHITE,
        weight=ft.FontWeight.W_500,
        text_align=ft.TextAlign.CENTER,
    )

    loading = ft.ProgressRing(width=40, height=40, stroke_width=4, color=AppColors.PRIMARY)

    overlay = ft.Container(
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.BLACK),
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

    def on_back_click(e):
        if len(page_obj.views) > 1:
            for control in page_obj.views[-1].controls:
                if hasattr(control, "pause"):
                    try:
                        control.pause()
                    except Exception:
                        pass
            state.reset_player()
            page_obj.views.pop()
            page_obj.update()

    back_btn = ft.Container(
        left=24,
        top=40,
        content=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color=ft.Colors.WHITE,
            icon_size=24,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            on_click=on_back_click,
            tooltip="Back",
        ),
    )
    back_btn.tab_index = 1

    async def load_stream():
        try:
            video.playlist = [fv.VideoMedia(stream_url)]
            video.autoplay = True
            overlay.visible = False
            page_obj.update()
        except Exception:
            status_text.value = LBL_STREAM_FAILED
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
            ft.Text(LBL_PLAYBACK_ERROR, color=ft.Colors.WHITE),
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
            ft.Text(LBL_PLAYBACK_ENDED, color=ft.Colors.WHITE),
            bgcolor=AppColors.SUCCESS,
            duration=3000,
        )
        page_obj.snack_bar.open = True
        page_obj.update()
    except Exception:
        pass
