import { fetchJson } from "./modules/api.js";
import { qs, qsa, showToast } from "./modules/dom.js";
import { riskBadge, statusBadge, typeBadge } from "./modules/badges.js";
import { setupTabs } from "./modules/tabs.js";

const state = {
  rules: [],
  selected: new Set(),
  system: null,
  admin: false,
  lastPlan: null,
  backups: [],
  logs: [],
  scanned: false,
  servicesSummary: null,
  servicesRunning: [],
};

const elements = {
  adminStatus: qs("#admin-status"),
  healthStatus: qs("#health-status"),
  scanProgress: qs("#scan-progress"),
  systemInfo: qs("#system-info"),
  planSummary: qs("#plan-summary"),
  rulesTable: qs("#rules-table"),
  recommendedTable: qs("#recommended-table"),
  advancedTable: qs("#advanced-table"),
  backupList: qs("#backup-list"),
  logsList: qs("#logs-list"),
  logDetail: qs("#log-detail"),
  rollbackInput: qs("#rollback-id"),
  adminWarning: qs("#admin-warning"),
  servicesSummary: qs("#services-summary"),
  servicesList: qs("#services-list"),
  statRunning: qs("#stat-running"),
  statTotal: qs("#stat-total"),
  statRules: qs("#stat-rules"),
  rulesHint: qs("#rules-hint"),
  dryrunBtn: qs("#dryrun-btn"),
  applyBtn: qs("#apply-btn"),
  enableBtn: qs("#enable-btn"),
  rulesSearch: qs("#rules-search"),
  rulesSelectAll: qs("#rules-select-all"),
  rulesClear: qs("#rules-clear"),
  servicesFilter: qs("#services-filter"),
};

function setHealth(text, type = "info") {
  if (!elements.healthStatus) return;
  elements.healthStatus.textContent = `Status: ${text}`;
  elements.healthStatus.style.color = type === "error" ? "#b91c1c" : "#1f2937";
}

function setAdminStatus(isAdmin) {
  state.admin = isAdmin;
  if (!elements.adminStatus) return;
  if (isAdmin) {
    elements.adminStatus.textContent = "Admin: Yes";
    elements.adminStatus.style.color = "#15803d";
    elements.adminWarning?.classList.add("hidden");
  } else {
    elements.adminStatus.textContent = "Admin: No";
    elements.adminStatus.style.color = "#b91c1c";
    elements.adminWarning?.classList.remove("hidden");
  }
}

function setActionState() {
  const locked = !state.scanned;
  elements.dryrunBtn.disabled = locked;
  elements.applyBtn.disabled = locked;
  if (elements.enableBtn) elements.enableBtn.disabled = locked;
  if (elements.rulesSelectAll) elements.rulesSelectAll.disabled = locked;
  if (elements.rulesClear) elements.rulesClear.disabled = locked;
  if (elements.rulesHint) {
    elements.rulesHint.textContent = locked
      ? "Scan to enable rule selection."
      : "Select rules to disable or enable.";
  }
  qsa("input[type='checkbox']").forEach((input) => {
    input.disabled = locked;
  });
}

function renderSystemInfo() {
  if (!elements.systemInfo) return;
  if (!state.system) {
    elements.systemInfo.textContent = "No scan yet.";
    return;
  }
  const info = state.system;
  elements.systemInfo.innerHTML = `
    <div>Computer: ${info.computer || "-"}</div>
    <div>OS: ${info.os || "-"}</div>
    <div>Version: ${info.version || "-"}</div>
    <div>Build: ${info.build || "-"}</div>
  `;
}

function renderServices() {
  const summary = state.servicesSummary;
  if (!state.scanned || !summary) {
    elements.servicesSummary.textContent = "Scan to load services.";
    elements.servicesList.textContent = "No data.";
    return;
  }
  elements.servicesSummary.innerHTML = `
    <div>Total services: ${summary.total}</div>
    <div>Running: ${summary.running}</div>
    <div>Stopped: ${summary.stopped}</div>
    <div>Disabled: ${summary.disabled ?? "-"}</div>
  `;

  elements.servicesList.innerHTML = "";
  if (!state.servicesRunning.length) {
    elements.servicesList.textContent = "No running services reported.";
    return;
  }

  const filter = (elements.servicesFilter?.value || "").toLowerCase();
  const filtered = state.servicesRunning.filter((service) => {
    if (!filter) return true;
    return (
      service.display_name?.toLowerCase().includes(filter) ||
      service.name?.toLowerCase().includes(filter)
    );
  });

  if (!filtered.length) {
    elements.servicesList.textContent = "No services match that filter.";
    return;
  }

  filtered.forEach((service) => {
    const row = document.createElement("div");
    row.className = "service-item";
    row.innerHTML = `
      <div class="service-name">${service.display_name || service.name}</div>
      <div class="service-meta">${service.name} :: ${service.start_mode || "-"}</div>
    `;
    elements.servicesList.appendChild(row);
  });
}

function renderTable(tableEl, rules) {
  tableEl.innerHTML = "";
  if (!rules.length) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='6' class='muted'>No rules loaded.</td>";
    tableEl.appendChild(row);
    return;
  }

  rules.forEach((rule) => {
    const row = document.createElement("tr");
    const checked = state.selected.has(rule.id) ? "checked" : "";
    const disabled = state.scanned ? "" : "disabled";
    row.innerHTML = `
      <td><input type="checkbox" data-rule-id="${rule.id}" ${checked} ${disabled} /></td>
      <td>${rule.title}</td>
      <td>${riskBadge(rule.risk)}</td>
      <td>${typeBadge(rule.type)}</td>
      <td title="${rule.details || ""}">${statusBadge(rule.status)}</td>
      <td title="${rule.notes || ""}">${rule.notes || ""}</td>
    `;
    tableEl.appendChild(row);
  });

  tableEl.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", (event) => {
      const id = event.target.getAttribute("data-rule-id");
      if (event.target.checked) {
        state.selected.add(id);
      } else {
        state.selected.delete(id);
      }
      syncCheckboxes(id, event.target.checked);
    });
  });
}

function syncCheckboxes(id, checked) {
  qsa(`input[data-rule-id='${id}']`).forEach((input) => {
    input.checked = checked;
  });
}

function getFilteredRules(rules) {
  const query = (elements.rulesSearch?.value || "").trim().toLowerCase();
  if (!query) return rules;
  return rules.filter((rule) => {
    return (
      rule.id?.toLowerCase().includes(query) ||
      rule.title?.toLowerCase().includes(query) ||
      rule.notes?.toLowerCase().includes(query)
    );
  });
}

function renderRules() {
  const filtered = getFilteredRules(state.rules);
  renderTable(elements.rulesTable, filtered);
  const recommended = filtered.filter((rule) => rule.risk === "LOW");
  const advanced = filtered.filter((rule) => rule.risk !== "LOW");
  renderTable(elements.recommendedTable, recommended);
  renderTable(elements.advancedTable, advanced);
  if (elements.statRules) {
    elements.statRules.textContent = state.rules.length.toString();
  }
}

function renderPlanSummary(plan) {
  if (!plan || !plan.plan) {
    elements.planSummary.textContent = "No plan yet.";
    return;
  }
  const actionLabel = plan.action === "enable" ? "Enable" : "Disable";
  const counts = plan.plan.reduce(
    (acc, item) => {
      if (item.action === "apply") acc.apply += 1;
      if (item.action === "skip") acc.skip += 1;
      if (item.action === "skip_not_found") acc.notfound += 1;
      return acc;
    },
    { apply: 0, skip: 0, notfound: 0 }
  );
  elements.planSummary.innerHTML = `
    <div>Action: ${actionLabel}</div>
    <div>Apply: ${counts.apply}</div>
    <div>Skip: ${counts.skip}</div>
    <div>Not found: ${counts.notfound}</div>
  `;
}

function getSummaryCounts(summary) {
  return {
    success: Number(summary?.success || 0),
    failed: Number(summary?.failed || 0),
    skipped: Number(summary?.skipped || 0),
    skippedNotFound: Number(summary?.skipped_not_found || 0),
  };
}

function getAlreadyMessage(action, counts) {
  if (counts.skipped <= 0) return null;
  const message =
    action === "enable"
      ? "This feature has been enabled already."
      : "This feature has been disabled already.";
  const allSkipped = counts.success === 0 && counts.failed === 0;
  return { message, allSkipped };
}

function getRuleTitle(id) {
  const rule = state.rules.find((item) => item.id === id);
  return rule?.title || id;
}

function translateApplyError(error) {
  if (!error) return "Could not apply the change.";
  const lowered = error.toLowerCase();
  if (lowered.includes("post-check not enabled")) {
    return "After enabling, the status is still not Enabled.";
  }
  if (lowered.includes("post-check not disabled")) {
    return "After disabling, the status is still not Disabled.";
  }
  if (lowered.includes("service still running")) {
    return "The service is still running.";
  }
  if (lowered.includes("task still running")) {
    return "The task is still running.";
  }
  if (lowered.includes("registry value not set correctly")) {
    return "Failed to write the registry value.";
  }
  if (lowered.includes("registry value type mismatch")) {
    return "Registry value type mismatch.";
  }
  if (lowered.includes("registry key not found")) {
    return "Registry key not found.";
  }
  if (lowered.includes("access is denied")) {
    return "Access denied when applying the change.";
  }
  return error;
}

function getFailureMessages(data) {
  const failures = (data?.results || []).filter(
    (item) => item.status === "Failed"
  );
  if (!failures.length) return [];
  return failures.map((failure) => {
    const title = getRuleTitle(failure.id);
    const details = failure.results || [];
    const errorEntry = details.find((item) => item.status === "Error");
    if (errorEntry?.error) {
      const reason = translateApplyError(errorEntry.error);
      const target = errorEntry.target ? ` (${errorEntry.target})` : "";
      return `${title}: ${reason}${target}`;
    }
    const postCheck = details.find((item) => item.status === "PostCheck");
    const actual = postCheck?.detail?.status;
    if (actual) {
      const expected = data.action === "enable" ? "Enabled" : "Disabled";
      return `${title}: After apply, status is ${actual} (expected ${expected}).`;
    }
    return `${title}: Could not apply the change.`;
  });
}

function showFailureToasts(data) {
  const messages = getFailureMessages(data);
  if (!messages.length) return;
  const limit = 3;
  messages.slice(0, limit).forEach((message) => {
    showToast(`Failure: ${message}`, "error");
  });
  if (messages.length > limit) {
    showToast(`Failure: ${messages.length - limit} more item(s) failed.`, "error");
  }
}

async function loadHealth() {
  try {
    const data = await fetchJson("/api/health");
    setAdminStatus(data.admin);
    setHealth("Ready");
  } catch (err) {
    setHealth("Error", "error");
  } finally {
    setActionState();
  }
}

async function scanSystem() {
  elements.scanProgress.classList.remove("hidden");
  elements.scanProgress.textContent = "Scanning...";
  setHealth("Scanning");
  try {
    const data = await fetchJson("/api/scan");
    state.rules = data.rules || [];
    state.system = data.system || null;
    state.servicesSummary = data.services_summary || null;
    state.servicesRunning = data.services_running || [];
    state.scanned = true;
    renderSystemInfo();
    renderRules();
    renderServices();
    setActionState();
    if (elements.statRunning && state.servicesSummary) {
      elements.statRunning.textContent = state.servicesSummary.running ?? "-";
    }
    if (elements.statTotal && state.servicesSummary) {
      elements.statTotal.textContent = state.servicesSummary.total ?? "-";
    }
    showToast("Scan completed", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    elements.scanProgress.classList.add("hidden");
    setHealth("Ready");
  }
}

async function dryRun() {
  if (!state.scanned) {
    showToast("Scan first to unlock actions", "error");
    return;
  }
  if (!state.selected.size) {
    showToast("Select at least one rule", "error");
    return;
  }
  elements.scanProgress.classList.remove("hidden");
  elements.scanProgress.textContent = "Planning...";
  try {
    const data = await fetchJson("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selected_actions: Array.from(state.selected),
        mode: "dry_run",
        action: "disable",
      }),
    });
    state.lastPlan = data;
    renderPlanSummary(data);
    showToast("Dry-run ready", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    elements.scanProgress.classList.add("hidden");
  }
}

async function applySelected() {
  if (!state.scanned) {
    showToast("Scan first to unlock actions", "error");
    return;
  }
  if (!state.selected.size) {
    showToast("Select at least one rule", "error");
    return;
  }
  if (!state.admin) {
    showToast("Run as Administrator to apply changes", "error");
    return;
  }
  elements.scanProgress.classList.remove("hidden");
  elements.scanProgress.textContent = "Applying...";
  try {
    const data = await fetchJson("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selected_actions: Array.from(state.selected),
        mode: "apply",
        action: "disable",
      }),
    });
    renderPlanSummary(data);
    const counts = getSummaryCounts(data.summary);
    const already = getAlreadyMessage("disable", counts);
    if (counts.failed > 0) {
      showToast(`Apply completed with ${counts.failed} failed`, "error");
      showFailureToasts(data);
    } else if (already?.allSkipped) {
      showToast(already.message, "info");
    } else {
      showToast("Apply completed", "success");
    }
    if (already && !already.allSkipped && counts.failed === 0) {
      showToast(already.message, "info");
    }
    if (data.log_id) {
      showToast(`Log saved: ${data.log_id}`, "success");
    }
    await scanSystem();
    await loadHistory();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    elements.scanProgress.classList.add("hidden");
  }
}

async function enableSelected() {
  if (!state.scanned) {
    showToast("Scan first to unlock actions", "error");
    return;
  }
  if (!state.selected.size) {
    showToast("Select at least one rule", "error");
    return;
  }
  if (!state.admin) {
    showToast("Run as Administrator to apply changes", "error");
    return;
  }
  elements.scanProgress.classList.remove("hidden");
  elements.scanProgress.textContent = "Enabling...";
  try {
    const data = await fetchJson("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selected_actions: Array.from(state.selected),
        mode: "apply",
        action: "enable",
      }),
    });
    renderPlanSummary(data);
    const counts = getSummaryCounts(data.summary);
    const already = getAlreadyMessage("enable", counts);
    if (counts.failed > 0) {
      showToast(`Enable completed with ${counts.failed} failed`, "error");
      showFailureToasts(data);
    } else if (already?.allSkipped) {
      showToast(already.message, "info");
    } else {
      showToast("Enable completed", "success");
    }
    if (already && !already.allSkipped && counts.failed === 0) {
      showToast(already.message, "info");
    }
    if (data.log_id) {
      showToast(`Log saved: ${data.log_id}`, "success");
    }
    await scanSystem();
    await loadHistory();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    elements.scanProgress.classList.add("hidden");
  }
}

async function rollback() {
  const backupId = elements.rollbackInput.value.trim();
  if (!backupId) {
    showToast("Enter a backup ID", "error");
    return;
  }
  if (!state.admin) {
    showToast("Run as Administrator to rollback", "error");
    return;
  }
  try {
    const data = await fetchJson("/api/rollback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rollback_id: backupId }),
    });
    showToast(`Rollback completed: ${data.backup_id}`, "success");
    await loadHistory();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderBackupList() {
  if (!state.backups.length) {
    elements.backupList.textContent = "No backups yet.";
    return;
  }
  elements.backupList.innerHTML = "";
  state.backups.forEach((item) => {
    const row = document.createElement("div");
    row.className = "list-item";
    row.innerHTML = `
      <div>
        <div><strong>${item.id}</strong></div>
        <div class="muted">${item.created_at || "unknown"}</div>
      </div>
      <button class="btn ghost" data-backup-id="${item.id}">Use</button>
    `;
    row.querySelector("button").addEventListener("click", () => {
      elements.rollbackInput.value = item.id;
      showToast("Rollback ID filled", "success");
    });
    elements.backupList.appendChild(row);
  });
}

function renderLogsList() {
  if (!state.logs.length) {
    elements.logsList.textContent = "No logs yet.";
    return;
  }
  elements.logsList.innerHTML = "";
  state.logs.forEach((item) => {
    const row = document.createElement("div");
    row.className = "list-item";
    const filesText = (item.files || []).join(", ");
    row.innerHTML = `
      <div>
        <div><strong>${item.id}</strong></div>
        <div class="muted">${filesText}</div>
      </div>
      <button class="btn ghost" data-log-id="${item.id}">View</button>
    `;
    row.querySelector("button").addEventListener("click", () => loadLog(item.id));
    elements.logsList.appendChild(row);
  });
}

async function loadHistory() {
  try {
    const data = await fetchJson("/api/history");
    state.backups = data.backups || [];
    state.logs = data.logs || [];
    renderBackupList();
    renderLogsList();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function loadLog(logId) {
  try {
    const data = await fetchJson(`/api/logs/${logId}`);
    elements.logDetail.textContent = JSON.stringify(data.log, null, 2);
    showToast("Log loaded", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function wireActions() {
  qs("#scan-btn")?.addEventListener("click", scanSystem);
  elements.dryrunBtn.addEventListener("click", dryRun);
  elements.applyBtn.addEventListener("click", applySelected);
  elements.enableBtn?.addEventListener("click", enableSelected);
  qs("#rollback-btn")?.addEventListener("click", rollback);
  elements.rulesSearch?.addEventListener("input", renderRules);
  elements.servicesFilter?.addEventListener("input", renderServices);
  elements.rulesSelectAll?.addEventListener("click", () => {
    state.rules.forEach((rule) => state.selected.add(rule.id));
    renderRules();
  });
  elements.rulesClear?.addEventListener("click", () => {
    state.selected.clear();
    renderRules();
  });
}

setupTabs();
wireActions();
loadHealth();
loadHistory();
renderServices();
renderRules();
