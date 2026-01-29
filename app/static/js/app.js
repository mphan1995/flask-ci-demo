(() => {
  const MB = window.MB;
  if (!MB) return;
  MB.ready(() => {
    MB.bindScan();
    MB.updateCounts();
    const recent = document.getElementById("recent-list");
    if (recent) {
      const data = JSON.parse(localStorage.getItem("mb_recent") || "[]");
      recent.textContent = data.length ? data.join(" · ") : "No recent tracks.";
    }
  });
})();
