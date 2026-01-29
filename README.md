# MusicBox (Raspberry Pi Music Server)

He thong phat nhac qua browser tren dien thoai, backend Flask chay tren Raspberry Pi 4.

## Quick start
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Truy cap: `http://<IP-Pi>:8000`

## Cau hinh (tuy chon)
```
export MUSICBOX_DATA_DIR=/srv/music
export MUSICBOX_LOCAL_DIR=/srv/music/local
export MUSICBOX_CACHE_DIR=/srv/music/cache
export MUSICBOX_DB_PATH=/srv/music/db.sqlite
export SECRET_KEY=change-me
```

## Download rules
- Chap nhan: link audio truc tiep `.mp3/.wav/.flac/.aac/.m4a/.ogg`
- Nhan dien: YouTube / Nhaccuatui / Zing MP3 (can adapter hop phap de tai)
- Link khac (image/web/khong ro dinh dang) -> **Link khong hop le**

Neu co resolver hop phap (API noi bo):
```
export MUSICBOX_RESOLVER_URL=http://localhost:9000/resolve
export MUSICBOX_RESOLVER_TIMEOUT=10
```

## Production (systemd)
Mau service: `deploy/systemd/musicbox.service`
```
sudo systemctl daemon-reload
sudo systemctl enable musicbox
sudo systemctl start musicbox
```

## Audio engine
De xuat: VLC (stream) / mpg123 (local). Ket noi ALSA/HDMI/USB DAC.
