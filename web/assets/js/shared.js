/** Shared nav — public site (GitHub Pages) vs local dashboard (harbor serve) */
function injectNav(active) {
  const el = document.getElementById("nav-links");
  if (!el) return;

  const site = document.body.dataset.site || "public";

  if (site === "local") {
    el.innerHTML = `
      <a href="/dashboard"${active === "dashboard" ? ' class="active"' : ""}>Dashboard</a>
      <a href="/docs">Docs</a>
      <a href="https://github.com/arjunkshah/harbor" target="_blank" rel="noopener">GitHub</a>
      <a href="https://arjunkshah.github.io/harbor/" target="_blank" rel="noopener" class="btn btn-ghost" style="padding:8px 16px;font-size:0.85rem">Project site</a>
    `;
    return;
  }

  const u = window.harborUrl;
  el.innerHTML = `
    <a href="${u("index.html")}"${active === "home" ? ' class="active"' : ""}>Home</a>
    <a href="${u("docs.html")}"${active === "docs" ? ' class="active"' : ""}>Docs</a>
    <a href="https://github.com/arjunkshah/harbor" target="_blank" rel="noopener">GitHub</a>
    <a href="${u("index.html")}#start" class="btn btn-primary" style="padding:8px 16px;font-size:0.85rem">Install</a>
  `;
}

document.addEventListener("DOMContentLoaded", () => injectNav(document.body.dataset.page || ""));
