(() => {
  const MB = window.MB;

  const updateRecent = (data) => {
    if (!data.title) return;
    const key = "mb_recent";
    const current = JSON.parse(localStorage.getItem(key) || "[]");
    const next = [data.title, ...current.filter((t) => t !== data.title)].slice(0, 5);
    localStorage.setItem(key, JSON.stringify(next));
    const list = document.getElementById("recent-list");
    if (list) {
      list.textContent = next.length ? next.join(" · ") : "No recent tracks.";
    }
  };

  const updatePlayer = (data) => {
    const title = document.getElementById("track-title");
    const artist = document.getElementById("track-artist");
    const pos = document.getElementById("pos");
    const dur = document.getElementById("dur");
    const seek = document.getElementById("seek");
    const volume = document.getElementById("volume");

    if (title && data.title) title.textContent = data.title;
    if (artist && data.artist) artist.textContent = data.artist || "Unknown";
    if (seek && data.duration) seek.max = Math.floor(data.duration);
    if (seek) seek.value = Math.floor(data.position || 0);
    if (pos) pos.textContent = MB?.formatTime ? MB.formatTime(data.position || 0) : "0:00";
    if (dur) dur.textContent = MB?.formatTime ? MB.formatTime(data.duration || 0) : "0:00";
    if (volume) volume.value = data.volume ?? volume.value;

    const miniTitle = document.getElementById("mini-title");
    const miniArtist = document.getElementById("mini-artist");
    const miniPos = document.getElementById("mini-pos");
    const miniDur = document.getElementById("mini-dur");
    const miniBar = document.getElementById("mini-bar");
    if (miniTitle && data.title) miniTitle.textContent = data.title;
    if (miniArtist && data.artist) miniArtist.textContent = data.artist || "Unknown";
    if (miniPos) miniPos.textContent = MB?.formatTime ? MB.formatTime(data.position || 0) : "0:00";
    if (miniDur) miniDur.textContent = MB?.formatTime ? MB.formatTime(data.duration || 0) : "0:00";
    if (miniBar && data.duration) {
      const pct = Math.min(100, (data.position / data.duration) * 100);
      miniBar.style.width = `${pct || 0}%`;
    }

    const statusDot = document.getElementById("status-dot");
    if (statusDot) {
      statusDot.classList.toggle("playing", data.status === "playing");
      statusDot.classList.toggle("paused", data.status === "paused");
    }

    updateRecent(data);
  };

  const updateDownloads = (data) => {
    const list = document.getElementById("download-list");
    if (!list) return;
    const existing = list.querySelector(`[data-id='${data.id}']`);
    const item = existing || document.createElement("div");
    item.className = "list-item";
    item.dataset.id = data.id;
    item.innerHTML = `<div>Job #${data.id} - ${data.status}</div><div>${Math.round(data.progress || 0)}%</div>`;
    if (!existing) list.prepend(item);
  };

  if (window.EventSource) {
    const es = new EventSource("/api/events");
    es.addEventListener("player", (e) => updatePlayer(JSON.parse(e.data)));
    es.addEventListener("download", (e) => updateDownloads(JSON.parse(e.data)));
  }
})();
