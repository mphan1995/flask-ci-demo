(() => {
  const MB = (window.MB = window.MB || {});

  MB.post = (url, body = {}) =>
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

  MB.get = (url) => fetch(url).then((res) => res.json());

  MB.ready = (fn) => {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  };

  MB.formatTime = (sec) => {
    const s = Math.floor(sec || 0);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${m}:${r.toString().padStart(2, "0")}`;
  };

  MB.setMessage = (text, isError = false) => {
    const el = document.getElementById("download-message");
    if (!el) return;
    el.textContent = text || "";
    el.classList.toggle("error", Boolean(isError));
  };

  MB.setAction = (payload) => {
    const el = document.getElementById("download-actions");
    if (!el) return;
    el.innerHTML = "";
    if (!payload || !payload.url) return;
    const button = document.createElement("button");
    button.className = "action-link";
    button.type = "button";
    button.textContent = payload.label || "Open";
    button.addEventListener("click", () => {
      if (payload.source === "youtube") {
        MB.openYouTubeModal(payload.url);
        return;
      }
      window.location.assign(payload.url);
    });
    el.appendChild(button);
  };

  MB.buildYouTubeEmbed = (url) => {
    try {
      const parsed = new URL(url);
      const host = parsed.hostname.replace("www.", "");
      let videoId = "";
      if (host === "youtu.be") {
        videoId = parsed.pathname.slice(1);
      } else if (host.endsWith("youtube.com")) {
        if (parsed.pathname.startsWith("/shorts/")) {
          videoId = parsed.pathname.split("/shorts/")[1]?.split("/")[0];
        } else if (parsed.pathname.startsWith("/embed/")) {
          videoId = parsed.pathname.split("/embed/")[1]?.split("/")[0];
        } else {
          videoId = parsed.searchParams.get("v") || "";
        }
      }
      if (!videoId) return null;
      return `https://www.youtube.com/embed/${videoId}?autoplay=1&playsinline=1`;
    } catch (err) {
      return null;
    }
  };

  MB.openYouTubeModal = (url) => {
    const modal = document.getElementById("yt-modal");
    const frame = document.getElementById("yt-frame");
    if (!modal || !frame) return;
    const embed = MB.buildYouTubeEmbed(url);
    if (!embed) {
      MB.setMessage("Unable to open YouTube embed.", true);
      return;
    }
    frame.src = embed;
    modal.hidden = false;
  };

  MB.closeModal = () => {
    const modal = document.getElementById("yt-modal");
    const frame = document.getElementById("yt-frame");
    if (modal) modal.hidden = true;
    if (frame) frame.src = "";
  };

  MB.bindModalClose = () => {
    const modal = document.getElementById("yt-modal");
    if (!modal) return;
    modal.querySelectorAll("[data-close]").forEach((el) => {
      el.addEventListener("click", MB.closeModal);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") MB.closeModal();
    });
  };

  MB.bindScan = () => {
    const scanBtn = document.getElementById("scan-library") || document.getElementById("btn-scan");
    if (!scanBtn) return;
    scanBtn.addEventListener("click", () => {
      MB.post("/api/scan");
    });
  };

  MB.updateCounts = async () => {
    const tracksEl = document.getElementById("count-tracks");
    const playlistsEl = document.getElementById("count-playlists");
    const downloadsEl = document.getElementById("count-downloads");
    try {
      if (tracksEl) {
        const tracks = await MB.get("/api/tracks");
        tracksEl.textContent = tracks.length;
      }
      if (playlistsEl) {
        const playlists = await MB.get("/api/playlists");
        playlistsEl.textContent = playlists.length;
      }
      if (downloadsEl) {
        const downloads = await MB.get("/api/downloads");
        downloadsEl.textContent = downloads.length;
      }
    } catch (err) {
      // ignore
    }
  };

  MB.ready(() => {
    MB.bindModalClose();
  });
})();
