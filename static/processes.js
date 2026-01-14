import { fetchJson } from "./modules/api.js";
import { qs, showToast } from "./modules/dom.js";
import { statusBadge } from "./modules/badges.js";

const state = {
  groups: [],
  summary: null,
};

const elements = {
  adminStatus: qs("#admin-status"),
  healthStatus: qs("#health-status"),
  progress: qs("#process-progress"),
  refreshBtn: qs("#process-refresh"),
  summary: qs("#process-summary"),
  table: qs("#process-table"),
  search: qs("#process-search"),
  minRam: qs("#process-min-ram"),
  limit: qs("#process-limit"),
  statProcesses: qs("#stat-processes"),
  statGroups: qs("#stat-groups"),
  statTopRam: qs("#stat-top-ram"),
};

function setHealth(text, type = "info") {
  if (!elements.healthStatus) return;
  elements.healthStatus.textContent = `Status: ${text}`;
  elements.healthStatus.style.color = type === "error" ? "#b91c1c" : "#1f2937";
}

function setAdminStatus(isAdmin) {
  if (!elements.adminStatus) return;
  if (isAdmin) {
    elements.adminStatus.textContent = "Admin: Yes";
    elements.adminStatus.style.color = "#15803d";
  } else {
    elements.adminStatus.textContent = "Admin: No";
    elements.adminStatus.style.color = "#b91c1c";
  }
}

function setProgress(text) {
  if (!elements.progress) return;
  elements.progress.classList.remove("hidden");
  elements.progress.textContent = text;
}

function clearProgress() {
  if (!elements.progress) return;
  elements.progress.classList.add("hidden");
}

function formatRam(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  const rounded = Math.round(value * 10) / 10;
  return rounded.toString();
}

function matchesQuery(group, query) {
  if (!query) return true;
  const nameMatch = (group.name || "").toLowerCase().includes(query);
  if (nameMatch) return true;
  return (group.services || []).some((service) => {
    const serviceName = service.name || "";
    const displayName = service.display_name || "";
    return (
      serviceName.toLowerCase().includes(query) ||
      displayName.toLowerCase().includes(query)
    );
  });
}

function renderSummary() {
  if (!elements.summary) return;
  if (!state.summary) {
    elements.summary.textContent = "No data yet.";
    return;
  }
  elements.summary.innerHTML = `
    <div>Processes: ${state.summary.processes}</div>
    <div>Groups: ${state.summary.groups}</div>
    <div>Services: ${state.summary.services}</div>
    <div>Process source: ${state.summary.process_source || "-"}</div>
    <div>Service source: ${state.summary.service_source || "-"}</div>
  `;
}

function renderStats() {
  if (elements.statProcesses) {
    elements.statProcesses.textContent = state.summary?.processes ?? "-";
  }
  if (elements.statGroups) {
    elements.statGroups.textContent = state.summary?.groups ?? "-";
  }
  if (elements.statTopRam) {
    const top = state.groups[0]?.memory_mb;
    elements.statTopRam.textContent = top !== undefined ? formatRam(top) : "-";
  }
}

function renderServiceDetails(group) {
  const services = group.services || [];
  if (!services.length) {
    return `<span class="muted">No linked services.</span>`;
  }

  const ruleMatches = services.filter((service) => (service.rules || []).length);
  const summaryText = ruleMatches.length
    ? `${services.length} services (${ruleMatches.length} with rules)`
    : `${services.length} services`;

  const items = services
    .map((service) => {
      const ruleTags = (service.rules || [])
        .map((rule) => {
          const risk = (rule.risk || "LOW").toLowerCase();
          const safeRisk = ["low", "medium", "high"].includes(risk)
            ? risk
            : "low";
          const title = rule.title || rule.id;
          return `<span class="badge risk-${safeRisk}" title="${title}">${rule.id}</span>`;
        })
        .join("");
      const note = service.notes
        ? `<div class="service-note muted">${service.notes}</div>`
        : "";
      return `
        <div class="service-row">
          <div class="service-title">${service.display_name || service.name}</div>
          <div class="service-meta-line">
            <span>${service.name}</span>
            <span>Start: ${service.start_mode || "-"}</span>
            ${statusBadge(service.state || "Unknown")}
          </div>
          <div class="rule-tags">
            ${ruleTags || `<span class="muted">No rule match.</span>`}
          </div>
          ${note}
        </div>
      `;
    })
    .join("");

  return `
    <details class="details">
      <summary>${summaryText}</summary>
      <div class="service-block">${items}</div>
    </details>
  `;
}

function renderTable() {
  if (!elements.table) return;
  const query = (elements.search?.value || "").trim().toLowerCase();
  const minRam = parseFloat(elements.minRam?.value || "0");
  const limit = parseInt(elements.limit?.value || "30", 10) || 30;

  const filtered = state.groups.filter((group) => {
    if (!matchesQuery(group, query)) return false;
    if (!Number.isNaN(minRam) && group.memory_mb < minRam) return false;
    return true;
  });

  const limited = filtered.slice(0, limit);
  elements.table.innerHTML = "";

  if (!limited.length) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='4' class='muted'>No processes match.</td>";
    elements.table.appendChild(row);
    return;
  }

  limited.forEach((group) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>
        <div class="process-title">${group.name || "-"}</div>
      </td>
      <td>${group.process_count || 0}</td>
      <td>${formatRam(group.memory_mb)}</td>
      <td>${renderServiceDetails(group)}</td>
    `;
    elements.table.appendChild(row);
  });
}

async function loadHealth() {
  try {
    const data = await fetchJson("/api/health");
    setAdminStatus(data.admin);
  } catch (err) {
    setHealth("Error", "error");
  }
}

async function loadProcesses() {
  setProgress("Scanning processes...");
  setHealth("Scanning");
  try {
    const data = await fetchJson("/api/processes");
    state.groups = data.process_groups || [];
    state.summary = data.summary || null;
    renderSummary();
    renderStats();
    renderTable();
    showToast("Process scan completed", "success");
  } catch (err) {
    showToast(err.message, "error");
    setHealth("Error", "error");
  } finally {
    clearProgress();
    setHealth("Ready");
  }
}

elements.refreshBtn?.addEventListener("click", loadProcesses);
elements.search?.addEventListener("input", renderTable);
elements.minRam?.addEventListener("input", renderTable);
elements.limit?.addEventListener("change", renderTable);

loadHealth();
loadProcesses();
