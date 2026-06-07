/** Shared nav + footer helpers */
function harborNav(active) {
  const links = [
    { href: "/", label: "Home", id: "home" },
    { href: "/docs", label: "Docs", id: "docs" },
    { href: "/dashboard", label: "Dashboard", id: "dashboard" },
    { href: "https://github.com/arjunkshah/harbor", label: "GitHub", external: true },
  ];
  return links
    .map((l) => {
      const cls = active === l.id ? ' class="active"' : "";
      const ext = l.external ? ' target="_blank" rel="noopener"' : "";
      return `<a href="${l.href}"${cls}${ext}>${l.label}</a>`;
    })
    .join("");
}

function injectNav(active) {
  const el = document.getElementById("nav-links");
  if (el) {
    el.innerHTML =
      harborNav(active) +
      ' <a href="/dashboard" class="btn btn-primary" style="padding:8px 16px;font-size:0.85rem">Open dashboard</a>';
  }
}

document.addEventListener("DOMContentLoaded", () => injectNav(document.body.dataset.page || ""));
