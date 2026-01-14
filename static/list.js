import { fetchJson } from "./modules/api.js";
import { qs, qsa, showToast } from "./modules/dom.js";
import { riskBadge, statusBadge } from "./modules/badges.js";

const state = {
  services: [],
  summary: null,
  filter: "all",
};

const elements = {
  refreshBtn: qs("#list-refresh"),
  summary: qs("#service-summary"),
  disabledList: qs("#disabled-list"),
  runningList: qs("#running-list"),
  table: qs("#services-table"),
  search: qs("#service-search"),
  statTotal: qs("#stat-total"),
  statRunning: qs("#stat-running"),
  statDisabled: qs("#stat-disabled"),
  filterButtons: qsa(".chip-filter"),
};

function getStartValue(service) {
  if (service.start_value === null || service.start_value === undefined) {
    return "-";
  }
  return service.start_value;
}

function getServiceState(service) {
  return service.state || "Unknown";
}

function isDisabled(service) {
  return (
    service.start_value === 4 ||
    (service.start_mode || "").toLowerCase() === "disabled"
  );
}

function matchesFilter(service) {
  if (state.filter === "all") return true;
  if (state.filter === "running") return getServiceState(service) === "Running";
  if (state.filter === "stopped") return getServiceState(service) === "Stopped";
  if (state.filter === "disabled") return isDisabled(service);
  if (state.filter === "unknown") return getServiceState(service) === "Unknown";
  return true;
}

function renderSummary() {
  if (!state.summary || !elements.summary) return;
  elements.summary.innerHTML = `
    <div>Total services: ${state.summary.total}</div>
    <div>Running: ${state.summary.running}</div>
    <div>Stopped: ${state.summary.stopped}</div>
    <div>Disabled: ${state.summary.disabled}</div>
    <div>Unknown: ${state.summary.unknown}</div>
    <div>Source: ${state.summary.source}</div>
  `;

  if (elements.statTotal) elements.statTotal.textContent = state.summary.total ?? "-";
  if (elements.statRunning) {
    elements.statRunning.textContent = state.summary.running ?? "-";
  }
  if (elements.statDisabled) {
    elements.statDisabled.textContent = state.summary.disabled ?? "-";
  }
}

function renderLists() {
  const disabled = state.services.filter((service) => isDisabled(service));
  const running = state.services.filter(
    (service) => getServiceState(service) === "Running"
  );

  elements.disabledList.innerHTML = "";
  elements.runningList.innerHTML = "";

  if (!disabled.length) {
    elements.disabledList.textContent = "No disabled services found.";
  } else {
    disabled.slice(0, 60).forEach((service) => {
      const row = document.createElement("div");
      row.className = "list-item";
      row.innerHTML = `
        <div>
          <div><strong>${service.display_name || service.name}</strong></div>
          <div class="muted">${service.name}</div>
        </div>
        ${statusBadge("Disabled")}
      `;
      elements.disabledList.appendChild(row);
    });
  }

  if (!running.length) {
    elements.runningList.textContent = "No running services found.";
  } else {
    running.slice(0, 60).forEach((service) => {
      const row = document.createElement("div");
      row.className = "list-item";
      row.innerHTML = `
        <div>
          <div><strong>${service.display_name || service.name}</strong></div>
          <div class="muted">${service.name}</div>
        </div>
        ${statusBadge("Running")}
      `;
      elements.runningList.appendChild(row);
    });
  }
}

function renderTable() {
  const query = (elements.search?.value || "").toLowerCase();
  const filtered = state.services.filter((service) => {
    if (!matchesFilter(service)) return false;
    if (!query) return true;
    return (
      service.name?.toLowerCase().includes(query) ||
      service.display_name?.toLowerCase().includes(query)
    );
  });

  elements.table.innerHTML = "";
  if (!filtered.length) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='6' class='muted'>No services found.</td>";
    elements.table.appendChild(row);
    return;
  }

  filtered.forEach((service) => {
    const status = isDisabled(service)
      ? "Disabled"
      : getServiceState(service);
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${service.display_name || service.name}</td>
      <td>${statusBadge(status)}</td>
      <td>${service.start_mode || "-"}</td>
      <td>${getStartValue(service)}</td>
      <td>${riskBadge(service.risk)}</td>
      <td title="${service.notes || ""}">${service.notes || ""}</td>
    `;
    elements.table.appendChild(row);
  });
}

async function loadServices() {
  const data = await fetchJson("/api/services");
  state.services = data.services || [];
  state.summary = data.summary || null;
  renderSummary();
  renderLists();
  renderTable();
}

function setActiveFilter(filter) {
  state.filter = filter;
  elements.filterButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.filter === filter);
  });
  renderTable();
}

elements.refreshBtn?.addEventListener("click", async () => {
  try {
    await loadServices();
    showToast("Service list refreshed", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
});

elements.search?.addEventListener("input", renderTable);
elements.filterButtons.forEach((btn) => {
  btn.addEventListener("click", () => setActiveFilter(btn.dataset.filter));
});

loadServices().catch((err) => showToast(err.message, "error"));
