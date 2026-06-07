const TERMINAL_LINES = [
  { cls: "t-dim", text: "$ harbor doctor" },
  { cls: "t-ok", text: "✓ SuperCompress memory   Learned Policy active" },
  { cls: "t-ok", text: "✓ Tavily search          4 hits" },
  { cls: "t-ok", text: "✓ Composio toolkits      GitHub · Slack · Linear · Gmail" },
  { cls: "t-ok", text: "✓ Nebius inference       Token Factory ready" },
  { cls: "t-ok", text: "✓ OpenClaw skill         webhook bridge :8787" },
  { cls: "t-dim", text: "" },
  { cls: "t-prompt", text: "$ harbor brief" },
  { cls: "t-dim", text: "  tavily    Multi-query market research" },
  { cls: "t-dim", text: "  composio  GitHub + Linear + Gmail gather" },
  { cls: "t-warn", text: "  memory    SuperCompress 1150→402 tokens (65% KV saved)" },
  { cls: "t-dim", text: "  nebius    Inference + tool loop" },
  { cls: "t-ok", text: "  composio  → Slack digest posted" },
  { cls: "t-ok", text: "  composio  → Linear ticket ENG-231 created" },
  { cls: "t-dim", text: "" },
  { cls: "t-prompt", text: "Brief ready. ☕ Go build." },
];

function animateTerminal() {
  const body = document.getElementById("terminal-body");
  if (!body) return;
  body.innerHTML = "";
  let delay = 0;
  TERMINAL_LINES.forEach((line, i) => {
    setTimeout(() => {
      const div = document.createElement("div");
      div.className = `t-line ${line.cls}`;
      div.textContent = line.text || "\u00A0";
      div.style.animationDelay = "0ms";
      body.appendChild(div);
    }, delay);
    delay += line.text ? 180 : 80;
  });
}

async function fetchHealth() {
  const el = document.getElementById("health-status");
  if (!el) return;
  try {
    const res = await fetch("/health");
    const data = await res.json();
    const live = data.integrations?.nebius && data.integrations?.composio && data.integrations?.tavily;
    el.textContent = data.demo_mode
      ? "demo mode — add API keys for live stack"
      : live
        ? "live stack connected"
        : "partial — check .env keys";
    el.style.color = live && !data.demo_mode ? "#28c840" : "#8ba3b8";
  } catch {
    el.textContent = "run harbor serve for live status";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  animateTerminal();
  fetchHealth();
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
