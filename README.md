# MusicBox - Raspberry Pi Music Server

Muc tieu: he thong phat nhac qua browser tren dien thoai, backend Flask chay tren Raspberry Pi 4.

## 1) Kien truc + lua chon stack
- **Chon stack**: Flask + Jinja + Vanilla JS + SSE (mobile-first, nhe, khong can build toolchain tren Pi).
- **Ly do**: Pi 4 RAM/CPU gioi han, can deploy nhanh; Jinja + CSS/JS van dat duoc UI dep + realtime.
- **Nang cap sau**: Co the tach thanh Flask API + React/Vue build static va phuc vu qua Flask/Nginx.

Xem so do chi tiet: `docs/ARCHITECTURE.md`.

## 2) Folder structure
```
app/
  __init__.py          # create_app + DI services
  config.py            # env config
  db.py                # SQLite schema
  models.py            # dataclasses
  routes/              # API + UI routes
  services/            # player, library, playlist, download, storage
  realtime/            # SSE event bus
  utils/               # validators
  templates/           # UI screens
  static/              # css/js
app.py                 # dev entry
wsgi.py                # production entry
requirements.txt
/docs/ARCHITECTURE.md
/deploy/ (optional for systemd/nginx)
/data/ (dev data)
```

## 3) API spec (tinh gon)
### Playback
- `POST /api/play` `{track_id}`
- `POST /api/pause`
- `POST /api/resume`
- `POST /api/next`
- `POST /api/prev`
- `POST /api/seek` `{position_seconds}`
- `POST /api/volume` `{volume}`
- `POST /api/repeat` `{mode: off|one|all}`
- `POST /api/shuffle` `{enabled: true|false}`
- `GET /api/status`

### Library
- `GET /api/tracks?query=&source=local|remote`
- `POST /api/upload` (multipart)
- `POST /api/scan`

### Playlists
- `GET /api/playlists`
- `POST /api/playlists` `{name}`
- `DELETE /api/playlists/{id}`
- `POST /api/playlists/{id}/items` `{track_id, position}`
- `PATCH /api/playlists/{id}/reorder` `{ordered_track_ids:[...]}`

### Downloads
- `POST /api/downloads` `{url, mode=direct|cache|stream}`
- `GET /api/downloads`
- `DELETE /api/downloads/{id}`

### Realtime
- `GET /api/events` (SSE: player/download updates)

## 4) Data models
### Track
- `id, title, artist, album, duration, cover_path, source_type, source_url, local_path`

### Playlist
- `id, name`

### PlaylistItem
- `id, playlist_id, track_id, position`

### DownloadJob
- `id, url, mode, status, progress, local_path, error`

## 5) Audio engine recommendation
- **VLC (python-vlc/CLI)**: manh ve stream HLS/DASH, xu ly nhieu format, on dinh cho network.
- **mpg123 CLI**: nhe, phu hop mp3 local, tieu ton it CPU.

Chon nhanh:
- **Local-only**: mpg123 (nhe, nhanh)
- **Stream-heavy / remote**: VLC (xu ly stream tot)

## 6) Setup tren Raspberry Pi 4
### OS packages
```
sudo apt update
sudo apt install -y python3-venv python3-pip vlc mpg123 ffmpeg
```

### App setup
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment (production)
```
export MUSICBOX_DATA_DIR=/srv/music
export MUSICBOX_LOCAL_DIR=/srv/music/local
export MUSICBOX_CACHE_DIR=/srv/music/cache
export MUSICBOX_DB_PATH=/srv/music/db.sqlite
export SECRET_KEY=change-me
```

### Run (dev)
```
python app.py
```

### systemd service
Tao file `/etc/systemd/system/musicbox.service`:
```
[Unit]
Description=MusicBox Flask Server
After=network.target

[Service]
User=pi
WorkingDirectory=/srv/musicbox
Environment=MUSICBOX_DATA_DIR=/srv/music
Environment=MUSICBOX_LOCAL_DIR=/srv/music/local
Environment=MUSICBOX_CACHE_DIR=/srv/music/cache
Environment=MUSICBOX_DB_PATH=/srv/music/db.sqlite
ExecStart=/srv/musicbox/.venv/bin/gunicorn -w 2 -b 0.0.0.0:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Kich hoat:
```
sudo systemctl daemon-reload
sudo systemctl enable musicbox
sudo systemctl start musicbox
```

### Optional: Nginx reverse proxy
- Terminate HTTP, serve static, rate limit download endpoint.

## 7) Download-from-link va Remote sources
- User dan link -> validate URL -> download (direct/cache) -> them vao library.
- Ho tro link file truc tiep (mp3/wav/flac/aac/ogg). HLS/DASH chi o che do stream (tuong thich voi VLC).
- Remote sources: Adapter class trong `source_manager` de goi API, lay metadata + playable URL.
- Cache: TTL + max size; co cleanup job.
- Luu y: chi su dung nguon hop phap, ton trong ban quyen.

## 8) Security & reliability
- Mac dinh LAN-only, co the them PIN/session.
- Validate URL (chan loopback/private IP neu can).
- Gioi han dung luong, allowlist extension.
- Rate limit /api/downloads.
- Safe storage paths (secure_filename, no path traversal).
- Logging + retry policy cho download.

## 9) Test checklist
- Audio output: HDMI / 3.5mm / USB DAC.
- Playback commands, seek, volume.
- Download: direct URL, size limit, retry.
- Reboot persistence: systemd auto-start.
- UI realtime updates (SSE).

## 10) Rui ro + huong xu ly
- **ARM packages**: VLC/ffmpeg co the khac version -> pin apt repo, test tren Pi.
- **Audio device**: ALSA default sai -> set output device, test `aplay -l`.
- **Stream instability**: can cache hoac retry, fallback to download.
- **Disk fill**: can TTL cleanup + max size.
- **Network drops**: reconnect SSE, retry downloads.

