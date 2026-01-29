(() => {
  const MB = window.MB;
  if (!MB) return;

  MB.ready(() => {
    const list = document.getElementById("track-list");
    const search = document.getElementById("search");
    const chips = document.querySelectorAll("[data-source]");
    if (!list) return;

    let allTracks = [];
    let currentSource = "";

    const render = (items) => {
      list.innerHTML = "";
      items.forEach((t) => {
        const item = document.createElement("div");
        item.className = "list-item";
        item.innerHTML = `<div><strong>${t.title}</strong><div class='muted'>${t.artist || "Unknown"}</div></div><button class='chip'>Play</button>`;
        item.querySelector("button").addEventListener("click", () => {
          MB.post("/api/play", { track_id: t.id });
        });
        list.appendChild(item);
      });
    };

    const applyFilter = () => {
      const q = (search?.value || "").toLowerCase();
      const filtered = allTracks.filter((t) => {
        const matchesSource = currentSource ? t.source_type === currentSource : true;
        const matchesQuery =
          t.title?.toLowerCase().includes(q) ||
          (t.artist || "").toLowerCase().includes(q) ||
          (t.album || "").toLowerCase().includes(q);
        return matchesSource && matchesQuery;
      });
      render(filtered);
    };

    const load = async () => {
      allTracks = await MB.get("/api/tracks");
      applyFilter();
      MB.updateCounts();
    };

    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        chips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        currentSource = chip.dataset.source || "";
        applyFilter();
      });
    });

    if (search) {
      search.addEventListener("input", applyFilter);
    }

    load();
  });
})();
