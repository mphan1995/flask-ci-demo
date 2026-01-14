const STATUS_CLASS = {
  disabled: "status-disabled",
  enabled: "status-enabled",
  notfound: "status-notfound",
  running: "status-running",
  stopped: "status-stopped",
  unknown: "status-unknown",
};

export function statusBadge(label) {
  const key = (label || "").toString().toLowerCase();
  const className = STATUS_CLASS[key] || "status-neutral";
  return `<span class="badge ${className}">${label || "-"}</span>`;
}

export function riskBadge(risk) {
  if (!risk) {
    return `<span class="badge status-neutral">N/A</span>`;
  }
  const normalized = risk.toString().toLowerCase();
  return `<span class="badge risk-${normalized}">${risk}</span>`;
}

export function typeBadge(type) {
  return `<span class="badge type">${type || "-"}</span>`;
}
