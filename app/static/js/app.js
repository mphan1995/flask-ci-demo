(() => {
  const post = (url, body = {}) =>
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

  const bindPlayback = () => {
    document.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        if (action === "play") {
          const trackId = btn.dataset.trackId || 1;
          post("/api/play", { track_id: Number(trackId) });
          return;
        }
        post(`/api/${action}`);
      });
    });

    const seek = document.getElementById("seek");
    if (seek) {
      seek.addEventListener("change", () => {
        post("/api/seek", { position_seconds: Number(seek.value) });
      });
    }

    const volume = document.getElementById("volume");
    if (volume) {
      volume.addEventListener("input", () => {
        post("/api/volume", { volume: Number(volume.value) });
      });
    }

    const shuffle = document.getElementById("shuffle");
    if (shuffle) {
      shuffle.addEventListener("change", () => {
        post("/api/shuffle", { enabled: shuffle.checked });
      });
    }

    const repeat = document.getElementById("repeat");
    if (repeat) {
      repeat.addEventListener("change", () => {
        post("/api/repeat", { mode: repeat.value });
      });
    }
  };

  const loadTracks = async () => {
    const list = document.getElementById("track-list");
    if (!list) return;
    const res = await fetch("/api/tracks");
    const data = await res.json();
    list.innerHTML = "";
    data.forEach((t) => {
      const item = document.createElement("div");
      item.className = "list-item";
      item.innerHTML = `<div><strong>${t.title}</strong><div class='muted'>${t.artist || "Unknown"}</div></div><button class='chip'>Play</button>`;
      item.querySelector("button").addEventListener("click", () => {
        post("/api/play", { track_id: t.id });
      });
      list.appendChild(item);
    });
  };

  const loadPlaylists = async () => {
    const list = document.getElementById("playlist-list");
    if (!list) return;
    const res = await fetch("/api/playlists");
    const data = await res.json();
    list.innerHTML = "";
    data.forEach((p) => {
      const item = document.createElement("div");
      item.className = "list-item";
      item.innerHTML = `<div>${p.name}</div><button class='ghost'>Delete</button>`;
      item.querySelector("button").addEventListener("click", () => {
        fetch(`/api/playlists/${p.id}`, { method: "DELETE" }).then(loadPlaylists);
      });
      list.appendChild(item);
    });
  };

  const bindPlaylistCreate = () => {
    const btn = document.getElementById("create-playlist");
    if (!btn) return;
    btn.addEventListener("click", () => {
      const input = document.getElementById("playlist-name");
      const name = input.value.trim();
      if (!name) return;
      post("/api/playlists", { name }).then(() => {
        input.value = "";
        loadPlaylists();
      });
    });
  };

  const bindDownload = () => {
    const btn = document.getElementById("start-download");
    if (!btn) return;
    btn.addEventListener("click", () => {
      const url = document.getElementById("download-url").value.trim();
      const mode = document.getElementById("download-mode").value;
      if (!url) return;
      post("/api/downloads", { url, mode });
    });
  };

  const bindScan = () => {
    const scanBtn = document.getElementById("scan-library") || document.getElementById("btn-scan");
    if (!scanBtn) return;
    scanBtn.addEventListener("click", () => {
      post("/api/scan");
    });
  };

  bindPlayback();
  bindPlaylistCreate();
  bindDownload();
  bindScan();
  loadTracks();
  loadPlaylists();
})();
