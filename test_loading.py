import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from services.cache import Cache
from services.livescore import LivescoreAPI
from core.controller import AppController, _restore_matches
from core.state import state

class FakePage:
    def __init__(self):
        self.title = ""
        self.padding = 0
        self.spacing = 0
        self.fonts = {}
        self.theme = None
        self.dark_theme = None
        self.theme_mode = None
        self.views = []
        self.route = "/home"
        self.update_calls = 0
        self.update_matches_list_called = 0

    def update(self):
        self.update_calls += 1

    def update_matches_list(self):
        self.update_matches_list_called += 1
        print(f"    [UI UPDATE] is_loading={state.is_loading}, leagues={len(state.matches_by_league)}")

async def test_loading_state():
    print("TEST: Loading state transitions correctly")
    print("=" * 50)

    livescore = LivescoreAPI()
    cache = Cache()
    page = FakePage()

    controller = AppController(page, livescore, None, cache)
    await controller.init()

    # First load - no cache
    print("\n--- First load (no cache) ---")
    print(f"  Before: is_loading={state.is_loading}, leagues={len(state.matches_by_league)}")
    await controller.load_matches()
    print(f"  After:  is_loading={state.is_loading}, leagues={len(state.matches_by_league)}")
    print(f"  UI updated: {page.update_matches_list_called} times")
    assert state.is_loading == False, f"is_loading should be False, got {state.is_loading}"
    assert len(state.matches_by_league) > 0, "Should have leagues"
    assert page.update_matches_list_called >= 2, "UI should have updated at least twice (loading + done)"
    print("  PASSED")

    # Second load - from cache
    print("\n--- Second load (from cache) ---")
    page.update_matches_list_called = 0
    state.is_loading = False
    state.matches_by_league = []
    await controller.load_matches()
    print(f"  After:  is_loading={state.is_loading}, leagues={len(state.matches_by_league)}")
    print(f"  UI updated: {page.update_matches_list_called} times")
    assert state.is_loading == False, f"is_loading should be False after cache hit, got {state.is_loading}"
    assert len(state.matches_by_league) > 0, "Should have leagues from cache"
    print("  PASSED")

    await controller.cleanup()

    print("\n" + "=" * 50)
    print("ALL LOADING STATE TESTS PASSED")
    print("=" * 50)

asyncio.run(test_loading_state())
