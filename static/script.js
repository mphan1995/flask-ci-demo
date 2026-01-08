const form = document.querySelector("#analyze-form");
const pipelineInput = document.querySelector("#pipeline-name");
const buildInput = document.querySelector("#build-id");
const providerSelect = document.querySelector("#provider");
const logText = document.querySelector("#log-text");
const logStats = document.querySelector("#log-stats");
const statusEl = document.querySelector("#status");
const analyzeBtn = document.querySelector("#analyze-btn");
const sampleBtn = document.querySelector("#load-sample");
const clearBtn = document.querySelector("#clear-form");
const fileInput = document.querySelector("#log-file");
const resultPanel = document.querySelector("#result-panel");
const rootCauseEl = document.querySelector("#result-root-cause");
const stageEl = document.querySelector("#result-stage");
const originStepEl = document.querySelector("#result-origin-step");
const failureSurfaceEl = document.querySelector("#result-failure-surface");
const eventsEl = document.querySelector("#result-events");
const confidenceEl = document.querySelector("#result-confidence");
const confidenceBar = document.querySelector("#confidence-bar");
const evidenceList = document.querySelector("#evidence-list");
const timelineList = document.querySelector("#timeline-list");
const reportEl = document.querySelector("#report-markdown");

const setStatus = (message, type = "neutral") => {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
};

const setLoading = (loading) => {
  analyzeBtn.disabled = loading;
  analyzeBtn.textContent = loading ? "Analyzing..." : "Analyze logs";
};

const renderList = (element, items, emptyText) => {
  element.innerHTML = "";
  if (!items || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = emptyText;
    element.appendChild(li);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    element.appendChild(li);
  });
};

const updateStats = () => {
  const value = logText.value || "";
  const trimmed = value.trim();
  const lines = trimmed ? trimmed.split(/\r?\n/).length : 0;
  const chars = value.length;
  logStats.textContent = `${lines} lines | ${chars} chars`;
};

const renderResult = (data) => {
  rootCauseEl.textContent = data.root_cause || "UNKNOWN";
  stageEl.textContent = data.stage_name || "UNKNOWN";
  originStepEl.textContent = data.origin_step || "UNKNOWN";
  failureSurfaceEl.textContent = data.failure_surface || "UNKNOWN";
  eventsEl.textContent = data.event_count || 0;

  const confidencePct = Math.round((data.confidence || 0) * 100);
  confidenceEl.textContent = `${confidencePct}%`;
  confidenceBar.style.width = `${confidencePct}%`;

  renderList(evidenceList, data.evidence, "No clear evidence yet.");
  renderList(timelineList, data.timeline, "No context timeline yet.");
  reportEl.textContent = data.report_markdown || "(No report yet)";

  resultPanel.classList.remove("hidden");
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setLoading(true);
  setStatus("Analyzing logs...", "neutral");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pipeline_name: pipelineInput.value,
        build_id: buildInput.value,
        provider: providerSelect.value,
        log_text: logText.value
      })
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unable to analyze logs.");
    }

    renderResult(payload);
    setStatus("Analysis complete.", "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    setLoading(false);
  }
});

sampleBtn.addEventListener("click", async () => {
  setStatus("Loading sample log...", "neutral");
  try {
    const response = await fetch("/api/sample-log");
    if (!response.ok) {
      throw new Error("Unable to load sample log.");
    }
    const text = await response.text();
    logText.value = text;
    updateStats();
    setStatus("Sample log loaded.", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
});

clearBtn.addEventListener("click", () => {
  logText.value = "";
  updateStats();
  setStatus("Log content cleared.", "neutral");
});

fileInput.addEventListener("change", (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    logText.value = reader.result || "";
    updateStats();
    setStatus(`Loaded ${file.name}.`, "success");
  };
  reader.onerror = () => {
    setStatus("Unable to read log file.", "error");
  };
  reader.readAsText(file);
});

window.addEventListener("load", () => {
  document.body.classList.add("ready");
  updateStats();
});
