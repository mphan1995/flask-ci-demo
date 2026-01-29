(() => {
  const MB = window.MB;
  if (!MB) return;

  MB.ready(() => {
    const list = document.getElementById("playlist-list");
    const btn = document.getElementById("create-playlist");
    if (!list) return;

    const load = async () => {
      const data = await MB.get("/api/playlists");
      list.innerHTML = "";
      data.forEach((p) => {
        const item = document.createElement("div");
        item.className = "list-item";
        item.innerHTML = `<div>${p.name}</div><button class='ghost'>Delete</button>`;
        item.querySelector("button").addEventListener("click", () => {
          fetch(`/api/playlists/${p.id}`, { method: "DELETE" }).then(load);
        });
        list.appendChild(item);
      });
      MB.updateCounts();
    };

    if (btn) {
      btn.addEventListener("click", () => {
        const input = document.getElementById("playlist-name");
        const name = input.value.trim();
        if (!name) return;
        MB.post("/api/playlists", { name }).then(() => {
          input.value = "";
          load();
        });
      });
    }

    load();
  });
})();
