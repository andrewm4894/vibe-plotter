from __future__ import annotations

import json
import textwrap
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI

from .config import settings
from .models import AppError, PlotResult

SAFE_BUILTINS = {
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "range": range,
    "list": list,
    "dict": dict,
    "set": set,
    "float": float,
    "int": int,
    "str": str,
}

SYSTEM_PROMPT = """
You are a data visualization agent.

Return a JSON object with keys:
- title: short chart title
- summary: 1-2 sentences describing what the chart shows
- assistant_message: a friendly response to the user (short)
- code: Python code that builds a Plotly figure named `fig`

Constraints for code:
- Use only the variables: df, pd, px, go
- Do not import modules
- Do not read/write files or use network calls
- Assign the final Plotly figure to a variable named `fig`
"""


def _truncate_rows(rows: List[Dict[str, Any]], max_rows: int = 10) -> List[Dict[str, Any]]:
    return rows[:max_rows]


def _build_prompt(df: pd.DataFrame, message: str) -> str:
    sample_rows = df.head(10).to_dict(orient="records")
    payload = {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_rows": _truncate_rows(sample_rows, 10),
        "row_count": int(len(df)),
    }
    return textwrap.dedent(
        f"""
        User request: {message}

        Dataset context:
        {json.dumps(payload, indent=2)}
        """
    ).strip()


def _get_llm_client() -> tuple[Optional[OpenAI], Optional[str]]:
    if settings.llm_disabled:
        return None, None
    if settings.openrouter_api_key:
        return OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url), "openrouter"
    if settings.openai_api_key:
        return OpenAI(api_key=settings.openai_api_key), "openai"
    return None, None


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if "```" in text:
        fence = text.split("```")
        for i in range(len(fence) - 1):
            if fence[i].strip().endswith("json"):
                candidate = fence[i + 1].strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    raise AppError("llm_parse_error", "LLM response was not valid JSON.")


def _run_plot_code(code: str, df: pd.DataFrame) -> go.Figure:
    local_vars: Dict[str, Any] = {"df": df, "pd": pd, "px": px, "go": go}
    exec(code, {"__builtins__": SAFE_BUILTINS}, local_vars)
    fig = local_vars.get("fig")
    if fig is None:
        raise AppError("plot_code_no_fig", "Plot code must define a `fig` variable.")
    if not isinstance(fig, go.Figure):
        try:
            fig = go.Figure(fig)
        except Exception as exc:
            raise AppError("plot_code_invalid_fig", "Plot code did not produce a valid Plotly figure.") from exc
    return fig


def _simple_fallback(df: pd.DataFrame) -> PlotResult:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    title = "Quick look"
    summary = "A fallback chart based on the first available numeric field."
    assistant_message = "I used a quick fallback chart based on the available numeric columns."

    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        fig = px.scatter(df, x=x_col, y=y_col, title=title)
        code = f"fig = px.scatter(df, x='{x_col}', y='{y_col}', title='{title}')"
    elif len(numeric_cols) == 1:
        col = numeric_cols[0]
        fig = px.histogram(df, x=col, title=title)
        code = f"fig = px.histogram(df, x='{col}', title='{title}')"
    else:
        col = df.columns[0]
        counts = df[col].astype(str).value_counts().reset_index()
        counts.columns = [col, "count"]
        fig = px.bar(counts, x=col, y="count", title=title)
        code = (
            "counts = df['{col}'].astype(str).value_counts().reset_index()\n"
            "counts.columns = ['{col}', 'count']\n"
            "fig = px.bar(counts, x='{col}', y='count', title='{title}')"
        ).format(col=col, title=title)

    return PlotResult(
        assistant_message=assistant_message,
        plot_json=fig.to_plotly_json(),
        title=title,
        summary=summary,
        code=code,
        model=None,
    )


def generate_plot(df: pd.DataFrame, message: str) -> PlotResult:
    client, provider = _get_llm_client()
    if not client:
        return _simple_fallback(df)

    prompt = _build_prompt(df, message)

    start = time.time()
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        raise AppError("llm_request_failed", f"LLM request failed: {exc}") from exc

    elapsed_ms = int((time.time() - start) * 1000)
    content = response.choices[0].message.content or ""

    parsed = _extract_json(content)
    code = parsed.get("code")
    if not code:
        raise AppError("llm_missing_code", "LLM response did not include code.")

    fig = _run_plot_code(code, df)
    title = parsed.get("title") or (fig.layout.title.text if fig.layout.title else "Chart")
    summary = parsed.get("summary") or "Chart generated from your dataset."
    assistant_message = parsed.get("assistant_message") or summary

    result = PlotResult(
        assistant_message=assistant_message,
        plot_json=fig.to_plotly_json(),
        title=title,
        summary=summary,
        code=code,
        model=settings.llm_model,
        provider=provider,
        elapsed_ms=elapsed_ms,
    )
    return result
