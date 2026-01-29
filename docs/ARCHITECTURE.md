# MusicBox Architecture

## Diagram (high level)

```
[Mobile Browser]
      |
      |  HTTPS (LAN)
      v
+---------------------+        +------------------+
|  Flask Web App      |<-----> |  SQLite Storage  |
|  - UI (Jinja)       |        |  tracks/playlists|
|  - REST API         |        |  downloads/cache |
|  - SSE events       |        +------------------+
|  - Auth (optional)  |
+----------+----------+
           |
           | internal service calls
           v
+---------------------+        +--------------------------+
|  player_engine      |<------>| download_manager         |
|  (VLC / mpg123)     |        |  queue + caching         |
+----------+----------+        +--------------------------+
           |
           v
   Audio Output (ALSA / HDMI / 3.5mm / USB DAC / BT)
```

## Stack choice
- **Flask + Jinja + Vanilla JS**: lighter CPU/RAM usage on Pi 4, no build step, easy deploy, still can build rich mobile UI with modern CSS and JS.
- Optional upgrade path: switch UI to React/Vue later and serve static build from Flask/Nginx without changing API.

## Core modules
- `player_engine`: wraps VLC/mpg123/ffplay; exposes state machine (idle/playing/paused/error).
- `library_manager`: scans local folder, builds metadata, cover extraction.
- `source_manager`: adapters for external APIs (podcasts, radio directories, internal service).
- `download_manager`: queue + progress + retry + caching cleanup.
- `realtime_gateway`: SSE pushes state + download progress to UI.
- `storage`: SQLite store for tracks, playlists, downloads, cache index.

