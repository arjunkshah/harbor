const TERMINAL_LINES = [
  { cls: "t-dim", text: "$ harbor setup" },
  { cls: "t-ok", text: "✓ API keys saved to .env" },
  { cls: "t-ok", text: "✓ GitHub connected (whole account)" },
  { cls: "t-dim", text: "" },
  { cls: "t-prompt", text: "$ harbor brief" },
  { cls: "t-dim", text: "  tavily    Market research + company intel" },
  { cls: "t-dim", text: "  composio  GitHub · Linear · Gmail gather" },
  { cls: "t-warn", text: "  memory    SuperCompress 1150→402 tokens (65% KV saved)" },
  { cls: "t-dim", text: "  nebius    Inference + tool loop" },
  { cls: "t-ok", text: "  brief     → .harbor/briefs/latest.md" },
  { cls: "t-dim", text: "" },
  { cls: "t-prompt", text: "Brief ready. ☕ Go build." },
];

function animateTerminal() {
  const body = document.getElementById("terminal-body");
  if (!body) return;
  body.innerHTML = "";
  let delay = 0;
  TERMINAL_LINES.forEach((line) => {
    setTimeout(() => {
      const div = document.createElement("div");
      div.className = `t-line ${line.cls}`;
      div.textContent = line.text || "\u00A0";
      body.appendChild(div);
    }, delay);
    delay += line.text ? 180 : 80;
  });
}

function setHealthLabel() {
  const el = document.getElementById("health-status");
  if (!el) return;
  if (window.HARBOR_PUBLIC_SITE) {
    el.textContent = "open source · BuilderShip 2026";
    el.style.color = "#8ba3b8";
    return;
  }
  fetch("/health")
    .then((res) => res.json())
    .then((data) => {
      const live = data.integrations?.nebius && data.integrations?.composio && data.integrations?.tavily;
      el.textContent = data.demo_mode
        ? "demo mode — run harbor setup for live keys"
        : live
          ? "live stack connected"
          : "partial — check .env keys";
      el.style.color = live && !data.demo_mode ? "#28c840" : "#8ba3b8";
    })
    .catch(() => {
      el.textContent = "project site — install locally to run";
    });
}

document.addEventListener("DOMContentLoaded", () => {
  animateTerminal();
  setHealthLabel();
  setInterval(animateTerminal, 12000);

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) e.target.classList.add("visible");
      });
    },
    { threshold: 0.1 }
  );
  document.querySelectorAll(".card, .stat, .pipe-step").forEach((el) => observer.observe(el));
});
