import flet as ft
from dataclasses import dataclass


@dataclass
class Match:
    id: str
    home_team: str
    away_team: str
    league: str
    time: str
    status: str  # "NS" (not started), "LIVE", "FT", etc.
    home_score: str = ""
    away_score: str = ""
    poster: str = ""


@dataclass
class StreamChannel:
    name: str
    url: str
    quality: str = ""


@dataclass
class MatchWithStreams:
    match: Match
    channels: list[StreamChannel]


@ft.observable
class AppState:
    is_loading: bool = False
    search_query: str = ""
    matches_by_league: list[dict] = []  # [{"league": str, "matches": [Match]}]
    search_results: list[Match] = []
    selected_match: Match | None = None
    match_channels: list[StreamChannel] = []
    stream_url: str | None = None
    player_error: str | None = None
    search_has_more: bool = True

    def __init__(self):
        self.matches_by_league = []
        self.search_results = []
        self.match_channels = []


state = AppState()
