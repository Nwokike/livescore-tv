import logging
import sys

import flet as ft

from core.controller import AppController
from core.focus_manager import FocusManager
from services.cache import Cache
from services.livescore import LivescoreAPI
from services.score808 import Score808Scraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("score808.main")


async def main(page: ft.Page):
    controller = AppController(page, LivescoreAPI(), Score808Scraper(), Cache())
    await controller.init()

    focus_manager = FocusManager(page)
    focus_manager.set_back_handler(controller.handle_global_back)

    page.on_route_change = controller.route_change
    page.on_view_pop = controller.view_pop

    async def on_unload(e):
        await controller.cleanup()

    page.on_unload = on_unload

    await controller.route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
