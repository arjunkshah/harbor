"""Central configuration via environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from harbor.integrations import SOLO_DEFAULT_TOOLKITS


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    nebius_api_key: str = ""
    nebius_model: str = "moonshotai/Kimi-K2-Instruct-0905"
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1/"

    composio_api_key: str = ""
    harbor_user_id: str = "harbor-builder-001"

    tavily_api_key: str = ""

    openclaw_gateway_url: str = "http://127.0.0.1:18789"
    openclaw_gateway_token: str = ""

    github_owner: str = ""
    github_repo: str = ""
    slack_channel_id: str = ""
    linear_team_id: str = ""

    harbor_demo: bool = Field(default=False, validation_alias="HARBOR_DEMO")
    harbor_memory_budget: float = Field(default=0.35, validation_alias="HARBOR_MEMORY_BUDGET")
    harbor_max_agent_turns: int = Field(default=12, validation_alias="HARBOR_MAX_AGENT_TURNS")
    harbor_log_level: str = Field(default="INFO", validation_alias="HARBOR_LOG_LEVEL")

    composio_toolkits: str = Field(
        default=",".join(SOLO_DEFAULT_TOOLKITS),
        validation_alias="COMPOSIO_TOOLKITS",
    )
    harbor_coding_agent: str = Field(default="auto", validation_alias="HARBOR_CODING_AGENT")

    @property
    def demo_mode(self) -> bool:
        return self.harbor_demo

    def active_toolkits(self) -> List[str]:
        """Toolkits Harbor will use (configured in COMPOSIO_TOOLKITS)."""
        return [t.strip().lower() for t in self.composio_toolkits.split(",") if t.strip()]

    def wants_toolkit(self, slug: str) -> bool:
        return slug.lower() in self.active_toolkits()

    def slack_configured(self) -> bool:
        return self.wants_toolkit("slack")

    def slack_ready(self) -> bool:
        return bool(self.slack_channel_id.strip())

    def has_nebius(self) -> bool:
        return bool(self.nebius_api_key.strip())

    def has_composio(self) -> bool:
        return bool(self.composio_api_key.strip())

    def has_tavily(self) -> bool:
        return bool(self.tavily_api_key.strip())

    def has_live_stack(self) -> bool:
        return self.has_nebius() and self.has_composio() and self.has_tavily()


@lru_cache
def get_settings() -> Settings:
    return Settings()
