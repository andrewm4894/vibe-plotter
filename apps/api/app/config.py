from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "gpt-4o-mini"

    posthog_enabled: bool = False
    posthog_api_key: str | None = None
    posthog_host: str = "https://us.i.posthog.com"

    session_secret: str = "dev"
    max_csv_bytes: int = 10_000_000
    allowed_csv_hosts: str | None = None
    web_origin: str = "http://localhost:3000"
    llm_disabled: bool = False
    debug: bool = False

    @property
    def allowed_hosts_set(self) -> set[str] | None:
        if not self.allowed_csv_hosts:
            return None
        return {host.strip().lower() for host in self.allowed_csv_hosts.split(",") if host.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
