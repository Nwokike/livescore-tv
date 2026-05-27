<p align="center">
  <img src="src/assets/icon.png" alt="Livescore TV" width="140" />
</p>

<h1 align="center">Livescore TV</h1>

<p align="center">
  A lightweight, responsive, and completely serverless desktop/Android application built with Python and Flet for watching live football matches directly from high-speed streaming CDNs.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Android-3DDC84?style=flat-square&logo=android&logoColor=white" alt="Android" />
  <img src="https://img.shields.io/badge/Built%20with-Flet%200.85-00B0FF?style=flat-square" alt="Built with Flet" />
</p>

---

## Download

Since we compile highly optimized standalone binaries target-specific to each processor architecture, Choose the highly optimized split APK for your device or the universal APK:

| Platform | Download | Notes |
|:--------:|:--------:|:------|
| 🤖 **Android (Universal)** | [**livescore_tv.apk**](https://github.com/Nwokike/livescore-tv/releases/latest/download/livescore_tv.apk) | Works on all Android devices (ARM64, ARMv7, x86_64) |
| 🤖 **Android (ARM64)** | [**livescore_tv-arm64-v8a.apk**](https://github.com/Nwokike/livescore-tv/releases/latest/download/livescore_tv-arm64-v8a.apk) | For modern 64-bit Android devices / Android TV |
| 🤖 **Android (ARM32)** | [**livescore_tv-armeabi-v7a.apk**](https://github.com/Nwokike/livescore-tv/releases/latest/download/livescore_tv-armeabi-v7a.apk) | For older 32-bit Android devices / TV Boxes |
| 🤖 **Android (x86_64)** | [**livescore_tv-x86_64.apk**](https://github.com/Nwokike/livescore-tv/releases/latest/download/livescore_tv-x86_64.apk) | For Android emulators / ChromeOS |

---

## Features

- **Redirection-Free Stream Resolution** — Parses homepage Nuxt state (`window.__NUXT__`) and resolves channels directly from Cloudflare-protected JSON APIs, bypassing edge redirection locks.
- **High-Speed CDN Playback** — Plays streams directly from high-performance edge streaming servers (`saten1`, `saten2`, `saten3`) with zero intermediary servers.
- **Failover Backup CDNs** — Automatically provides 3 backup stream hosts per broadcasting channel to ensure uninterrupted viewing.
- **Dynamic Liveliness Checker** — Spawns non-blocking async background workers to query stream URLs (`HEAD` / Range `GET`) and updates a live green/red status indicator dot next to each stream quality badge.
- **TV Remote Ready** — Full sequential D-pad focus routing and scaling highlights optimized for Android TV, Fire Stick, and remote controls.
- **Elegant Themes** — System-aware light/dark mode configuration utilizing Glassmorphism design and harmonized color systems.
- **Offline-First Cache** — SQLite async cache with WAL-mode and NORMAL sync configurations for instant matching, search queries, and stream lookup operations.

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | Flet 0.85 (Python → Flutter UI Engine) |
| Video | `flet-video` (libmpv HLS media engine) |
| Database | `aiosqlite` (async WAL-mode SQLite cache) |
| Network | `httpx` (async client, connection pooling, retries) |
| Scraper | nuxt state parser & direct detail API resolver |

---

## Development

Set up your local machine to build or run the application:

```bash
# Clone the repository
git clone https://github.com/Nwokike/livescore-tv.git
cd livescore-tv

# Install dev dependencies
uv sync

# Run the app locally
uv run flet run src

# Verify the test suite
uv run python -m unittest discover -s tests
```

---

## Legal Disclaimer

Livescore TV is a media player and network utility. It does not host, store, or distribute any copyrighted media streams. The application interfaces with publicly accessible APIs and web pages. Users are solely responsible for ensuring compliance with all local laws and terms of service regarding third-party broadcast resources.
