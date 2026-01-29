# MusicBox (Raspberry Pi Music Server)

Mobile-first music server controlled from a phone browser. Flask backend on Raspberry Pi 4.

## Quick start
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open: `http://<PI-IP>:8000`

## Optional config
```
export MUSICBOX_DATA_DIR=/srv/music
export MUSICBOX_LOCAL_DIR=/srv/music/local
export MUSICBOX_CACHE_DIR=/srv/music/cache
export MUSICBOX_DB_PATH=/srv/music/db.sqlite
export SECRET_KEY=change-me
```

## Download rules
- Allowed: direct audio links `.mp3/.wav/.flac/.aac/.m4a/.ogg`
- Detected: YouTube / Nhaccuatui / Zing MP3 (requires legal resolver or direct audio URL)
- Everything else => **Invalid link**

If you have a legal resolver:
```
export MUSICBOX_RESOLVER_URL=http://localhost:9000/resolve
export MUSICBOX_RESOLVER_TIMEOUT=10
```

## Nginx (root + /musicbox)
Template: `deploy/nginx/musicbox_combined.conf`
```
sudo ln -s /srv/musicbox/deploy/nginx/musicbox_combined.conf /etc/nginx/sites-enabled/musicbox
sudo nginx -t && sudo systemctl reload nginx
```
Access:
- `http://<PI-IP>/`
- `http://<PI-IP>/musicbox/`

## Static IP for Raspberry Pi
### Raspberry Pi OS (dhcpcd)
Edit `/etc/dhcpcd.conf`:
```
interface eth0
static ip_address=192.168.1.10/24
static routers=192.168.1.1
static domain_name_servers=1.1.1.1 8.8.8.8
```
Then: `sudo reboot`

### Ubuntu Server (netplan)
Edit `/etc/netplan/01-netcfg.yaml`:
```
network:
  version: 2
  ethernets:
    eth0:
      addresses: [192.168.1.10/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1,8.8.8.8]
```
Then: `sudo netplan apply`

## UFW (open ports)
```
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp
sudo ufw enable
sudo ufw status
```

## Production (systemd)
Template: `deploy/systemd/musicbox.service`
```
sudo systemctl daemon-reload
sudo systemctl enable musicbox
sudo systemctl start musicbox
```

## Audio engine
Recommended: VLC (stream) / mpg123 (local). Outputs: ALSA/HDMI/USB DAC.
