# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

| Command | Purpose |
|---------|---------|
| `make dev` | Run API (port 8000) + web (port 3000) servers together |
| `make api` | Run FastAPI server only |
| `make web` | Run Next.js server only |
| `make install` | Install all dependencies (pnpm + uv) |
| `make test` | Run backend pytest tests |
| `make test-web` | Run Playwright E2E tests |
| `make build-web` | Build Next.js for production |
| `make lint` | Run Next.js linter |

Run a single backend test:
```
cd apps/api && uv run pytest tests/test_validation.py -v
```

## Architecture

Monorepo with two apps communicating over REST:

```
apps/web (Next.js 14, port 3000)  →  apps/api (FastAPI, port 8000)
     ↓                                      ↓
  react-plotly.js rendering         LLM agent (OpenRouter/OpenAI)
  PostHog analytics                 In-memory session store
  Tailwind CSS                      Sandboxed code execution
```

**Data flow:** User selects a dataset (curated UCI or CSV URL) → sends chat message → backend calls LLM to generate Plotly code → code executed in sandbox → Plotly JSON returned → frontend renders chart.

### Backend (`apps/api/`)

- **`app/main.py`** — FastAPI app, routes, CORS setup
- **`app/plot_agent.py`** — LLM agent that generates Plotly visualizations. Calls LLM, parses JSON response, executes generated code in restricted environment (whitelisted builtins only), returns plot JSON
- **`app/models.py`** — Pydantic request/response models shared across endpoints
- **`app/config.py`** — Pydantic Settings reading from env vars
- **`app/session_store.py`** — Ephemeral in-memory dict mapping session IDs to dataframes + chat history (no persistence)
- **`app/datasets.py`** — Loads curated CSV files from `data/` directory
- **`app/utils.py`** — CSV URL validation (blocks localhost/private IPs) and async streaming download
- **`app/analytics.py`** — PostHog wrapper with AI span tracking (`$ai_session_id`, `$ai_span_name`)

### Frontend (`apps/web/`)

- **`app/page.tsx`** — Single main component handling dataset selection, chat interface, and plot rendering. All state is local React hooks (no global store)
- **`lib/api.ts`** — Typed fetch wrappers for backend endpoints with `ApiError` class
- **`app/providers.tsx`** — PostHog provider initialization

### Key API Endpoints

- `POST /api/datasets/uci` — Load curated dataset (iris, wine, auto_mpg)
- `POST /api/datasets/url` — Load CSV from URL with validation
- `POST /api/chat` — Generate visualization via LLM agent
- `GET /api/datasets` — List available datasets

## Important Patterns

**Plotly JSON serialization:** Use `json.loads(plotly.io.to_json(fig))` — never `fig.to_plotly_json()` which returns numpy arrays that break Pydantic serialization.

**LLM response format:** Always pass `response_format={"type": "json_object"}` to the LLM call to ensure valid JSON output.

**Error model:** Backend uses `AppError(code, message, status_code)` exception. Frontend uses `ApiError` class. Both produce `{"error": {"code": "...", "message": "..."}}` responses.

**Session management:** Sessions are ephemeral in-memory dicts keyed by UUID. Frontend stores session ID in `localStorage`. Sessions are lost on server restart.

**Code sandbox:** The LLM-generated Plotly code runs in a restricted `exec()` environment with only `df`, `pd`, `px`, `go` available and whitelisted builtins. The code must create a `fig` variable.

## Environment

- Backend env: `apps/api/.env` (see `.env.example`)
- Frontend env: `apps/web/.env.local`
- Key vars: `OPENROUTER_API_KEY` or `OPENAI_API_KEY`, `POSTHOG_API_KEY`, `WEB_ORIGIN`
- Package managers: **pnpm** (web), **uv** (api)
- Deployment: Render (see `render.yaml` — separate API and Web services)

## Custom Tailwind Theme

Colors defined in `tailwind.config.ts`: `ink`, `mist`, `flare`, `splash`, `moss`, `dusk`. Fonts: Space Grotesk (display), IBM Plex Mono (mono).
