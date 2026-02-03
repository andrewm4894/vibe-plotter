from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class SessionState:
    session_id: str
    df: Optional[pd.DataFrame] = None
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    last_plot: Optional[Dict[str, Any]] = None
    last_code: Optional[str] = None
    last_title: Optional[str] = None
    last_summary: Optional[str] = None


_sessions: Dict[str, SessionState] = {}


def get_or_create_session(session_id: str) -> SessionState:
    if session_id not in _sessions:
        _sessions[session_id] = SessionState(session_id=session_id)
    return _sessions[session_id]


def get_session(session_id: str) -> Optional[SessionState]:
    return _sessions.get(session_id)
