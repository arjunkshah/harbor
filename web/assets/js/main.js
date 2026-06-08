const TERMINAL_LINES = [
  { cls: "dim", text: "$ harbor setup" },
  { cls: "ok", text: "✓ github · linear · gmail connected" },
  { cls: "dim", text: "" },
  { cls: "cmd", text: "$ harbor run \"triage open PRs\"" },
  { cls: "dim", text: "  tavily    competitor + docs search" },
  { cls: "dim", text: "  composio  12 PRs across your account" },
  { cls: "accent", text: "  memory    SuperCompress 62% KV saved" },
  { cls: "dim", text: "  nebius    3 tool calls → 2 actions" },
  { cls: "ok", text: "  saved     .harbor/runs/ + summary" },
  { cls: "dim", text: "" },
  { cls: "cmd", text: "$ harbor run \"plan auth flow\" --plan" },
  { cls: "ok", text: "  plan      → .harbor/plans.json (5 tasks)" },
  { cls: "dim", text: "" },
  { cls: "accent", text: "harbor serve → localhost:8787/dashboard" },
];

function animateTerminal() {
  const body = document.getElementById("terminal-body");
  if (!body) return;
  body.innerHTML = "";
  let delay = 0;
  TERMINAL_LINES.forEach((line, i) => {
    setTimeout(() => {
      const div = document.createElement("div");
      div.className = `term-line ${line.cls}`;
      div.textContent = line.text || "\u00A0";
      div.style.animationDelay = "0ms";
      body.appendChild(div);
    }, delay);
    delay += line.text ? 160 : 60;
  });
}

function setHealthLabel() {
  const el = document.getElementById("health-status");
  if (!el) return;
  if (window.HARBOR_PUBLIC_SITE) {
    el.textContent = "open source · BuilderShip 2026";
    return;
  }
  fetch("/health")
    .then((res) => res.json())
    .then((data) => {
      const live = data.integrations?.nebius && data.integrations?.composio && data.integrations?.tavily;
      el.textContent = data.demo_mode ? "demo mode" : live ? "live stack" : "needs setup";
    })
    .catch(() => {
      el.textContent = "project site — install locally";
    });
}

document.addEventListener("DOMContentLoaded", () => {
  animateTerminal();
  setHealthLabel();
  setInterval(animateTerminal, 14000);
});
