from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .analytics import analytics
from .config import settings
from .datasets import UCI_DATASETS, load_uci_dataset, preview_dataframe
from .models import AppError, ChatRequest, ChatResponse, DatasetResponse, DatasetUCIRequest, DatasetURLRequest, ErrorResponse
from .plot_agent import generate_plot
from .session_store import get_or_create_session, get_session
from .utils import read_csv_from_url

app = FastAPI(title="Vibe Plotter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    payload = ErrorResponse(error={"code": exc.code, "message": exc.message})
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/datasets/uci", response_model=DatasetResponse)
async def load_uci_dataset_endpoint(request: DatasetUCIRequest) -> DatasetResponse:
    session_id = request.session_id or "demo"
    session = get_or_create_session(session_id)

    df = load_uci_dataset(request.dataset_id)
    session.df = df

    preview = preview_dataframe(df)
    analytics.capture(
        distinct_id=session_id,
        event="dataset_loaded",
        properties={
            "session_id": session_id,
            "dataset_type": "uci",
            "dataset_id": request.dataset_id,
            "row_count": preview["row_count"],
            "column_count": len(preview["columns"]),
            "$ai_session_id": session_id,
        },
    )

    return DatasetResponse(session_id=session_id, dataset_id=request.dataset_id, **preview)


@app.post("/api/datasets/url", response_model=DatasetResponse)
async def load_url_dataset_endpoint(request: DatasetURLRequest) -> DatasetResponse:
    session_id = request.session_id or "demo"
    session = get_or_create_session(session_id)

    df = await read_csv_from_url(request.url)
    session.df = df

    preview = preview_dataframe(df)
    analytics.capture(
        distinct_id=session_id,
        event="dataset_loaded",
        properties={
            "session_id": session_id,
            "dataset_type": "url",
            "source_url": request.url,
            "row_count": preview["row_count"],
            "column_count": len(preview["columns"]),
            "$ai_session_id": session_id,
        },
    )

    return DatasetResponse(session_id=session_id, **preview)


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    session = get_session(request.session_id)
    if not session or session.df is None:
        raise AppError("session_missing_dataset", "Load a dataset before chatting.")

    session.chat_history.append({"role": "user", "content": request.message})
    analytics.capture(
        distinct_id=request.session_id,
        event="chat_message_sent",
        properties={
            "session_id": request.session_id,
            "message_length": len(request.message),
            "$ai_session_id": request.session_id,
        },
    )

    result = generate_plot(session.df, request.message, session_id=request.session_id)

    session.chat_history.append({"role": "assistant", "content": result.assistant_message})
    session.last_plot = result.plot_json
    session.last_code = result.code
    session.last_title = result.title
    session.last_summary = result.summary

    if result.model:
        analytics.capture(
            distinct_id=request.session_id,
            event="llm_call",
            properties={
                "session_id": request.session_id,
                "model": result.model,
                "provider": result.provider,
                "duration_ms": result.elapsed_ms,
                "$ai_span_name": "plot_agent",
                "$ai_session_id": request.session_id,
            },
        )

    analytics.capture(
        distinct_id=request.session_id,
        event="chart_rendered",
        properties={
            "session_id": request.session_id,
            "title": result.title,
            "$ai_session_id": request.session_id,
        },
    )

    return ChatResponse(
        session_id=request.session_id,
        assistant_message=result.assistant_message,
        plot_json=result.plot_json,
        title=result.title,
        summary=result.summary,
        code=result.code,
    )


@app.get("/api/datasets")
async def list_datasets() -> dict:
    return {"datasets": UCI_DATASETS}


@app.on_event("shutdown")
async def shutdown() -> None:
    analytics.flush()
