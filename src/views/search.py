import asyncio

import flet as ft

from components.loading_state import build_empty_state, build_loading_centered
from components.match_card import build_match_card
from core.constants import LBL_NO_RESULTS, LBL_SEARCH_HINT, MAX_SEARCH_QUERY_LENGTH, SEARCH_DEBOUNCE_SEC
from core.focus_manager import make_focusable_button
from core.state import state
from core.theme import AppColors


def build_search_view(
    page_obj: ft.Page,
    controller,
    on_select_match,
    on_back,
) -> ft.View:

    _debounce_task: asyncio.Task | None = None
    surface_variant = AppColors.get_surface_variant(page_obj)

    def _cancel_debounce():
        nonlocal _debounce_task
        if _debounce_task and not _debounce_task.done():
            _debounce_task.cancel()

    def _do_search(query: str):
        _cancel_debounce()
        if not query or state.is_loading:
            return
        if len(query) > MAX_SEARCH_QUERY_LENGTH:
            query = query[:MAX_SEARCH_QUERY_LENGTH]
        search_btn.disabled = True
        search_spinner.visible = True
        page_obj.update()
        page_obj.run_task(controller.load_search, query)

    def on_search_change(e):
        nonlocal _debounce_task
        query = e.control.value.strip() if e.control.value else ""
        if not query:
            state.search_results = []
            state.search_query = ""
            update_results()
            return
        if len(query) > MAX_SEARCH_QUERY_LENGTH:
            e.control.value = query[:MAX_SEARCH_QUERY_LENGTH]
            query = query[:MAX_SEARCH_QUERY_LENGTH]
        _cancel_debounce()
        _debounce_task = asyncio.create_task(_delayed_search(query))

    async def _delayed_search(query: str):
        try:
            await asyncio.sleep(SEARCH_DEBOUNCE_SEC)
            if query and not state.is_loading:
                page_obj.run_task(controller.load_search, query)
        except asyncio.CancelledError:
            pass

    search_field = ft.TextField(
        hint_text=LBL_SEARCH_HINT,
        border=ft.InputBorder.OUTLINE,
        border_radius=12,
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        on_submit=lambda e: _do_search(e.control.value.strip()),
        on_change=lambda e: on_search_change(e),
        autofocus=True,
        expand=True,
    )

    results_list = ft.Column(spacing=12)

    def update_results():
        results_list.controls.clear()
        search_btn.disabled = False
        search_spinner.visible = False

        if state.is_loading:
            results_list.controls.append(build_loading_centered("Searching..."))
        elif state.search_results:
            for i, match in enumerate(state.search_results):
                results_list.controls.append(
                    build_match_card(match, on_select_match, page_obj, i, surface_variant)
                )
        elif state.search_query:
            results_list.controls.append(build_empty_state(LBL_NO_RESULTS, icon=ft.Icons.SEARCH_OFF_ROUNDED))

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

    search_btn = ft.Container(
        content=ft.Icon(ft.Icons.SEARCH_ROUNDED, color=AppColors.PRIMARY),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=lambda _: _do_search(search_field.value),
    )
    search_btn.tab_index = 1
    make_focusable_button(search_btn)

    search_spinner = ft.ProgressRing(
        color=AppColors.PRIMARY, stroke_width=3, width=20, height=20, visible=False
    )

    header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=16),
        content=ft.Column(
            [
                ft.Row(
                    [
                        back_btn,
                        ft.Container(
                            width=36,
                            height=36,
                            border_radius=10,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Image(
                                src="icon.png",
                                width=24,
                                height=24,
                                fit="contain",
                            ),
                        ),
                        ft.Text("Search", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ],
                    spacing=12,
                ),
                ft.Container(height=8),
                ft.Row(
                    [search_field, search_btn, search_spinner],
                    spacing=8,
                ),
            ],
            spacing=0,
        )
    )

    scroll_content = ft.Column(
        controls=[header, results_list],
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

    state.on_search_refreshed = update_results

    return ft.View(
        route="/search",
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
