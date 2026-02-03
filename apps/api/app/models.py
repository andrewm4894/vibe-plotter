from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ErrorPayload(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorPayload


class DatasetUCIRequest(BaseModel):
    dataset_id: str = Field(..., examples=["iris"])
    session_id: Optional[str] = None


class DatasetURLRequest(BaseModel):
    url: str
    session_id: Optional[str] = None


class DatasetResponse(BaseModel):
    session_id: str
    dataset_id: Optional[str] = None
    columns: List[str]
    dtypes: Dict[str, str]
    rows: List[Dict[str, Any]]
    row_count: int
    sample_count: int


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    plot_json: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    code: Optional[str] = None


@dataclass
class PlotResult:
    assistant_message: str
    plot_json: Dict[str, Any]
    title: str
    summary: str
    code: str
    model: str | None = None
    provider: str | None = None
    elapsed_ms: int | None = None
