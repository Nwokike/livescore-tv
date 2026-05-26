import datetime
from dataclasses import dataclass

import flet as ft


@dataclass
class Match:
    id: str
    home_team: str
    away_team: str
    league: str
    time: str
    status: str
    home_score: str = ""
    away_score: str = ""
    poster: str = ""
    home_logo: str = ""
    away_logo: str = ""


@dataclass
class StreamChannel:
    name: str
    url: str
    quality: str = ""


@ft.observable
class AppState:
    is_loading: bool = False
    search_query: str = ""
    selected_date: str = datetime.date.today().strftime("%Y-%m-%d")
    matches_by_league: list[dict] = []
    search_results: list[Match] = []
    selected_match: Match | None = None
    match_channels: list[StreamChannel] = []
    stream_url: str | None = None
    player_error: str | None = None
    search_has_more: bool = True
    error_message: str | None = None

    def reset_player(self):
        self.stream_url = None
        self.player_error = None
        self.match_channels = []

    def reset_search(self):
        self.search_query = ""
        self.search_results = []
        self.search_has_more = True


state = AppState()
