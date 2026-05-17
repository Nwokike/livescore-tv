# ⚽ Score808 TV

<div align="center">

**Live football for everyone**

Lightweight client-side Android TV / mobile / desktop app for watching live football matches. Zero server. Built with Python and Flet.

</div>

<div align="center">

[![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/user/score808-tv/releases)
[![Android](https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://github.com/user/score808-tv/releases)
[![Built with Flet 0.85](https://img.shields.io/badge/Built%20with-Flet%200.85-00B0FF?style=for-the-badge)](https://flet.dev)

</div>

---

## 📥 Downloads

| Platform | Download | Status |
|----------|----------|--------|
| Windows | [Installer (.exe)](https://github.com/user/score808-tv/releases) | Ready |
| Android (Universal) | [APK](https://github.com/user/score808-tv/releases) | Ready |
| Android (ARM64) | [APK](https://github.com/user/score808-tv/releases) | Ready |
| macOS | — | *Coming soon* |
| iOS | — | *Coming soon* |

---

## ✨ Features

- **Live Football** — Today's matches from major leagues worldwide
- **Real-Time Scores** — Live match scores and status updates
- **Multi-Stream Support** — Multiple stream sources per match
- **Clean Interface** — Ad-free, distraction-free viewing
- **Dark/Light Mode** — System theme awareness with manual override
- **TV Remote Navigation** — Full D-pad support for Android TV and Fire Stick
- **No Server Required** — Fully client-side, zero infrastructure
- **Offline Resilient** — Local caching with graceful error handling

---

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | Flet 0.85 (Python → Flutter) |
| Video Engine | `flet-video` (libmpv backend) |
| Network | `httpx` (async, connection pooling, retry logic) |
| Cache | `aiosqlite` (WAL-mode SQLite with TTL) + in-memory LRU |
| Stream Resolver | HTML scraper with regex m3u8 extraction |
| Match Data | Livescore.com public API |
| State Management | Flet `@observable` reactive state |
| Routing | Flet declarative routing with view stack |
| Navigation | Sequential `tab_index` D-pad focus chain |

### Project Structure

```
src/
├── main.py                 # App entry, routing, global back handler
├── core/
│   ├── config.py           # Feature flags (internal/external player)
│   ├── constants.py        # App labels, timeouts, cache TTLs
│   ├── controller.py       # AppController: routing, state, rate limiting
│   ├── errors.py           # Custom exception types
│   ├── focus_manager.py    # D-pad/keyboard event handling for TV remotes
│   ├── state.py            # @observable reactive state (AppState)
│   └── theme.py            # Light/dark color schemes, theme helpers
├── views/
│   ├── splash.py           # Animated splash with auto-transition
│   ├── home.py             # Match list grouped by league, refresh, search
│   ├── search.py           # Search bar with debounce + results
│   ├── match_detail.py     # Match info + stream channel list
│   └── player.py           # flet-video player with loading overlay
├── services/
│   ├── cache.py            # Async SQLite cache with TTL + LRU memory cache
│   ├── livescore.py        # Livescore API client with retry logic
│   └── score808.py         # HTML scraper for stream URL resolution
└── components/
    ├── channel_card.py     # Stream channel list item
    ├── ktv_dialog.py       # External player install dialog
    ├── loading_state.py    # Loading/empty/error state builders
    └── match_card.py       # Match list item card
```

### Stream Resolution Pipeline

```
User selects match
    │
    ▼
controller.load_streams(match)
    │
    ├── Check cache (TTL: 60s)
    │
    ├── scraper.find_match_page_by_id(match_id)
    │       └── fallback: scraper.find_match_page(home, away)
    │
    ├── scraper.get_streams_from_match_page(url)
    │       └── Parse <a> and <iframe> for stream links
    │
    └── User clicks stream
            │
            ▼
        controller.play_stream(channel)
            │
            ├── scraper.resolve_stream_url(channel_url)
            │       └── regex: extract .m3u8 or iframe URL
            │
            └── Navigate to /play → flet-video loads stream
```

### D-Pad Navigation Model

Every interactive element has a sequential `tab_index` for Android TV FocusFinder:

```
Home:    Refresh(1) → Search(2) → Theme(3) → Cards(4..N)
Search:  Back(0) → SearchBtn(1) → Cards(2..N)
Match:   Back(0) → Streams(10..N)
Player:  Back(1)
```

Focus highlights animate scale, shadow, and border via `on_focus`/`on_blur` callbacks.

---

## 🛠️ Development

```bash
# Clone and set up
git clone https://github.com/user/score808-tv.git
cd score808-tv
uv sync

# Run in development
uv run flet run src

# Lint
uv run ruff check src/

# Build for Android
uv run flet build apk --release

# Build for Windows
uv run flet build windows --release
```

---

## 📄 License

MIT

---

## Legal Disclaimer

Score808 TV is a media player and network utility. It does not host, store, or distribute any copyrighted content. The app interfaces with publicly available APIs and web pages. Users are solely responsible for ensuring compliance with applicable laws and terms of service in their jurisdiction.
