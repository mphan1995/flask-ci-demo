const formatBytes = (bytes) => {
  if (bytes === null || bytes === undefined) return "-";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = Number(bytes);
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
};

const fetchJSON = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || "Request failed");
    error.payload = data;
    throw error;
  }
  return data;
};

let actionCache = [];
let scanStats = {};

const computeScanStats = (logs) => {
  const stats = {};
  logs.forEach((entry) => {
    if (entry.mode !== "scan") return;
    if (!entry.action_id || typeof entry.duration_ms !== "number") return;
    if (!stats[entry.action_id]) {
      stats[entry.action_id] = { totalMs: 0, count: 0 };
    }
    stats[entry.action_id].totalMs += entry.duration_ms;
    stats[entry.action_id].count += 1;
  });

  const averages = {};
  Object.keys(stats).forEach((actionId) => {
    const item = stats[actionId];
    if (item.count) {
      averages[actionId] = Math.round(item.totalMs / item.count);
    }
  });
  return averages;
};

const loadScanStats = async () => {
  try {
    const data = await fetchJSON("/api/logs?limit=200");
    scanStats = computeScanStats(data.logs || []);
  } catch (error) {
    scanStats = {};
  }
};

const formatDuration = (ms) => {
  if (ms === null || ms === undefined) return "-";
  const seconds = Number(ms) / 1000;
  if (seconds < 1) return `${Math.round(ms)} ms`;
  return `${seconds.toFixed(2)} s`;
};

const startScanFallback = (container, actionId) => {
  const start = Date.now();
  const etaMs = scanStats[actionId];
  const etaText = etaMs ? `ETA ~${formatDuration(etaMs)}` : "ETA unknown";
  container.textContent = `Scanning... ${etaText}`;

  const timer = setInterval(() => {
    const elapsed = Date.now() - start;
    const elapsedText = formatDuration(elapsed);
    const hint = etaMs ? ` ETA ~${formatDuration(etaMs)}` : "";
    container.textContent = `Scanning... elapsed ${elapsedText}.${hint}`;
  }, 2000);

  return () => clearInterval(timer);
};

const setStatusStrip = async () => {
  const status = document.getElementById("status-strip");
  if (!status) return;
  try {
    const data = await fetchJSON("/api/status");
    status.querySelector(".status-sim").textContent = data.simulation
      ? "SIMULATION ON"
      : "LIVE MODE";
    status.querySelector(".status-sim").className =
      "badge " + (data.simulation ? "warning" : "success");
    status.querySelector(".status-busy").textContent = data.busy
      ? "JOB RUNNING"
      : "IDLE";
    status.querySelector(".status-busy").className =
      "badge " + (data.busy ? "warning" : "success");
    status.querySelector(".status-admin").textContent = data.admin
      ? "ADMIN" : "STANDARD";
    status.querySelector(".status-admin").className =
      "badge " + (data.admin ? "success" : "warning");
  } catch (error) {
    status.querySelector(".status-sim").textContent = "STATUS UNKNOWN";
    status.querySelector(".status-sim").className = "badge warning";
  }
};

const loadDashboard = async () => {
  const drivesGrid = document.getElementById("drives-grid");
  const foldersGrid = document.getElementById("folders-grid");
  if (!drivesGrid || !foldersGrid) return;

  drivesGrid.innerHTML = "";
  foldersGrid.innerHTML = "";

  try {
    const data = await fetchJSON("/api/drives");
    data.drives.forEach((drive, index) => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.animationDelay = `${index * 0.05}s`;
      card.innerHTML = `
        <h3>${drive.name}</h3>
        <div class="metric">${formatBytes(drive.free)} free</div>
        <div class="submetric">${formatBytes(drive.used)} used of ${formatBytes(drive.total)}</div>
        <div class="submetric">${drive.free_percent}% free</div>
      `;
      drivesGrid.appendChild(card);
    });

    data.top_folders.forEach((folder, index) => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.animationDelay = `${index * 0.06}s`;
      card.innerHTML = `
        <h3>${folder.name}</h3>
        <div class="metric">${formatBytes(folder.bytes)}</div>
        <div class="submetric">${folder.path}</div>
        <div class="submetric">${folder.files} files${folder.truncated ? " (truncated)" : ""}</div>
      `;
      foldersGrid.appendChild(card);
    });
  } catch (error) {
    drivesGrid.innerHTML = `<div class="card"><h3>Error</h3><p>${error.message}</p></div>`;
  }
};

const renderActionResult = (container, payload) => {
  const summary = payload.result || {};
  const bytes = summary.bytes ?? summary.estimated_bytes;
  const status = payload.ok ? "success" : "danger";
  const label = payload.ok ? "Success" : "Failed";
  container.innerHTML = `
    <div class="badge ${status}">${label}</div>
    <div>Mode: ${payload.mode || "-"}</div>
    <div>Duration: ${formatDuration(payload.duration_ms)}</div>
    <div>Estimated bytes: ${bytes !== undefined ? formatBytes(bytes) : "-"}</div>
    <pre>${JSON.stringify(payload, null, 2)}</pre>
  `;
};

const scanAction = async (actionId, resultBox) => {
  const stopFallback = startScanFallback(resultBox, actionId);
  try {
    const response = await fetchJSON(`/api/actions/${actionId}/scan`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    renderActionResult(resultBox, response);
  } catch (error) {
    resultBox.textContent = error.payload?.error || error.message;
  } finally {
    stopFallback();
  }
};

const scanAllActions = async () => {
  if (!actionCache.length) {
    await loadActions();
  }
  await loadScanStats();
  const tasks = actionCache.map((action) => {
    const resultBox = document.getElementById(`result-${action.id}`);
    if (!resultBox) return Promise.resolve();
    return scanAction(action.id, resultBox);
  });
  await Promise.allSettled(tasks);
};

const loadActions = async () => {
  const actionsGrid = document.getElementById("actions-grid");
  if (!actionsGrid) return;
  actionsGrid.innerHTML = "";

  try {
    const data = await fetchJSON("/api/actions");
    actionCache = data.actions || [];
    await loadScanStats();
    actionCache.forEach((action, index) => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.animationDelay = `${index * 0.04}s`;
      card.innerHTML = `
        <h3>${action.name}</h3>
        <p>${action.description}</p>
        <div class="badge ${action.requires_admin ? "warning" : "success"}">
          ${action.requires_admin ? "ADMIN REQUIRED" : "SAFE"}
        </div>
        <div class="actions-row">
          <button class="secondary" data-action="scan">Scan</button>
          ${action.requires_admin ? "<button class=\"secondary\" data-action=\"admin\">Admin ON</button>" : ""}
          <button class="danger" data-action="run">Clean</button>
        </div>
        <div class="result-box" id="result-${action.id}">No activity yet.</div>
      `;
      actionsGrid.appendChild(card);

      const scanBtn = card.querySelector("button[data-action='scan']");
      const runBtn = card.querySelector("button[data-action='run']");
      const adminBtn = card.querySelector("button[data-action='admin']");
      const resultBox = card.querySelector(`#result-${action.id}`);

      scanBtn.addEventListener("click", async () => {
        await scanAction(action.id, resultBox);
      });

      runBtn.addEventListener("click", async () => {
        const confirmed = window.confirm(
          `Clean ${action.name}? This will delete files.\n\nClick OK to confirm.`
        );
        if (!confirmed) return;
        resultBox.textContent = "Cleaning...";
        try {
          const response = await fetchJSON(`/api/actions/${action.id}/run`, {
            method: "POST",
            body: JSON.stringify({ confirm: true }),
          });
          renderActionResult(resultBox, response);
        } catch (error) {
          resultBox.textContent = error.payload?.error || error.message;
        }
      });

      if (adminBtn) {
        adminBtn.addEventListener("click", async () => {
          resultBox.textContent = "Requesting admin mode...";
          try {
            const response = await fetchJSON("/api/admin/launch", {
              method: "POST",
              body: JSON.stringify({}),
            });
            if (response.url) {
              window.open(response.url, "_blank");
            }
            resultBox.innerHTML = `
              <div class="badge success">Admin request sent</div>
              <div>Open: ${response.url || "Check admin prompt"}</div>
              <pre>${JSON.stringify(response, null, 2)}</pre>
            `;
          } catch (error) {
            resultBox.textContent = error.payload?.error || error.message;
          }
        });
      }
    });
  } catch (error) {
    actionsGrid.innerHTML = `<div class="card"><h3>Error</h3><p>${error.message}</p></div>`;
  }
};

const loadLogs = async () => {
  const logsTable = document.getElementById("logs-table");
  if (!logsTable) return;

  try {
    const data = await fetchJSON("/api/logs?limit=200");
    const tbody = logsTable.querySelector("tbody");
    tbody.innerHTML = "";

    data.logs.forEach((log) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${log.timestamp || ""}</td>
        <td>${log.user || ""}</td>
        <td>${log.action_name || log.action_id || ""}</td>
        <td>${log.mode || ""}</td>
        <td>${log.status || ""}</td>
        <td>${formatBytes(log.bytes)}</td>
        <td>${formatDuration(log.duration_ms)}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (error) {
    const tbody = logsTable.querySelector("tbody");
    tbody.innerHTML = `<tr><td colspan="7">${error.message}</td></tr>`;
  }
};

const bindRefresh = () => {
  const refreshDashboard = document.getElementById("refresh-dashboard");
  if (refreshDashboard) {
    refreshDashboard.addEventListener("click", loadDashboard);
  }
  const refreshLogs = document.getElementById("refresh-logs");
  if (refreshLogs) {
    refreshLogs.addEventListener("click", loadLogs);
  }
  const scanAllBtn = document.getElementById("scan-all");
  if (scanAllBtn) {
    scanAllBtn.addEventListener("click", scanAllActions);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  setStatusStrip();
  loadDashboard();
  loadActions();
  loadLogs();
  bindRefresh();
});
