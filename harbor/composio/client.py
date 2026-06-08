"""Composio integration — GitHub, Slack, Linear, Gmail action layer."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from harbor.config import Settings, get_settings


@dataclass
class ComposioActionResult:
    action: str
    success: bool
    data: Any
    error: Optional[str] = None


@dataclass
class GitHubSnapshot:
    prs_needing_review: List[Dict[str, Any]] = field(default_factory=list)
    open_issues: List[Dict[str, Any]] = field(default_factory=list)
    recent_commits: List[Dict[str, Any]] = field(default_factory=list)

    def to_context_block(self) -> str:
        lines = ["## GitHub (Composio)"]
        if self.prs_needing_review:
            lines.append("\n### PRs needing your review")
            for pr in self.prs_needing_review[:10]:
                lines.append(
                    f"- #{pr.get('number')} {pr.get('title')} — {pr.get('html_url', pr.get('url', ''))}"
                )
        if self.open_issues:
            lines.append("\n### Open issues")
            for issue in self.open_issues[:10]:
                lines.append(f"- #{issue.get('number')} {issue.get('title')}")
        if self.recent_commits:
            lines.append("\n### Recent commits (across your repos)")
            for c in self.recent_commits[:8]:
                repo = c.get("_repo", c.get("repository", {}).get("full_name", ""))
                msg = c.get("message", c.get("commit", {}).get("message", ""))[:80]
                prefix = f"[{repo}] " if repo else ""
                lines.append(f"- {c.get('sha', '')[:7]} {prefix}{msg}")
        return "\n".join(lines) if len(lines) > 1 else "## GitHub\nNo data."


@dataclass
class LinearSnapshot:
    blocked: List[Dict[str, Any]] = field(default_factory=list)
    in_progress: List[Dict[str, Any]] = field(default_factory=list)
    urgent: List[Dict[str, Any]] = field(default_factory=list)

    def to_context_block(self) -> str:
        lines = ["## Linear (Composio)"]
        for label, items in [
            ("Blocked", self.blocked),
            ("In Progress", self.in_progress),
            ("Urgent", self.urgent),
        ]:
            if items:
                lines.append(f"\n### {label}")
                for item in items[:8]:
                    lines.append(f"- {item.get('identifier', item.get('id', '?'))} {item.get('title', '')}")
        return "\n".join(lines) if len(lines) > 1 else "## Linear\nNo data."


@dataclass
class GmailSnapshot:
    unanswered: List[Dict[str, Any]] = field(default_factory=list)
    important: List[Dict[str, Any]] = field(default_factory=list)

    def to_context_block(self) -> str:
        lines = ["## Gmail (Composio)"]
        if self.unanswered:
            lines.append("\n### Unanswered (24h)")
            for m in self.unanswered[:8]:
                lines.append(f"- From: {m.get('from', m.get('sender', '?'))} — {m.get('subject', '')}")
        if self.important:
            lines.append("\n### Important")
            for m in self.important[:5]:
                lines.append(f"- {m.get('subject', '')}")
        return "\n".join(lines) if len(lines) > 1 else "## Gmail\nNo data."


@dataclass
class ComposioGatherResult:
    github: GitHubSnapshot
    linear: LinearSnapshot
    gmail: GmailSnapshot
    raw_actions: List[ComposioActionResult] = field(default_factory=list)

    def all_context_blocks(self) -> List[str]:
        return [
            self.github.to_context_block(),
            self.linear.to_context_block(),
            self.gmail.to_context_block(),
        ]


class ComposioHub:
    """Session-based Composio hub with multi-toolkit gather + execute."""

    TOOLKITS = ["github", "slack", "linear", "gmail"]

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._composio = None
        self._session = None
        self._tools_cache: Optional[List[Dict[str, Any]]] = None

    @property
    def composio(self):
        if self._composio is None:
            import os

            from composio import Composio
            from composio_openai import OpenAIProvider

            if self.settings.composio_api_key:
                os.environ.setdefault("COMPOSIO_API_KEY", self.settings.composio_api_key)
            self._composio = Composio(provider=OpenAIProvider())
        return self._composio

    @property
    def session(self):
        if self._session is None:
            self._session = self.composio.create(user_id=self.settings.harbor_user_id)
        return self._session

    def get_openai_tools(self, toolkits: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if self._tools_cache is not None:
            return self._tools_cache
        kits = toolkits or self.settings.composio_toolkits
        tools = self.composio.tools.get(
            user_id=self.settings.harbor_user_id,
            toolkits=kits,
            limit=100,
        )
        self._tools_cache = tools
        return tools

    def execute(self, action: str, arguments: Dict[str, Any]) -> ComposioActionResult:
        try:
            result = self.composio.tools.execute(
                action,
                user_id=self.settings.harbor_user_id,
                arguments=arguments,
            )
            return ComposioActionResult(action=action, success=True, data=result)
        except Exception as exc:
            return ComposioActionResult(action=action, success=False, data=None, error=str(exc))

    def _safe_list(self, action: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        res = self.execute(action, arguments)
        if not res.success or res.data is None:
            return []
        data = res.data
        if isinstance(data, dict):
            if "data" in data:
                inner = data["data"]
                if isinstance(inner, dict):
                    for key in (
                        "pull_requests", "issues", "items", "issues_list",
                        "messages", "commits", "repositories", "search_results",
                    ):
                        if key in inner and isinstance(inner[key], list):
                            return inner[key]
                    if "response_data" in inner and isinstance(inner["response_data"], list):
                        return inner["response_data"]
                if isinstance(inner, list):
                    return inner
            for key in ("pull_requests", "issues", "items", "messages", "commits", "repositories"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        if isinstance(data, list):
            return data
        return []

    def gather_github(self) -> GitHubSnapshot:
        """Account-wide GitHub via Composio OAuth — optional owner/repo narrows scope."""
        owner = self.settings.github_owner.strip() if self.settings.github_owner else ""
        repo = self.settings.github_repo.strip() if self.settings.github_repo else ""
        snap = GitHubSnapshot()

        if owner and repo:
            prs = self._safe_list(
                "GITHUB_LIST_PULL_REQUESTS",
                {"owner": owner, "repo": repo, "state": "open"},
            )
            snap.prs_needing_review = [p for p in prs if p.get("draft") is not True][:15]
            snap.open_issues = self._safe_list(
                "GITHUB_LIST_REPOSITORY_ISSUES",
                {"owner": owner, "repo": repo, "state": "open"},
            )[:15]
            snap.recent_commits = self._safe_list(
                "GITHUB_LIST_COMMITS",
                {"owner": owner, "repo": repo, "per_page": 10},
            )[:10]
            return snap

        # Whole connected GitHub account (OAuth — no repo config required)
        snap.prs_needing_review = self._safe_list(
            "GITHUB_FIND_PULL_REQUESTS",
            {"q": "is:open is:pr review-requested:@me archived:false", "per_page": 20},
        )[:20]

        snap.open_issues = self._safe_list(
            "GITHUB_FIND_PULL_REQUESTS",
            {"q": "is:open is:issue assignee:@me archived:false", "per_page": 15},
        )[:15]

        repos = self._safe_list(
            "GITHUB_FIND_REPOSITORIES",
            {"q": "sort:updated fork:true", "per_page": 8},
        )
        for r in repos:
            full = r.get("full_name") or r.get("name", "")
            if "/" not in full:
                continue
            o, rn = full.split("/", 1)
            commits = self._safe_list(
                "GITHUB_LIST_COMMITS",
                {"owner": o, "repo": rn, "per_page": 2},
            )
            for c in commits:
                c["_repo"] = full
            snap.recent_commits.extend(commits)
            if len(snap.recent_commits) >= 10:
                break
        snap.recent_commits = snap.recent_commits[:10]
        return snap

    def gather_linear(self) -> LinearSnapshot:
        snap = LinearSnapshot()
        issues = self._safe_list("LINEAR_LIST_LINEAR_ISSUES", {"first": 50})
        for issue in issues:
            state = str(issue.get("state", issue.get("state_name", ""))).lower()
            priority = issue.get("priority", 0)
            if "block" in state or issue.get("blocked"):
                snap.blocked.append(issue)
            elif "progress" in state or "started" in state:
                snap.in_progress.append(issue)
            if priority in (1, "urgent", "Urgent") or issue.get("priority_label") == "Urgent":
                snap.urgent.append(issue)
        return snap

    def gather_gmail(self) -> GmailSnapshot:
        snap = GmailSnapshot()
        messages = self._safe_list(
            "GMAIL_FETCH_EMAILS",
            {"max_results": 20, "query": "is:unread newer_than:1d"},
        )
        snap.unanswered = messages[:15]
        important = self._safe_list(
            "GMAIL_FETCH_EMAILS",
            {"max_results": 10, "query": "is:important newer_than:3d"},
        )
        snap.important = important[:10]
        return snap

    def gather_all(self) -> ComposioGatherResult:
        raw: List[ComposioActionResult] = []
        gh = self.gather_github()
        lin = self.gather_linear()
        gm = self.gather_gmail()
        return ComposioGatherResult(github=gh, linear=lin, gmail=gm, raw_actions=raw)

    def post_slack_digest(self, text: str, channel: Optional[str] = None) -> ComposioActionResult:
        ch = channel or self.settings.slack_channel_id or "general"
        return self.execute(
            "SLACK_SEND_MESSAGE",
            {"channel": ch, "text": text},
        )

    def create_linear_issue(
        self,
        title: str,
        description: str,
        team_id: Optional[str] = None,
    ) -> ComposioActionResult:
        args: Dict[str, Any] = {"title": title, "description": description}
        tid = team_id or self.settings.linear_team_id
        if tid:
            args["team_id"] = tid
        return self.execute("LINEAR_CREATE_LINEAR_ISSUE", args)

    def draft_gmail_reply(self, thread_id: str, body: str) -> ComposioActionResult:
        return self.execute(
            "GMAIL_REPLY_TO_THREAD",
            {"thread_id": thread_id, "message_body": body},
        )

    def create_github_comment(self, owner: str, repo: str, issue_number: int, body: str) -> ComposioActionResult:
        return self.execute(
            "GITHUB_CREATE_ISSUE_COMMENT",
            {"owner": owner, "repo": repo, "issue_number": issue_number, "body": body},
        )

    def auth_connect_url(self, toolkit: str) -> str:
        """Return OAuth connect link for a toolkit."""
        try:
            req = self.composio.connected_accounts.initiate(
                user_id=self.settings.harbor_user_id,
                auth_config_id=toolkit,
            )
            return getattr(req, "redirect_url", str(req))
        except Exception:
            return f"https://app.composio.dev — connect {toolkit} for user {self.settings.harbor_user_id}"

    @property
    def mcp_url(self) -> str:
        return self.session.mcp.url


class DemoComposioHub(ComposioHub):
    """Fixture-backed Composio for demo/CI."""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(settings)
        self._fixture_dir = Path(__file__).resolve().parent.parent.parent / "examples/demo_fixtures"

    def _load(self, name: str) -> Dict[str, Any]:
        return json.loads((self._fixture_dir / name).read_text())

    def gather_github(self) -> GitHubSnapshot:
        data = self._load("github_snapshot.json")
        return GitHubSnapshot(**data)

    def gather_linear(self) -> LinearSnapshot:
        data = self._load("linear_snapshot.json")
        return LinearSnapshot(**data)

    def gather_gmail(self) -> GmailSnapshot:
        data = self._load("gmail_snapshot.json")
        return GmailSnapshot(**data)

    def get_openai_tools(self, toolkits: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "SLACK_SEND_MESSAGE",
                    "description": "Post a message to Slack",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string"},
                            "text": {"type": "string"},
                        },
                        "required": ["channel", "text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "LINEAR_CREATE_LINEAR_ISSUE",
                    "description": "Create a Linear issue",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["title", "description"],
                    },
                },
            },
        ]

    def execute(self, action: str, arguments: Dict[str, Any]) -> ComposioActionResult:
        return ComposioActionResult(action=action, success=True, data={"demo": True, "arguments": arguments})

    def post_slack_digest(self, text: str, channel: Optional[str] = None) -> ComposioActionResult:
        return self.execute("SLACK_SEND_MESSAGE", {"channel": channel or "C-demo", "text": text})

    def create_linear_issue(self, title: str, description: str, team_id: Optional[str] = None) -> ComposioActionResult:
        return self.execute(
            "LINEAR_CREATE_LINEAR_ISSUE",
            {"title": title, "description": description, "team_id": team_id},
        )


def get_composio(settings: Optional[Settings] = None) -> ComposioHub:
    s = settings or get_settings()
    if s.demo_mode or not s.has_composio():
        return DemoComposioHub(s)
    return ComposioHub(s)
