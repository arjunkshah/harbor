/** Base path: /harbor/ on GitHub Pages, / when running harbor serve locally */
(function () {
  const path = window.location.pathname;
  const isGhProject =
    path.startsWith("/harbor/") || path === "/harbor" || path.endsWith("/harbor");
  window.HARBOR_BASE = isGhProject ? "/harbor/" : "/";
  window.HARBOR_PUBLIC_SITE = isGhProject;

  window.harborUrl = function harborUrl(rel) {
    const clean = String(rel || "").replace(/^\//, "");
    if (!clean) return window.HARBOR_BASE;
    if (clean.startsWith("http")) return clean;
    return window.HARBOR_BASE + clean;
  };
})();
