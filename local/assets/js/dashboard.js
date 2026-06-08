/** Harbor builder workspace — full management dashboard */
let selectedRunId = null;
let running = false;
let lastToolkits = [];
let activeView = "overview";
let boardColumns = [];
let activeDocTab = "ideation.md";
let refreshTimer = null;

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

function toast(msg, type = "info") {
  const el = document.getElementById("ws-toast");
  if (!el) return;
  el.hidden = false;
  el.className = `ws-toast ws-toast--${type}`;
  el.textContent = msg;
  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(() => {
    el.hidden = true;
  }, 3200);
}

function flashStatus(msg) {
  const el = document.getElementById("run-status");
  if (el) el.textContent = msg;
  toast(msg);
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

async function loadBoard() {
  const res = await fetch("/api/dashboard/board");
  if (!res.ok) return null;
  return res.json();
}

async function loadSettings() {
  const res = await fetch("/api/dashboard/settings");
  if (!res.ok) return { settings: {} };
  return res.json();
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

function renderDiffs(list) {
  const el = document.getElementById("diff-list");
  if (!el || !list) return;
  el.innerHTML = list.map((item) => `<li>${esc(item)}</li>`).join("");
}

function getActiveProjectFromSelect() {
  const sel = document.getElementById("project-select");
  const id = sel?.value;
  if (!id) return null;
  return { id };
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

  if (active) {
    if (meta) {
      meta.textContent = `${active.run_count || 0} runs · phase: ${active.build_phase || "idle"} · ${esc(active.focus || "")}`;
    }
    const fields = {
      "proj-name": active.name,
      "proj-company": active.company,
      "proj-focus": active.focus,
      "proj-repo": active.repo_path,
      "proj-notes": active.notes,
    };
    Object.entries(fields).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el && !el.dataset.touched) el.value = val || "";
    });
    const company = document.getElementById("brief-company");
    const focus = document.getElementById("brief-focus");
    if (company && !company.dataset.touched) company.value = active.company || company.value;
    if (focus && !focus.dataset.touched) focus.value = active.focus || focus.value;
  }
}

const CATEGORY_LABELS = {
  dev: "Development",
  comms: "Communication",
  productivity: "Productivity",
  core: "Core",
};

function renderIntegrations(toolkits) {
  const el = document.getElementById("integrations-panel");
  const summary = document.getElementById("integrations-summary");
  if (!el) return;
  lastToolkits = toolkits || [];
  const enabled = lastToolkits.filter((t) => t.enabled).length;
  const connected = lastToolkits.filter((t) => t.connected).length;
  if (summary) summary.textContent = `${enabled} enabled · ${connected} linked`;

  const groups = {};
  lastToolkits.forEach((t) => {
    const cat = t.category || "core";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(t);
  });

  el.innerHTML = Object.entries(groups)
    .map(
      ([cat, items]) => `
    <div class="int-group">
      <div class="int-group-title">${esc(CATEGORY_LABELS[cat] || cat)}</div>
      ${items
        .map(
          (t) => `
        <div class="int-card">
          <input type="checkbox" class="int-toggle" id="int-${esc(t.slug)}" value="${esc(t.slug)}"${t.enabled ? " checked" : ""} />
          <div class="int-card-body">
            <label for="int-${esc(t.slug)}"><strong>${esc(t.label)}</strong>${t.recommended ? ' <span class="int-rec">recommended</span>' : ""}</label>
            <small>${esc(t.blurb)}</small>
            <div class="int-pills">
              ${t.enabled ? '<span class="int-pill on">enabled</span>' : '<span class="int-pill">off</span>'}
              ${t.connected ? '<span class="int-pill on">oauth linked</span>' : '<span class="int-pill">not connected</span>'}
            </div>
          </div>
          <button type="button" class="ws-btn btn-connect" data-slug="${esc(t.slug)}">Connect</button>
        </div>`
        )
        .join("")}
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
    <details class="prompt-box">
      <summary><strong>${esc(p.label)}</strong></summary>
      <pre>${esc(p.system || "")}</pre>
    </details>`
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
      <span class="status-detail">${esc(c.detail)}</span>
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
  const actions = (r.actions_taken || [])
    .map((a) => `<li>${esc(typeof a === "string" ? a : JSON.stringify(a))}</li>`)
    .join("");
  el.innerHTML = `
    <span class="ws-panel-title">${esc(r.workflow?.replace(/_/g, " "))} · ${fmtTime(r.created_at)}</span>
    <p class="ws-meta" style="margin:12px 0">Project: ${esc(r.meta?.project_name || "—")}</p>
    <div class="detail-summary">${esc(r.summary || "No summary")}</div>
    <div class="ws-meta">KV −${Number(r.memory_savings_pct || 0).toFixed(1)}% · ${(r.actions_taken || []).length} actions</div>
    ${actions ? `<ul class="action-list">${actions}</ul>` : ""}
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
    .map((p) => {
      const done = (p.tasks || []).filter((t) => t.done).length;
      const total = (p.tasks || []).length;
      return `
    <div class="plan-card">
      <div class="plan-card-head">
        <div>
          <strong>${esc(p.title)}</strong>
          <span class="plan-progress">${done}/${total} done</span>
        </div>
        <button type="button" class="ws-btn ws-btn-sm ws-btn-danger plan-delete" data-id="${esc(p.id)}">Delete</button>
      </div>
      <p class="ws-meta" style="margin:8px 0">${esc(p.goal)}</p>
      ${(p.tasks || [])
        .map(
          (t, i) => `
        <label class="plan-task${t.done ? " done" : ""}">
          <input type="checkbox" data-plan="${esc(p.id)}" data-idx="${i}"${t.done ? " checked" : ""} />
          <span>${esc(t.text)}</span>
        </label>`
        )
        .join("")}
    </div>`;
    })
    .join("");

  el.querySelectorAll('input[type="checkbox"][data-plan]').forEach((cb) => {
    cb.addEventListener("change", () => togglePlanTask(cb.dataset.plan, Number(cb.dataset.idx)));
  });
  el.querySelectorAll(".plan-delete").forEach((btn) => {
    btn.addEventListener("click", () => deletePlan(btn.dataset.id));
  });
}

async function togglePlanTask(planId, idx) {
  await fetch(`/api/dashboard/plans/${planId}/tasks/${idx}`, { method: "PATCH" });
  const { plans } = await loadPlans();
  renderPlans(plans);
  const board = await loadBoard();
  renderBoard(board);
}

async function deletePlan(planId) {
  if (!confirm("Delete this plan?")) return;
  await fetch(`/api/dashboard/plans/${planId}`, { method: "DELETE" });
  const { plans } = await loadPlans();
  renderPlans(plans);
  toast("Plan deleted");
}

function renderBoard(data) {
  const el = document.getElementById("board-columns");
  if (!el || !data) return;
  boardColumns = data.columns || [];
  const cards = data.cards || {};
  const colSelect = document.getElementById("modal-card-col");
  if (colSelect) {
    colSelect.innerHTML = boardColumns.map((c) => `<option value="${esc(c.id)}">${esc(c.label)}</option>`).join("");
  }

  el.innerHTML = boardColumns
    .map(
      (col) => `
    <div class="board-col" data-col="${esc(col.id)}">
      <div class="board-col-head">
        <span>${esc(col.label)}</span>
        <span class="board-count">${(cards[col.id] || []).length}</span>
      </div>
      <div class="board-col-body">
      ${(cards[col.id] || [])
        .map(
          (c) => `
        <div class="board-card" data-id="${esc(c.id)}" draggable="true">
          <div class="board-card-top">
            <strong>${esc(c.title)}</strong>
            ${(c.labels || []).map((l) => `<span class="board-label">${esc(l)}</span>`).join("")}
          </div>
          ${c.description ? `<p class="board-desc">${esc(c.description.slice(0, 120))}${c.description.length > 120 ? "…" : ""}</p>` : ""}
          <div class="board-card-foot">
            <span class="ws-meta">${esc(c.source_type)}</span>
            <select class="board-move-select" data-id="${esc(c.id)}">
              ${boardColumns.map((x) => `<option value="${esc(x.id)}"${x.id === col.id ? " selected" : ""}>${esc(x.label)}</option>`).join("")}
            </select>
          </div>
        </div>`
        )
        .join("")}
      </div>
    </div>`
    )
    .join("");

  el.querySelectorAll(".board-card").forEach((card) => {
    card.addEventListener("click", (e) => {
      if (e.target.closest(".board-move-select")) return;
      openCardModal(card.dataset.id, data);
    });
  });
  el.querySelectorAll(".board-move-select").forEach((sel) => {
    sel.addEventListener("change", (e) => {
      e.stopPropagation();
      moveBoardCard(sel.dataset.id, sel.value).catch((err) => toast(err.message, "error"));
    });
  });
  setupBoardDragDrop(el);
}

function setupBoardDragDrop(container) {
  let draggedId = null;
  container.querySelectorAll(".board-card").forEach((card) => {
    card.addEventListener("dragstart", (e) => {
      draggedId = card.dataset.id;
      card.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    });
    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
      draggedId = null;
    });
  });
  container.querySelectorAll(".board-col").forEach((col) => {
    col.addEventListener("dragover", (e) => {
      e.preventDefault();
      col.classList.add("drag-over");
    });
    col.addEventListener("dragleave", () => col.classList.remove("drag-over"));
    col.addEventListener("drop", (e) => {
      e.preventDefault();
      col.classList.remove("drag-over");
      if (draggedId) moveBoardCard(draggedId, col.dataset.col).catch((err) => toast(err.message, "error"));
    });
  });
}

function openCardModal(cardId, boardData) {
  let card = null;
  const cards = boardData?.cards || {};
  for (const col of Object.values(cards)) {
    card = (col || []).find((c) => c.id === cardId);
    if (card) break;
  }
  if (!card) return;
  document.getElementById("modal-card-id").value = card.id;
  document.getElementById("modal-card-title").value = card.title;
  document.getElementById("modal-card-desc").value = card.description || "";
  document.getElementById("modal-card-col").value = card.column;
  document.getElementById("modal-overlay").hidden = false;
}

function closeModal() {
  document.getElementById("modal-overlay").hidden = true;
}

async function saveCardModal() {
  const id = document.getElementById("modal-card-id").value;
  const res = await fetch(`/api/dashboard/board/cards/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: document.getElementById("modal-card-title").value,
      description: document.getElementById("modal-card-desc").value,
      column: document.getElementById("modal-card-col").value,
    }),
  });
  if (!res.ok) throw new Error("Save failed");
  closeModal();
  await refresh();
  toast("Card saved");
}

async function deleteCardModal() {
  const id = document.getElementById("modal-card-id").value;
  if (!confirm("Delete this card?")) return;
  await fetch(`/api/dashboard/board/cards/${id}`, { method: "DELETE" });
  closeModal();
  await refresh();
  toast("Card deleted");
}

async function addBoardCard() {
  const title = prompt("Card title?");
  if (!title?.trim()) return;
  const res = await fetch("/api/dashboard/board/cards", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title.trim(), column: "backlog" }),
  });
  if (!res.ok) throw new Error("Could not create card");
  await refresh();
  toast("Card added");
}

async function moveBoardCard(cardId, column) {
  await fetch(`/api/dashboard/board/cards/${cardId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ column }),
  });
  await refresh();
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

  const badge = document.getElementById("nav-badge-build");
  if (badge) {
    const n = (q.needs_you ?? 0) + (st.alerts_unread ?? 0);
    badge.textContent = n > 0 ? String(n) : "";
    badge.hidden = n <= 0;
  }

  const repo = document.getElementById("repo-path");
  if (repo && proj.repo_path && !repo.dataset.touched) repo.value = proj.repo_path;

  const agentsEl = document.getElementById("agents-panel");
  if (agentsEl) {
    agentsEl.innerHTML = (st.agents || [])
      .map(
        (a) =>
          `<div class="agent-row"><span class="agent-dot ${a.available ? "on" : ""}"></span><strong>${esc(a.label)}</strong><span class="ws-meta">${esc(a.id)}</span></div>`
      )
      .join("") || `<p class="ws-meta">No coding agents detected — install Codex or Claude Code CLI</p>`;
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
      <div class="job-card">
        <div class="run-item-head">
          <span class="run-tag job-status job-status--${esc(j.status)}">${esc(j.status)}</span>
          <span>${esc(j.agent)} · ${esc(j.phase)}</span>
        </div>
        <div class="run-preview">${esc((j.meta?.title || j.prompt || "").slice(0, 120))}</div>
        ${j.needs_attention ? `<p class="job-attention">${esc(j.attention_reason)}</p>` : ""}
        ${j.result_summary ? `<p class="ws-meta">${esc(j.result_summary.slice(0, 100))}</p>` : ""}
      </div>`
          )
          .join("")
      : `<div class="empty">No coding jobs — ideate &amp; approve to queue</div>`;
  }

  renderDocs(st.docs);
  const syncEl = document.getElementById("sync-panel");
  if (syncEl && st.ecosystem_sync) {
    const es = st.ecosystem_sync;
    const conn = Object.entries(es.connected || {})
      .map(([k, v]) => `<span class="sync-chip ${v ? "on" : ""}">${v ? "✓" : "—"} ${esc(k)}</span>`)
      .join("");
    const reg = es.registry || {};
    syncEl.innerHTML = `<div class="sync-chips">${conn}</div><p style="margin-top:8px">${reg.total || 0} synced items · auto-sync ${es.auto_sync ? "on" : "off"}</p>`;
  }
}

function renderDocs(docs) {
  const tabsEl = document.getElementById("doc-tabs");
  const viewer = document.getElementById("build-docs");
  if (!tabsEl || !viewer) return;
  const files = docs?.files || {};
  const names = Object.keys(files);
  if (!names.length) {
    tabsEl.innerHTML = "";
    viewer.textContent = "No docs yet — run Ideate to scaffold docs/harbor/";
    return;
  }
  if (!names.includes(activeDocTab)) activeDocTab = names[0];
  tabsEl.innerHTML = names
    .map((n) => `<button type="button" class="doc-tab${n === activeDocTab ? " active" : ""}" data-doc="${esc(n)}">${esc(n)}</button>`)
    .join("");
  viewer.textContent = files[activeDocTab] || "";
  tabsEl.querySelectorAll(".doc-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      activeDocTab = btn.dataset.doc;
      renderDocs(docs);
    });
  });
}

async function renderAlerts() {
  const { alerts } = await loadAlerts();
  const el = document.getElementById("alerts-panel");
  if (!el) return;
  if (!alerts.length) {
    el.innerHTML = `<p class="ws-meta">No unread alerts</p>`;
    return;
  }
  el.innerHTML = alerts
    .map(
      (a) => `
    <div class="alert-card">
      <div class="alert-card-head">
        <strong>${esc(a.title)}</strong>
        <button type="button" class="ws-btn ws-btn-sm alert-dismiss" data-id="${esc(a.id)}">Dismiss</button>
      </div>
      <p class="ws-meta">${esc(a.message)}</p>
      ${a.needs_you ? '<span class="needs-you">Needs you</span>' : ""}
    </div>`
    )
    .join("");
  el.querySelectorAll(".alert-dismiss").forEach((btn) => {
    btn.addEventListener("click", () => dismissAlert(btn.dataset.id));
  });
}

async function dismissAlert(id) {
  await fetch(`/api/dashboard/alerts/${id}/read`, { method: "PATCH" });
  await refresh();
}

async function dismissAllAlerts() {
  const { alerts } = await loadAlerts();
  await Promise.all(alerts.map((a) => fetch(`/api/dashboard/alerts/${a.id}/read`, { method: "PATCH" })));
  await refresh();
  toast("Alerts dismissed");
}

async function renderSettingsPanel() {
  const { settings } = await loadSettings();
  const mode = document.getElementById("gmail-mode");
  const to = document.getElementById("gmail-to");
  const autoSync = document.getElementById("auto-sync");
  if (mode && settings.gmail_sync_mode) mode.value = settings.gmail_sync_mode;
  if (to && settings.gmail_to) to.value = settings.gmail_to;
  if (autoSync) autoSync.checked = settings.auto_sync !== false;
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
        : `<div class="alert alert-warn">Run <code>harbor setup</code> to add API keys and connect integrations. <button type="button" class="ws-btn ws-btn-sm" data-goto="connect">Open Connect</button></div>`;
      banner.querySelector("[data-goto]")?.addEventListener("click", (e) => setView(e.target.dataset.goto));
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
  const board = await loadBoard();
  renderBoard(board);
  await renderSettingsPanel();
}

async function saveIntegrations() {
  const enabled = [...document.querySelectorAll(".int-toggle:checked")].map((el) => el.value);
  if (!enabled.length) {
    toast("Enable at least one integration", "error");
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
  toast("Integrations saved");
}

async function connectToolkit(slug) {
  const res = await fetch(`/api/dashboard/integrations/${slug}/connect-url`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Connect failed");
  if (data.already_connected) {
    toast(`${slug} is already connected`);
    return refresh();
  }
  if (data.redirect_url) {
    window.open(data.redirect_url, "_blank");
    toast(`Complete ${slug} OAuth in browser — refreshing status…`);
    for (let i = 0; i < 40; i++) {
      await new Promise((r) => setTimeout(r, 3000));
      const r = await fetch("/api/dashboard/integrations/refresh", { method: "POST" });
      const j = await r.json();
      const row = (j.toolkits || []).find((t) => t.slug === slug);
      if (row?.connected) {
        renderIntegrations(j.toolkits);
        toast(`${slug} connected`);
        return;
      }
    }
    await refresh();
    toast(`${slug} — finish OAuth, then click Refresh`, "error");
  }
}

async function activateProject(id) {
  await fetch(`/api/dashboard/projects/${id}/activate`, { method: "POST" });
  document.querySelectorAll("#proj-name, #proj-company, #proj-focus, #proj-repo, #proj-notes").forEach((el) => {
    delete el.dataset.touched;
  });
  await refresh();
  toast("Active project switched");
}

async function saveProject() {
  const sel = document.getElementById("project-select");
  const pid = sel?.value;
  if (!pid) return;
  const body = {
    name: document.getElementById("proj-name")?.value,
    company: document.getElementById("proj-company")?.value,
    focus: document.getElementById("proj-focus")?.value,
    repo_path: document.getElementById("proj-repo")?.value,
    notes: document.getElementById("proj-notes")?.value,
  };
  const res = await fetch(`/api/dashboard/projects/${pid}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Save failed");
  await refresh();
  toast("Project saved");
}

async function newProject() {
  const name = prompt("Project name?");
  if (!name) return;
  await fetch("/api/dashboard/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  document.querySelectorAll("#proj-name, #proj-company, #proj-focus, #proj-repo, #proj-notes").forEach((el) => {
    delete el.dataset.touched;
  });
  await refresh();
  toast("Project created");
}

async function saveSettings() {
  const res = await fetch("/api/dashboard/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      gmail_sync_mode: document.getElementById("gmail-mode")?.value,
      gmail_to: document.getElementById("gmail-to")?.value,
      auto_sync: document.getElementById("auto-sync")?.checked,
    }),
  });
  if (!res.ok) throw new Error("Save failed");
  toast("Settings saved");
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
  toast("Syncing to connected tools…");
  const res = await fetch("/api/dashboard/sync", { method: "POST" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Sync failed");
  await refresh();
  toast("Ecosystem sync complete");
}

async function runIdeate() {
  const idea = document.getElementById("ideate-input")?.value.trim();
  if (!idea) return toast("Describe your idea", "error");
  toast("Ideating…");
  const res = await fetch("/api/dashboard/build/ideate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Ideate failed");
  await refresh();
  toast("Ideation saved — approve when ready");
}

async function runApprove() {
  await saveRepoPath().catch(() => {});
  const agent = document.getElementById("coding-agent")?.value || "auto";
  toast("Generating PRD & queuing jobs…");
  const res = await fetch("/api/dashboard/build/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent: agent === "auto" ? null : agent }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Approve failed");
  await refresh();
  setView("board");
  toast(`${data.jobs_queued} jobs queued`);
}

async function runCodeQueue() {
  await saveRepoPath().catch(() => {});
  const prompt = document.getElementById("code-prompt")?.value.trim();
  if (!prompt) return toast("Enter a prompt", "error");
  const agent = document.getElementById("coding-agent")?.value || "auto";
  const res = await fetch("/api/dashboard/build/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, agent: agent === "auto" ? null : agent }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Queue failed");
  await refresh();
  toast(`Job ${data.job.id} queued`);
}

function setRunning(on, label) {
  running = on;
  ["btn-brief", "btn-incident", "btn-agent-run", "btn-agent-plan", "btn-ideate", "btn-approve"].forEach((id) => {
    const b = document.getElementById(id);
    if (b) b.disabled = on;
  });
  if (on && label) toast(label);
}

async function runAgent(planOnly) {
  if (running) return;
  const query = document.getElementById("agent-query")?.value.trim();
  if (!query) return toast("Describe what Harbor should do", "error");
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
    toast(planOnly ? "Plan saved" : "Task complete");
  } catch (e) {
    toast(e.message, "error");
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
    toast("Brief complete");
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setRunning(false, "");
  }
}

async function runIncident() {
  if (running) return;
  const query = document.getElementById("incident-query").value.trim();
  if (!query) return toast("Describe the incident", "error");
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
    toast("Incident run complete");
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setRunning(false, "");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".ws-nav button").forEach((btn) => {
    btn.addEventListener("click", () => setView(btn.dataset.view));
  });
  document.querySelectorAll("[data-goto]").forEach((btn) => {
    btn.addEventListener("click", () => setView(btn.dataset.goto));
  });

  document.getElementById("btn-brief")?.addEventListener("click", runBrief);
  document.getElementById("btn-incident")?.addEventListener("click", runIncident);
  document.getElementById("btn-agent-run")?.addEventListener("click", () => runAgent(false));
  document.getElementById("btn-agent-plan")?.addEventListener("click", () => runAgent(true));
  document.getElementById("btn-refresh")?.addEventListener("click", () => refresh().then(() => toast("Refreshed")));
  document.getElementById("btn-save-integrations")?.addEventListener("click", () => saveIntegrations().catch((e) => toast(e.message, "error")));
  document.getElementById("btn-refresh-oauth")?.addEventListener("click", () =>
    fetch("/api/dashboard/integrations/refresh", { method: "POST" })
      .then((r) => r.json())
      .then((j) => {
        renderIntegrations(j.toolkits);
        toast("OAuth status refreshed");
      })
      .catch((e) => toast(e.message, "error"))
  );
  document.getElementById("btn-new-project")?.addEventListener("click", () => newProject().catch((e) => toast(e.message, "error")));
  document.getElementById("btn-save-project")?.addEventListener("click", () => saveProject().catch((e) => toast(e.message, "error")));
  document.getElementById("project-select")?.addEventListener("change", (e) => activateProject(e.target.value).catch((err) => toast(err.message, "error")));
  ["brief-company", "brief-focus", "proj-name", "proj-company", "proj-focus", "proj-repo", "proj-notes"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", (e) => (e.target.dataset.touched = "1"));
  });
  document.getElementById("btn-save-settings")?.addEventListener("click", () => saveSettings().catch((e) => toast(e.message, "error")));
  document.getElementById("btn-sync-all")?.addEventListener("click", () => runSyncAll().catch((e) => toast(e.message, "error")));
  document.getElementById("btn-ideate")?.addEventListener("click", () => runIdeate().catch((e) => toast(e.message, "error")));
  document.getElementById("btn-approve")?.addEventListener("click", () => runApprove().catch((e) => toast(e.message, "error")));
  document.getElementById("btn-code-queue")?.addEventListener("click", () => runCodeQueue().catch((e) => toast(e.message, "error")));
  document.getElementById("repo-path")?.addEventListener("change", (e) => (e.target.dataset.touched = "1"));
  document.getElementById("btn-board-add")?.addEventListener("click", () => addBoardCard().catch((e) => toast(e.message, "error")));
  document.getElementById("btn-dismiss-alerts")?.addEventListener("click", () => dismissAllAlerts().catch((e) => toast(e.message, "error")));
  document.getElementById("modal-close")?.addEventListener("click", closeModal);
  document.getElementById("modal-overlay")?.addEventListener("click", (e) => {
    if (e.target.id === "modal-overlay") closeModal();
  });
  document.getElementById("modal-save")?.addEventListener("click", () => saveCardModal().catch((e) => toast(e.message, "error")));
  document.getElementById("modal-delete")?.addEventListener("click", () => deleteCardModal().catch((e) => toast(e.message, "error")));

  refresh();
  setInterval(refresh, 15000);
});
