/** Harbor builder workspace — sidebar dashboard */
let selectedRunId = null;
let running = false;
let lastToolkits = [];
let activeView = "overview";

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

function setView(name) {
  activeView = name;
  document.querySelectorAll(".ws-view").forEach((v) => v.classList.remove("active"));
  document.querySelectorAll(".ws-nav button").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  const el = document.getElementById(`view-${name}`);
  if (el) el.classList.add("active");
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

async function loadPlans() {
  const res = await fetch("/api/dashboard/plans");
  if (!res.ok) return { plans: [] };
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
    meta.textContent = `${active.run_count || 0} runs · ${esc(active.focus || active.company || "")}`;
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
    <div class="int-card">
      <input type="checkbox" class="int-toggle" id="int-${esc(t.slug)}" value="${esc(t.slug)}"${t.enabled ? " checked" : ""} />
      <div class="int-card-body" style="flex:1">
        <label for="int-${esc(t.slug)}"><strong>${esc(t.label)}</strong></label>
        <small>${esc(t.blurb)}</small>
        <div class="int-pills">
          ${t.enabled ? '<span class="int-pill on">enabled</span>' : '<span class="int-pill">off</span>'}
          ${t.connected ? '<span class="int-pill on">oauth linked</span>' : '<span class="int-pill">not connected</span>'}
        </div>
      </div>
      <button type="button" class="ws-btn btn-connect" data-slug="${esc(t.slug)}" style="align-self:center">Connect</button>
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
    <div class="prompt-box">
      <strong style="font-size:0.85rem">${esc(p.label)}</strong>
      <pre>${esc(p.system?.slice(0, 240) || "")}${(p.system?.length || 0) > 240 ? "…" : ""}</pre>
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
  const runs = document.getElementById("stat-runs");
  if (!runs) return;
  runs.textContent = stats.total_runs ?? 0;
  document.getElementById("stat-kv").textContent = (stats.avg_memory_savings ?? 0) + "%";
  document.getElementById("stat-integrations").textContent = (toolkits || []).filter((t) => t.enabled).length;
  document.getElementById("stat-connected").textContent = (toolkits || []).filter((t) => t.connected).length;
}

function renderRuns(runs) {
  const el = document.getElementById("run-list");
  if (!el) return;
  if (!runs.length) {
    el.innerHTML = `<div class="empty">No runs yet. Use Agent or <code>harbor run</code>.</div>`;
    return;
  }
  el.innerHTML = runs
    .map(
      (r) => `
    <div class="run-item ${r.id === selectedRunId ? "active" : ""}" data-id="${r.id}">
      <div class="run-item-head">
        <span class="run-tag">${esc(r.workflow?.replace(/_/g, " "))}</span>
        <span>${fmtTime(r.created_at)}</span>
      </div>
      <div class="run-preview">${esc((r.summary || "").slice(0, 140))}</div>
    </div>`
    )
    .join("");
  el.querySelectorAll(".run-item").forEach((card) => {
    card.addEventListener("click", () => showRunDetail(card.dataset.id, runs));
  });
  if (!selectedRunId && runs[0]) showRunDetail(runs[0].id, runs);
}

function showRunDetail(id, runs) {
  selectedRunId = id;
  const r = runs.find((x) => x.id === id);
  if (!r) return;
  document.querySelectorAll(".run-item").forEach((c) => c.classList.toggle("active", c.dataset.id === id));
  const el = document.getElementById("run-detail");
  const turns = (r.turns || []).map((t) => `<div><span>${esc(t.phase)}</span> ${esc(t.detail)}</div>`).join("");
  el.innerHTML = `
    <span class="ws-panel-title">${esc(r.workflow?.replace(/_/g, " "))} · ${fmtTime(r.created_at)}</span>
    <p style="font-size:0.85rem;color:var(--text-muted);margin:12px 0">Project: ${esc(r.meta?.project_name || "—")}</p>
    <div class="detail-summary">${esc(r.summary || "No summary")}</div>
    <div style="font-size:0.78rem;color:var(--text-faint)">KV −${Number(r.memory_savings_pct || 0).toFixed(1)}% · ${(r.actions_taken || []).length} actions</div>
    ${turns ? `<div class="turn-log">${turns}</div>` : ""}
  `;
}

function renderPlans(plans) {
  const el = document.getElementById("plans-panel");
  if (!el) return;
  if (!plans.length) {
    el.innerHTML = `<div class="empty">No plans yet — Agent → Plan only, or <code>harbor run "…" --plan</code></div>`;
    return;
  }
  el.innerHTML = plans
    .map(
      (p) => `
    <div class="plan-card">
      <strong>${esc(p.title)}</strong>
      <p style="font-size:0.85rem;color:var(--text-muted);margin:8px 0">${esc(p.goal)}</p>
      ${(p.tasks || [])
        .map(
          (t, i) => `
        <label class="plan-task${t.done ? " done" : ""}">
          <input type="checkbox" data-plan="${esc(p.id)}" data-idx="${i}"${t.done ? " checked" : ""} />
          <span>${esc(t.text)}</span>
        </label>`
        )
        .join("")}
    </div>`
    )
    .join("");
  el.querySelectorAll('input[type="checkbox"][data-plan]').forEach((cb) => {
    cb.addEventListener("change", () => togglePlanTask(cb.dataset.plan, Number(cb.dataset.idx)));
  });
}

async function togglePlanTask(planId, idx) {
  await fetch(`/api/dashboard/plans/${planId}/tasks/${idx}`, { method: "PATCH" });
  const { plans } = await loadPlans();
  renderPlans(plans);
}

async function refreshHealth(status) {
  const cfg = status?.config || {};
  const live = cfg.keys?.nebius && cfg.keys?.composio && cfg.keys?.tavily && !cfg.demo_mode;
  const label = cfg.demo_mode ? "demo mode" : live ? "live stack" : "needs setup";
  const health = document.getElementById("health-status");
  const sidebar = document.getElementById("sidebar-status");
  if (health) health.textContent = label;
  if (sidebar) sidebar.textContent = label;
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
        : `<div class="alert alert-warn">Run <code>harbor setup</code> to add API keys and connect integrations.</div>`;
    }

    const { prompts } = await loadPrompts();
    renderPrompts(prompts);
  } catch (e) {
    const banner = document.getElementById("setup-banner");
    if (banner) banner.innerHTML = `<div class="alert alert-warn">${esc(e.message)}</div>`;
  }
  const { runs } = await loadRuns();
  renderRuns(runs);
  const { plans } = await loadPlans();
  renderPlans(plans);
  const build = await loadBuild();
  renderBuild(build);
  await renderAlerts();
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
  flashStatus("Integrations saved");
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

async function loadBuild() {
  const res = await fetch("/api/dashboard/build");
  if (!res.ok) return null;
  return res.json();
}

async function loadAlerts() {
  const res = await fetch("/api/dashboard/alerts?unread=true");
  if (!res.ok) return { alerts: [] };
  return res.json();
}

function renderBuild(st) {
  if (!st) return;
  const proj = st.project || {};
  const q = st.queue || {};
  const set = (id, v) => {
    const el = document.getElementById(id);
    if (el) el.textContent = v;
  };
  set("build-phase", proj.build_phase || "idle");
  set("build-queued", q.queued ?? 0);
  set("build-running", q.running ?? 0);
  set("build-needs", q.needs_you ?? 0);
  set("build-alerts", st.alerts_unread ?? 0);

  const repo = document.getElementById("repo-path");
  if (repo && proj.repo_path && !repo.dataset.touched) repo.value = proj.repo_path;

  const agentsEl = document.getElementById("agents-panel");
  if (agentsEl) {
    agentsEl.innerHTML = (st.agents || [])
      .map(
        (a) =>
          `<p style="font-size:0.85rem;margin-bottom:8px">${a.available ? "✓" : "—"} <strong>${esc(a.label)}</strong> <span style="color:var(--text-faint)">${esc(a.id)}</span></p>`
      )
      .join("");
  }

  const sel = document.getElementById("coding-agent");
  if (sel) {
    const opts = [{ id: "auto", label: "Auto-detect" }, ...(st.agents || []).filter((a) => a.available)];
    sel.innerHTML = opts.map((a) => `<option value="${esc(a.id)}">${esc(a.label || a.id)}</option>`).join("");
    if (proj.coding_agent) sel.value = proj.coding_agent;
  }

  const jobsEl = document.getElementById("build-jobs");
  if (jobsEl) {
    const jobs = st.jobs || [];
    jobsEl.innerHTML = jobs.length
      ? jobs
          .map(
            (j) => `
      <div class="run-item" style="cursor:default">
        <div class="run-item-head"><span class="run-tag">${esc(j.status)}</span><span>${esc(j.agent)} · ${esc(j.phase)}</span></div>
        <div class="run-preview">${esc((j.meta?.title || j.prompt || "").slice(0, 100))}</div>
        ${j.needs_attention ? `<p style="color:var(--accent);font-size:0.78rem;margin-top:6px">${esc(j.attention_reason)}</p>` : ""}
      </div>`
          )
          .join("")
      : `<div class="empty">No coding jobs — ideate &amp; approve to queue</div>`;
  }

  const docsEl = document.getElementById("build-docs");
  if (docsEl && st.docs) {
    const root = st.docs.docs_root || "";
    const files = Object.keys(st.docs.files || {});
    const feats = (st.docs.features || []).join(", ");
    docsEl.textContent = `${root}\n${files.join("\n")}\nfeatures: ${feats}`;
  }

  const syncEl = document.getElementById("sync-panel");
  if (syncEl && st.ecosystem_sync) {
    const es = st.ecosystem_sync;
    const conn = Object.entries(es.connected || {})
      .map(([k, v]) => `${v ? "✓" : "—"} ${k}`)
      .join(" · ");
    const reg = es.registry || {};
    syncEl.innerHTML = `<p>${esc(conn)}</p><p>${reg.total || 0} synced items · auto-sync ${es.auto_sync ? "on" : "off"}</p>`;
  }
}

async function renderAlerts() {
  const { alerts } = await loadAlerts();
  const el = document.getElementById("alerts-panel");
  if (!el) return;
  if (!alerts.length) {
    el.innerHTML = `<p style="font-size:0.85rem;color:var(--text-faint)">No alerts</p>`;
    return;
  }
  el.innerHTML = alerts
    .map(
      (a) => `
    <div class="plan-card" style="margin-bottom:8px">
      <strong>${esc(a.title)}</strong>
      <p style="font-size:0.82rem;color:var(--text-muted);margin-top:6px">${esc(a.message)}</p>
      ${a.needs_you ? '<span style="color:var(--accent);font-size:0.75rem">Needs you</span>' : ""}
    </div>`
    )
    .join("");
}

async function saveRepoPath() {
  const path = document.getElementById("repo-path")?.value.trim();
  const sel = document.getElementById("project-select");
  const pid = sel?.value;
  if (!pid || !path) return;
  await fetch(`/api/dashboard/projects/${pid}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: path }),
  });
}

async function runSyncAll() {
  flashStatus("Syncing to connected tools…");
  const res = await fetch("/api/dashboard/sync", { method: "POST" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Sync failed");
  await refresh();
  flashStatus("Ecosystem sync complete");
}

  const idea = document.getElementById("ideate-input")?.value.trim();
  if (!idea) return alert("Describe your idea");
  flashStatus("Ideating…");
  const res = await fetch("/api/dashboard/build/ideate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Ideate failed");
  await refresh();
  flashStatus("Ideation saved — approve when ready");
}

async function runApprove() {
  await saveRepoPath().catch(() => {});
  const agent = document.getElementById("coding-agent")?.value || "auto";
  flashStatus("Generating PRD & queuing jobs…");
  const res = await fetch("/api/dashboard/build/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent: agent === "auto" ? null : agent }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Approve failed");
  await refresh();
  flashStatus(`${data.jobs_queued} jobs queued`);
}

async function runCodeQueue() {
  await saveRepoPath().catch(() => {});
  const prompt = document.getElementById("code-prompt")?.value.trim();
  if (!prompt) return alert("Enter a prompt");
  const agent = document.getElementById("coding-agent")?.value || "auto";
  const res = await fetch("/api/dashboard/build/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, agent: agent === "auto" ? null : agent }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Queue failed");
  await refresh();
  flashStatus(`Job ${data.job.id} queued`);
}

function flashStatus(msg) {
  const el = document.getElementById("run-status");
  if (!el) return;
  el.textContent = msg;
  setTimeout(() => (el.textContent = ""), 2500);
}

function setRunning(on, label) {
  running = on;
  ["btn-brief", "btn-incident", "btn-agent-run", "btn-agent-plan"].forEach((id) => {
    const b = document.getElementById(id);
    if (b) b.disabled = on;
  });
  if (on) flashStatus(label);
}

async function runAgent(planOnly) {
  if (running) return;
  const query = document.getElementById("agent-query")?.value.trim();
  if (!query) return alert("Describe what Harbor should do");
  setRunning(true, planOnly ? "Planning…" : "Running agent…");
  try {
    const res = await fetch("/api/dashboard/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, plan_only: planOnly }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Agent failed");
    selectedRunId = data.run_id;
    if (planOnly) setView("plans");
    else setView("history");
    await refresh();
    flashStatus(planOnly ? "Plan saved" : "Task complete");
  } catch (e) {
    alert(e.message);
  } finally {
    setRunning(false, "");
  }
}

async function runBrief() {
  if (running) return;
  setRunning(true, "Running morning brief…");
  try {
    const res = await fetch("/api/dashboard/brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company: document.getElementById("brief-company").value,
        focus: document.getElementById("brief-focus").value,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Brief failed");
    selectedRunId = data.run_id;
    setView("history");
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
    const res = await fetch("/api/dashboard/incident", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        service: document.getElementById("incident-service").value,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed");
    selectedRunId = data.run_id;
    setView("history");
    await refresh();
  } catch (e) {
    alert(e.message);
  } finally {
    setRunning(false, "");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".ws-nav button").forEach((btn) => {
    btn.addEventListener("click", () => setView(btn.dataset.view));
  });
  document.getElementById("btn-brief")?.addEventListener("click", runBrief);
  document.getElementById("btn-incident")?.addEventListener("click", runIncident);
  document.getElementById("btn-agent-run")?.addEventListener("click", () => runAgent(false));
  document.getElementById("btn-agent-plan")?.addEventListener("click", () => runAgent(true));
  document.getElementById("btn-refresh")?.addEventListener("click", refresh);
  document.getElementById("btn-save-integrations")?.addEventListener("click", () => saveIntegrations().catch((e) => alert(e.message)));
  document.getElementById("btn-new-project")?.addEventListener("click", () => newProject().catch((e) => alert(e.message)));
  document.getElementById("project-select")?.addEventListener("change", (e) => activateProject(e.target.value).catch((err) => alert(err.message)));
  ["brief-company", "brief-focus"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", (e) => (e.target.dataset.touched = "1"));
  });
  document.getElementById("btn-sync-all")?.addEventListener("click", () => runSyncAll().catch((e) => alert(e.message)));
  document.getElementById("btn-ideate")?.addEventListener("click", () => runIdeate().catch((e) => alert(e.message)));
  document.getElementById("btn-approve")?.addEventListener("click", () => runApprove().catch((e) => alert(e.message)));
  document.getElementById("btn-code-queue")?.addEventListener("click", () => runCodeQueue().catch((e) => alert(e.message)));
  document.getElementById("repo-path")?.addEventListener("change", (e) => (e.target.dataset.touched = "1"));
  refresh();
  setInterval(refresh, 15000);
});
