/** Harbor user dashboard */
let selectedRunId = null;
let running = false;

function fmtTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s || "";
  return d.innerHTML;
}

async function loadStatus() {
  const res = await fetch("/api/dashboard/status");
  if (!res.ok) throw new Error("Start the local server: harbor serve");
  return res.json();
}

async function loadRuns() {
  const res = await fetch("/api/dashboard/runs?limit=30");
  if (!res.ok) return { runs: [] };
  return res.json();
}

function renderChecks(checks) {
  const el = document.getElementById("status-checks");
  if (!el) return;
  el.innerHTML = checks
    .map(
      (c) => `
    <div class="status-row">
      <div class="status-left">
        <span class="status-dot ${c.ok ? "ok" : "fail"}"></span>
        ${esc(c.name)}
      </div>
      <span style="color:var(--text-muted);font-size:0.78rem">${esc(c.detail)}</span>
    </div>`
    )
    .join("");
}

function renderConfig(config) {
  const el = document.getElementById("config-panel");
  if (!el) return;
  const k = config.keys || {};
  el.innerHTML = `
    <div class="status-row"><span>Mode</span><span>${config.demo_mode ? "Demo" : "Live"}</span></div>
    <div class="status-row"><span>Nebius</span><span>${k.nebius ? "✓ " + esc(config.masked?.NEBIUS_API_KEY) : "✗ not set"}</span></div>
    <div class="status-row"><span>Composio</span><span>${k.composio ? "✓ " + esc(config.masked?.COMPOSIO_API_KEY) : "✗ not set"}</span></div>
    <div class="status-row"><span>Tavily</span><span>${k.tavily ? "✓ " + esc(config.masked?.TAVILY_API_KEY) : "✗ not set"}</span></div>
    <div class="status-row"><span>GitHub</span><span>${
      config.github_owner && config.github_repo
        ? esc(config.github_owner) + "/" + esc(config.github_repo)
        : "Whole account (OAuth)"
    }</span></div>
    <div class="status-row"><span>User ID</span><span style="font-family:var(--mono);font-size:0.78rem">${esc(config.harbor_user_id)}</span></div>
  `;
}

function renderStats(stats) {
  document.getElementById("stat-runs").textContent = stats.total_runs ?? 0;
  document.getElementById("stat-kv").textContent = (stats.avg_memory_savings ?? 0) + "%";
  document.getElementById("stat-slack").textContent = stats.slack_posts ?? 0;
  document.getElementById("stat-linear").textContent = stats.linear_tickets ?? 0;
}

function renderRuns(runs) {
  const el = document.getElementById("run-list");
  if (!runs.length) {
    el.innerHTML = `<div class="empty-state"><p>No runs yet.</p><p>Trigger a morning brief or run <code>harbor brief</code> in terminal.</p></div>`;
    return;
  }
  el.innerHTML = runs
    .map(
      (r) => `
    <div class="run-card ${r.id === selectedRunId ? "active" : ""}" data-id="${r.id}">
      <div class="run-card-head">
        <span class="run-tag ${r.workflow === "incident_commander" ? "incident" : ""}">${esc(r.workflow?.replace("_", " "))}</span>
        <span class="run-time">${fmtTime(r.created_at)}</span>
      </div>
      <div class="run-preview">${esc((r.summary || "").slice(0, 160))}</div>
      <div class="run-meta">
        <span>KV −${Number(r.memory_savings_pct || 0).toFixed(0)}%</span>
        <span>${(r.actions_taken || []).length} actions</span>
      </div>
    </div>`
    )
    .join("");

  el.querySelectorAll(".run-card").forEach((card) => {
    card.addEventListener("click", () => showRunDetail(card.dataset.id, runs));
  });

  if (!selectedRunId && runs[0]) showRunDetail(runs[0].id, runs);
}

function showRunDetail(id, runs) {
  selectedRunId = id;
  const r = runs.find((x) => x.id === id);
  if (!r) return;
  document.querySelectorAll(".run-card").forEach((c) => {
    c.classList.toggle("active", c.dataset.id === id);
  });
  const el = document.getElementById("run-detail");
  const turns = (r.turns || [])
    .map((t) => `<div><span>${esc(t.phase)}</span> ${esc(t.detail)}</div>`)
    .join("");
  el.innerHTML = `
    <h3>${esc(r.workflow?.replace("_", " "))} · ${fmtTime(r.created_at)}</h3>
    <div class="detail-summary">${esc(r.summary || "No summary")}</div>
    <div class="run-meta" style="margin-top:16px">
      <span>Memory saved: ${Number(r.memory_savings_pct || 0).toFixed(1)}%</span>
      <span>Slack: ${r.posted_to_slack ? "yes" : "no"}</span>
      <span>Linear: ${r.linear_tickets_created || 0}</span>
    </div>
    ${turns ? `<div class="turn-log">${turns}</div>` : ""}
  `;
}

function setRunning(on, label) {
  running = on;
  document.getElementById("btn-brief").disabled = on;
  document.getElementById("btn-incident").disabled = on;
  document.getElementById("run-status").textContent = on ? label : "";
}

async function refresh() {
  try {
    const status = await loadStatus();
    renderChecks(status.checks || []);
    renderConfig(status.config || {});
    renderStats(status.stats || {});

    const setupBanner = document.getElementById("setup-banner");
    const cfg = status.config || {};
    const live = cfg.keys?.nebius && cfg.keys?.composio && cfg.keys?.tavily && !cfg.demo_mode;
    if (setupBanner) {
      setupBanner.style.display = live ? "none" : "block";
    }
  } catch (e) {
    const banner = document.getElementById("setup-banner");
    if (banner) {
      banner.innerHTML = `
      <div class="alert alert-warn">
        ${esc(e.message)}<br><br>
        <code>cd harbor && source .venv/bin/activate && harbor serve</code>
        then open <a href="http://127.0.0.1:8787/dashboard">localhost:8787/dashboard</a>
        · <a href="docs.html#setup">setup docs</a>
      </div>`;
    }
  }

  const { runs } = await loadRuns();
  renderRuns(runs);
}

async function runBrief() {
  if (running) return;
  setRunning(true, "Running morning brief…");
  try {
    const company = document.getElementById("brief-company").value || "Composio";
    const focus = document.getElementById("brief-focus").value || "AI agents";
    const res = await fetch("/api/dashboard/brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company, focus }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Brief failed");
    selectedRunId = data.run_id;
    await refresh();
    if (data.run_id) {
      const { runs } = await loadRuns();
      showRunDetail(data.run_id, runs);
    }
  } catch (e) {
    alert(e.message);
  } finally {
    setRunning(false, "");
  }
}

async function runIncident() {
  if (running) return;
  const query = document.getElementById("incident-query").value.trim();
  if (!query) {
    alert("Describe the incident first.");
    return;
  }
  setRunning(true, "Running incident commander…");
  try {
    const service = document.getElementById("incident-service").value || "production API";
    const res = await fetch("/api/dashboard/incident", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, service }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Incident run failed");
    selectedRunId = data.run_id;
    await refresh();
  } catch (e) {
    alert(e.message);
  } finally {
    setRunning(false, "");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-brief")?.addEventListener("click", runBrief);
  document.getElementById("btn-incident")?.addEventListener("click", runIncident);
  document.getElementById("btn-refresh")?.addEventListener("click", refresh);
  refresh();
  setInterval(refresh, 30000);
});
