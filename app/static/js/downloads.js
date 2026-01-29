(() => {
  const MB = window.MB;
  if (!MB) return;

  MB.ready(() => {
    const btn = document.getElementById("start-download");
    const list = document.getElementById("download-list");
    if (!btn) return;

    const load = async () => {
      if (!list) return;
      const data = await MB.get("/api/downloads");
      list.innerHTML = "";
      data.forEach((d) => {
        const item = document.createElement("div");
        item.className = "list-item";
        item.dataset.id = d.id;
        item.innerHTML = `<div>Job #${d.id} - ${d.status}</div><div>${Math.round(d.progress || 0)}%</div>`;
        list.appendChild(item);
      });
      MB.updateCounts();
    };

    btn.addEventListener("click", () => {
      const url = document.getElementById("download-url").value.trim();
      const mode = document.getElementById("download-mode").value;
      if (!url) {
        MB.setMessage("Invalid link.", true);
        MB.setAction(null);
        return;
      }
      MB.post("/api/downloads", { url, mode }).then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          MB.setMessage(data.message || "Invalid link.", true);
          MB.setAction(null);
          return;
        }
        if (res.status === 202) {
          MB.setMessage(data.message || "Source accepted. Waiting for adapter.");
          MB.setAction({ url: data.open_url, label: data.open_label, source: data.source });
          return;
        }
        MB.setMessage("Downloading...");
        MB.setAction(null);
        load();
      });
    });

    load();
  });
})();
