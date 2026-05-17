import flet as ft

from core.theme import AppColors

PRIMARY_COLOR = AppColors.PRIMARY


class FocusManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self._back_handler = None
        page.on_keyboard_event = self._handle_keyboard

    def set_back_handler(self, handler: callable):
        self._back_handler = handler

    def _handle_keyboard(self, e: ft.KeyboardEvent):
        if e.key in ("Escape", "Go Back", "Browser Back", "Backspace"):
            if self._back_handler:
                self._back_handler()

    @staticmethod
    def apply_focus(control: ft.Container, focused: bool, style: str = "card"):
        if style == "card":
            if focused:
                control.scale = 1.05
                control.border = ft.Border.all(2.5, PRIMARY_COLOR)
                control.shadow = ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.2, PRIMARY_COLOR),
                    offset=ft.Offset(0, 4),
                )
            else:
                control.scale = 1.0
                control.border = ft.Border.all(0, ft.Colors.TRANSPARENT)
                control.shadow = None
        elif style == "btn":
            control.bgcolor = ft.Colors.with_opacity(0.1, PRIMARY_COLOR) if focused else None
        elif style == "border":
            if focused:
                control.bgcolor = ft.Colors.with_opacity(0.1, PRIMARY_COLOR)
                control.border = ft.Border.all(2, PRIMARY_COLOR)
            else:
                control.bgcolor = None
                control.border = ft.Border.all(1.5, PRIMARY_COLOR)
        try:
            control.update()
        except Exception:
            pass


def make_focusable_card(control: ft.Container):
    control.on_focus = lambda e: FocusManager.apply_focus(e.control, True, "card")
    control.on_blur = lambda e: FocusManager.apply_focus(e.control, False, "card")


def make_focusable_button(control: ft.Container):
    control.on_focus = lambda e: FocusManager.apply_focus(e.control, True, "btn")
    control.on_blur = lambda e: FocusManager.apply_focus(e.control, False, "btn")


def make_focusable_border(control: ft.Container):
    control.on_focus = lambda e: FocusManager.apply_focus(e.control, True, "border")
    control.on_blur = lambda e: FocusManager.apply_focus(e.control, False, "border")
