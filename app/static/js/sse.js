(() => {
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
    if (pos) pos.textContent = formatTime(data.position || 0);
    if (dur) dur.textContent = formatTime(data.duration || 0);
    if (volume) volume.value = data.volume ?? volume.value;
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

  const formatTime = (sec) => {
    const s = Math.floor(sec || 0);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${m}:${r.toString().padStart(2, "0")}`;
  };

  if (window.EventSource) {
    const es = new EventSource("/api/events");
    es.addEventListener("player", (e) => updatePlayer(JSON.parse(e.data)));
    es.addEventListener("download", (e) => updateDownloads(JSON.parse(e.data)));
  }
})();
