from __future__ import annotations

from typing import Any, Dict, Optional

from posthog import Posthog

from .config import settings


class Analytics:
    def __init__(self) -> None:
        self.client: Optional[Posthog] = None
        if settings.posthog_enabled and settings.posthog_api_key:
            self.client = Posthog(settings.posthog_api_key, host=settings.posthog_host)

    def capture(self, distinct_id: str, event: str, properties: Optional[Dict[str, Any]] = None) -> None:
        if not self.client:
            return
        self.client.capture(distinct_id=distinct_id, event=event, properties=properties or {})

    def flush(self) -> None:
        if not self.client:
            return
        try:
            self.client.flush()
        except Exception:
            pass


analytics = Analytics()
