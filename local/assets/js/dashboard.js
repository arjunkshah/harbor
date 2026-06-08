/** Harbor builder workspace — local dashboard only */
let selectedRunId = null;
let running = false;
let lastToolkits = [];

function fmtTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
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
  if (!res.ok) throw new Error("API unavailable — run harbor serve");
  return res.json();
}

async function loadRuns() {
  const res = await fetch("/api/dashboard/runs?limit=30");
  if (!res.ok) return { runs: [] };
  return res.json();
}

async function loadPrompts() {
  const res = await fetch("/api/dashboard/prompts");
  if (!res.ok) return { prompts: [] };
  return res.json();
}

function renderDiffs(list) {
  const el = document.getElementById("diff-list");
  if (!el || !list) return;
  el.innerHTML = list.map((item) => `<li>${esc(item)}</li>`).join("");
}

function renderProjects(workspace) {
  const sel = document.getElementById("project-select");
  const meta = document.getElementById("project-meta");
  if (!sel) return;
  const projects = workspace?.projects || [];
  const active = workspace?.active_project;
  sel.innerHTML = projects
    .map((p) => `<option value="${esc(p.id)}"${p.id === active?.id ? " selected" : ""}>${esc(p.name)}</option>`)
    .join("");
  if (active && meta) {
    meta.textContent = `${active.run_count || 0} runs · ${esc(active.focus)}`;
    const company = document.getElementById("brief-company");
    const focus = document.getElementById("brief-focus");
    if (company && !company.dataset.touched) company.value = active.company || company.value;
    if (focus && !focus.dataset.touched) focus.value = active.focus || focus.value;
  }
}

function renderIntegrations(toolkits) {
  const el = document.getElementById("integrations-panel");
  if (!el) return;
  lastToolkits = toolkits || [];
  el.innerHTML = lastToolkits
    .map(
      (t) => `
    <div class="int-row">
      <input type="checkbox" class="int-toggle" id="int-${esc(t.slug)}" value="${esc(t.slug)}"${t.enabled ? " checked" : ""} />
      <label for="int-${esc(t.slug)}">
        <strong>${esc(t.label)}</strong>
        <small>${esc(t.blurb)}</small>
        <div class="int-badges">
          ${t.enabled ? '<span class="int-badge on">enabled</span>' : '<span class="int-badge">off</span>'}
          ${t.connected ? '<span class="int-badge on">oauth linked</span>' : '<span class="int-badge">not connected</span>'}
        </div>
      </label>
      <button type="button" class="btn btn-ghost btn-connect" data-slug="${esc(t.slug)}" style="padding:6px 10px;font-size:0.75rem">Connect</button>
    </div>`
    )
    .join("");
  el.querySelectorAll(".btn-connect").forEach((btn) => {
    btn.addEventListener("click", () => connectToolkit(btn.dataset.slug));
  });
}

function renderPrompts(prompts) {
  const el = document.getElementById("prompts-panel");
  if (!el) return;
  el.innerHTML = (prompts || [])
    .map(
      (p) => `
    <div class="prompt-block">
      <h4>${esc(p.label)}</h4>
      <pre>${esc(p.system?.slice(0, 280) || "")}${(p.system?.length || 0) > 280 ? "…" : ""}</pre>
      <pre style="margin-top:8px;color:var(--water-glow)">${esc(p.dynamic_task?.slice(0, 200) || "")}${(p.dynamic_task?.length || 0) > 200 ? "…" : ""}</pre>
    </div>`
    )
    .join("");
}

function renderChecks(checks) {
  const el = document.getElementById("status-checks");
  if (!el) return;
  el.innerHTML = checks
    .map(
      (c) => `
    <div class="status-row">
      <div class="status-left"><span class="status-dot ${c.ok ? "ok" : "fail"}"></span>${esc(c.name)}</div>
      <span style="color:var(--text-muted);font-size:0.78rem">${esc(c.detail)}</span>
    </div>`
    )
    .join("");
}

function renderStatsBlock(stats, toolkits) {
  document.getElementById("stat-runs").textContent = stats.total_runs ?? 0;
  document.getElementById("stat-kv").textContent = (stats.avg_memory_savings ?? 0) + "%";
  const enabled = (toolkits || []).filter((t) => t.enabled).length;
  const connected = (toolkits || []).filter((t) => t.connected).length;
  document.getElementById("stat-integrations").textContent = enabled;
  document.getElementById("stat-connected").textContent = connected;
}

function renderRuns(runs) {
  const el = document.getElementById("run-list");
  if (!runs.length) {
    el.innerHTML = `<div class="empty-state"><p>No runs yet.</p><p>Run a brief or use <code>harbor brief</code>.</p></div>`;
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
        <span>${esc(r.meta?.project_name || "—")}</span>
        <span>KV −${Number(r.memory_savings_pct || 0).toFixed(0)}%</span>
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
  document.querySelectorAll(".run-card").forEach((c) => c.classList.toggle("active", c.dataset.id === id));
  const el = document.getElementById("run-detail");
  const turns = (r.turns || []).map((t) => `<div><span>${esc(t.phase)}</span> ${esc(t.detail)}</div>`).join("");
  const prompt = r.meta?.prompt;
  const promptBlock = prompt
    ? `<div class="prompt-block"><h4>Agent prompt snapshot</h4><pre>${esc(prompt.user_task || "")}</pre></div>`
    : "";
  el.innerHTML = `
    <h3>${esc(r.workflow?.replace("_", " "))} · ${fmtTime(r.created_at)}</h3>
    <p style="font-size:0.85rem;color:var(--text-muted)">Project: ${esc(r.meta?.project_name || "—")}</p>
    <div class="detail-summary">${esc(r.summary || "No summary")}</div>
    ${promptBlock}
    <div class="run-meta" style="margin-top:16px">
      <span>Memory saved: ${Number(r.memory_savings_pct || 0).toFixed(1)}%</span>
      <span>Actions: ${(r.actions_taken || []).length}</span>
    </div>
    ${turns ? `<div class="turn-log">${turns}</div>` : ""}
  `;
}

async function refreshHealth(status) {
  const el = document.getElementById("health-status");
  if (!el || !status) return;
  const cfg = status.config || {};
  const live = cfg.keys?.nebius && cfg.keys?.composio && cfg.keys?.tavily && !cfg.demo_mode;
  el.textContent = cfg.demo_mode ? "demo mode" : live ? "live stack" : "needs setup";
}

async function refresh() {
  try {
    const status = await loadStatus();
    const ws = status.workspace || {};
    renderDiffs(ws.differentiators);
    renderProjects(ws);
    renderIntegrations(status.toolkits);
    renderChecks(status.checks || []);
    renderStatsBlock(status.stats || {}, status.toolkits);
    await refreshHealth(status);
    const tagline = document.getElementById("workspace-tagline");
    if (tagline && ws.tagline) tagline.textContent = ws.tagline;

    const banner = document.getElementById("setup-banner");
    const cfg = status.config || {};
    const live = cfg.keys?.nebius && cfg.keys?.composio && cfg.keys?.tavily && !cfg.demo_mode;
    if (banner) {
      banner.innerHTML = live
        ? ""
        : `<div class="alert alert-info" style="margin-top:24px">Run <code>harbor setup</code> to add API keys and connect integrations.</div>`;
    }

    const { prompts } = await loadPrompts();
    renderPrompts(prompts);
  } catch (e) {
    const banner = document.getElementById("setup-banner");
    if (banner) {
      banner.innerHTML = `<div class="alert alert-warn">${esc(e.message)}</div>`;
    }
  }
  const { runs } = await loadRuns();
  renderRuns(runs);
}

async function saveIntegrations() {
  const enabled = [...document.querySelectorAll(".int-toggle:checked")].map((el) => el.value);
  if (!enabled.length) {
    alert("Enable at least one integration (GitHub recommended).");
    return;
  }
  const res = await fetch("/api/dashboard/integrations", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Save failed");
  renderIntegrations(data.toolkits);
  const { prompts } = await loadPrompts();
  renderPrompts(prompts);
  document.getElementById("run-status").textContent = "Integrations saved";
  setTimeout(() => (document.getElementById("run-status").textContent = ""), 2000);
}

async function connectToolkit(slug) {
  const res = await fetch(`/api/dashboard/integrations/${slug}/connect-url`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Connect failed");
  if (data.already_connected) {
    alert(`${slug} is already connected`);
    return refresh();
  }
  if (data.redirect_url) window.open(data.redirect_url, "_blank");
}

async function activateProject(id) {
  await fetch(`/api/dashboard/projects/${id}/activate`, { method: "POST" });
  await refresh();
}

async function newProject() {
  const name = prompt("Project name?");
  if (!name) return;
  await fetch("/api/dashboard/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  await refresh();
}

function setRunning(on, label) {
  running = on;
  document.getElementById("btn-brief").disabled = on;
  document.getElementById("btn-incident").disabled = on;
  document.getElementById("run-status").textContent = on ? label : "";
}

async function runBrief() {
  if (running) return;
  setRunning(true, "Running morning brief…");
  try {
    const company = document.getElementById("brief-company").value;
    const focus = document.getElementById("brief-focus").value;
    const res = await fetch("/api/dashboard/brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company, focus }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Brief failed");
    selectedRunId = data.run_id;
    await refresh();
  } catch (e) {
    alert(e.message);
  } finally {
    setRunning(false, "");
  }
}

async function runIncident() {
  if (running) return;
  const query = document.getElementById("incident-query").value.trim();
  if (!query) return alert("Describe the incident");
  setRunning(true, "Running incident…");
  try {
    const service = document.getElementById("incident-service").value;
    const res = await fetch("/api/dashboard/incident", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, service }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed");
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
  document.getElementById("btn-save-integrations")?.addEventListener("click", () => saveIntegrations().catch((e) => alert(e.message)));
  document.getElementById("btn-new-project")?.addEventListener("click", () => newProject().catch((e) => alert(e.message)));
  document.getElementById("project-select")?.addEventListener("change", (e) => activateProject(e.target.value).catch((err) => alert(err.message)));
  ["brief-company", "brief-focus"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", (e) => (e.target.dataset.touched = "1"));
  });
  refresh();
  setInterval(refresh, 45000);
});
