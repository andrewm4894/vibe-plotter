"""
Plot agent adapter using the external plot-agent library.

This module provides an adapter between vibe-plotter and the plot-agent library,
managing per-session agents and converting results to the expected format.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import plotly.io as pio

from plot_agent import PlotAgent

from .config import settings
from .models import AppError, PlotResult

logger = logging.getLogger(__name__)

# Per-session agent cache
_agents: Dict[str, PlotAgent] = {}


def _simple_fallback(df: pd.DataFrame) -> PlotResult:
    """Generate a simple fallback chart when the LLM is unavailable or fails."""
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
        plot_json=json.loads(pio.to_json(fig)),
        title=title,
        summary=summary,
        code=code,
        model=None,
    )


def _get_or_create_agent(session_id: str) -> PlotAgent:
    """Get or create a PlotAgent for the given session."""
    if session_id not in _agents:
        # Configure environment for external plot-agent library
        # API key (prefer OpenRouter, fall back to OpenAI)
        if settings.openrouter_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
            os.environ["OPENAI_BASE_URL"] = settings.openrouter_base_url
        elif settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
            os.environ.pop("OPENAI_BASE_URL", None)

        # PostHog configuration
        os.environ["POSTHOG_ENABLED"] = str(settings.posthog_enabled).lower()
        if settings.posthog_api_key:
            os.environ["POSTHOG_API_KEY"] = settings.posthog_api_key
        if settings.posthog_host:
            os.environ["POSTHOG_HOST"] = settings.posthog_host

        # Session tracking
        os.environ["POSTHOG_AI_SESSION_ID"] = session_id
        os.environ["POSTHOG_DISTINCT_ID"] = session_id

        # Determine if we should include plot images for PostHog
        include_plot_image = settings.posthog_enabled

        agent = PlotAgent(
            model=settings.llm_model,
            include_plot_image=include_plot_image,
            debug=settings.debug,
        )
        _agents[session_id] = agent
        logger.info(f"Created new PlotAgent for session {session_id}")

    return _agents[session_id]


def clear_agent(session_id: str) -> None:
    """Clear the agent for a given session."""
    if session_id in _agents:
        del _agents[session_id]
        logger.info(f"Cleared PlotAgent for session {session_id}")


def generate_plot(df: pd.DataFrame, message: str, session_id: str = "default") -> PlotResult:
    """
    Generate a plot using the external plot-agent library.

    Args:
        df: The pandas dataframe to visualize.
        message: The user's plot request.
        session_id: The session ID for agent reuse and PostHog tracking.

    Returns:
        PlotResult with the generated plot and metadata.
    """
    # Check if LLM is disabled
    if settings.llm_disabled:
        return _simple_fallback(df)

    # Check for API key
    if not settings.openai_api_key and not settings.openrouter_api_key:
        logger.warning("No API key configured, using fallback")
        return _simple_fallback(df)

    start = time.time()

    try:
        agent = _get_or_create_agent(session_id)
        agent.set_df(df)

        # Process the message through the agent
        response = agent.process_message(message)
        fig = agent.get_figure()

        if fig is None:
            logger.warning("Agent did not produce a figure, using fallback")
            return _simple_fallback(df)

        elapsed_ms = int((time.time() - start) * 1000)

        # Get metadata from agent
        title = agent.get_plot_title() or "Chart"
        summary = agent.get_plot_summary() or response
        code = agent.generated_code or ""

        # Determine provider based on settings
        provider = "openrouter" if settings.openrouter_api_key else "openai"

        return PlotResult(
            assistant_message=response,
            plot_json=json.loads(pio.to_json(fig)),
            title=title,
            summary=summary,
            code=code,
            model=settings.llm_model,
            provider=provider,
            elapsed_ms=elapsed_ms,
        )

    except Exception as exc:
        logger.exception(f"Plot generation failed: {exc}")
        raise AppError("plot_generation_failed", f"Plot generation failed: {exc}") from exc
