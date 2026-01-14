import { fetchJson } from "./modules/api.js";
import { qs, showToast } from "./modules/dom.js";
import { riskBadge, statusBadge, typeBadge } from "./modules/badges.js";

const state = {
  services: [],
  rules: [],
  summary: null,
};

const elements = {
  adminStatus: qs("#admin-status"),
  healthStatus: qs("#health-status"),
  progress: qs("#check-progress"),
  serviceIntegrity: qs("#service-integrity"),
  ruleIntegrity: qs("#rule-integrity"),
  serviceTable: qs("#check-service-table"),
  ruleTable: qs("#check-rule-table"),
  serviceSearch: qs("#check-service-search"),
  ruleSearch: qs("#check-rule-search"),
  refreshBtn: qs("#check-refresh"),
  reloadRulesBtn: qs("#check-rules"),
  statTargeted: qs("#stat-targeted"),
  statDisabled: qs("#stat-disabled"),
  statRules: qs("#stat-rules"),
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

function getServiceStatus(service) {
  const startMode = (service.start_mode || "").toLowerCase();
  const hasStart =
    service.start_value !== null && service.start_value !== undefined;
  if (!hasStart && !startMode && service.state === "Unknown") {
    return "NotFound";
  }
  if (service.start_value === 4 || startMode === "disabled") {
    return "Disabled";
  }
  return "Enabled";
}

function renderServiceIntegrity(services) {
  const targeted = services.filter((service) => service.rule_ids?.length);
  const disabled = targeted.filter(
    (service) => getServiceStatus(service) === "Disabled"
  );
  const running = targeted.filter((service) => service.state === "Running");

  if (elements.statTargeted) {
    elements.statTargeted.textContent = targeted.length.toString();
  }
  if (elements.statDisabled) {
    elements.statDisabled.textContent = disabled.length.toString();
  }

  if (!elements.serviceIntegrity) return;
  elements.serviceIntegrity.innerHTML = `
    <div>Targeted: ${targeted.length}</div>
    <div>Disabled: ${disabled.length}</div>
    <div>Running: ${running.length}</div>
  `;
}

function renderRuleIntegrity(rules) {
  const counts = rules.reduce(
    (acc, rule) => {
      const status = (rule.status || "").toLowerCase();
      if (status === "disabled") acc.disabled += 1;
      else if (status === "notfound") acc.notfound += 1;
      else acc.enabled += 1;
      return acc;
    },
    { disabled: 0, enabled: 0, notfound: 0 }
  );
  if (!elements.ruleIntegrity) return;
  elements.ruleIntegrity.innerHTML = `
    <div>Disabled: ${counts.disabled}</div>
    <div>Enabled: ${counts.enabled}</div>
    <div>Not found: ${counts.notfound}</div>
  `;
}

function renderServiceTable() {
  const query = (elements.serviceSearch?.value || "").toLowerCase();
  const services = state.services.filter((service) => service.rule_ids?.length);
  const filtered = services.filter((service) => {
    if (!query) return true;
    return (
      service.name?.toLowerCase().includes(query) ||
      service.display_name?.toLowerCase().includes(query)
    );
  });

  elements.serviceTable.innerHTML = "";
  if (!filtered.length) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='6' class='muted'>No services found.</td>";
    elements.serviceTable.appendChild(row);
    return;
  }

  filtered.forEach((service) => {
    const status = getServiceStatus(service);
    const startValue =
      service.start_value === null || service.start_value === undefined
        ? "-"
        : service.start_value;
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${service.display_name || service.name}</td>
      <td>${statusBadge(status)}</td>
      <td>${statusBadge(service.state || "Unknown")}</td>
      <td>${service.start_mode || "-"}</td>
      <td>${startValue}</td>
      <td title="${service.notes || ""}">${service.notes || ""}</td>
    `;
    elements.serviceTable.appendChild(row);
  });
}

function renderRuleTable() {
  const query = (elements.ruleSearch?.value || "").toLowerCase();
  const filtered = state.rules.filter((rule) => {
    if (!query) return true;
    return (
      rule.id?.toLowerCase().includes(query) ||
      rule.title?.toLowerCase().includes(query) ||
      rule.notes?.toLowerCase().includes(query)
    );
  });

  elements.ruleTable.innerHTML = "";
  if (!filtered.length) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='5' class='muted'>No rules found.</td>";
    elements.ruleTable.appendChild(row);
    return;
  }

  filtered.forEach((rule) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${rule.title}</td>
      <td>${riskBadge(rule.risk)}</td>
      <td>${typeBadge(rule.type)}</td>
      <td title="${rule.details || ""}">${statusBadge(rule.status)}</td>
      <td title="${rule.notes || ""}">${rule.notes || ""}</td>
    `;
    elements.ruleTable.appendChild(row);
  });
}

async function loadHealth() {
  try {
    const data = await fetchJson("/api/health");
    setAdminStatus(data.admin);
    setHealth("Ready");
  } catch (err) {
    setHealth("Error", "error");
  }
}

async function loadRules() {
  const data = await fetchJson("/api/scan");
  state.rules = data.rules || [];
  if (elements.statRules) {
    elements.statRules.textContent = state.rules.length.toString();
  }
  renderRuleIntegrity(state.rules);
  renderRuleTable();
}

async function loadServices() {
  const data = await fetchJson("/api/services");
  state.services = data.services || [];
  state.summary = data.summary || null;
  renderServiceIntegrity(state.services);
  renderServiceTable();
}

async function refreshAll() {
  setProgress("Checking local services...");
  setHealth("Checking");
  try {
    await Promise.all([loadServices(), loadRules()]);
    showToast("Local check updated", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    clearProgress();
    setHealth("Ready");
  }
}

elements.refreshBtn?.addEventListener("click", refreshAll);
elements.reloadRulesBtn?.addEventListener("click", async () => {
  setProgress("Reloading rules...");
  try {
    await loadRules();
    showToast("Rules refreshed", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    clearProgress();
  }
});
elements.serviceSearch?.addEventListener("input", renderServiceTable);
elements.ruleSearch?.addEventListener("input", renderRuleTable);

loadHealth();
refreshAll();
