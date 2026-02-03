# Vibe Plotter

Vibe Plotter is a demo product showcasing PostHog LLM analytics with a multimodal-friendly data visualization agent. Users can load a dataset, chat to request a visualization, and receive a Plotly chart plus a title, summary, and code.

## Features
- Curated datasets (Iris, Wine, Auto MPG) or CSV URL loading
- Chat-driven Plotly chart generation
- Download chart as JSON, HTML, PNG, or code
- PostHog instrumentation on frontend + backend (including AI span metadata)
- Ephemeral in-memory sessions (no database)

## Repo Structure
- `apps/web` — Next.js App Router frontend
- `apps/api` — FastAPI backend
- `packages/` — reserved for shared modules

## Quickstart

### 1) Install dependencies

Frontend:
```bash
pnpm install
```

Backend:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
```

### 2) Configure environment

Copy the env examples and fill in keys:
```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

### 3) Run both apps

```bash
make dev
```

- Web app: `http://localhost:3000`
- API: `http://localhost:8000`

## Environment Variables

Backend (`apps/api/.env`):
- `OPENAI_API_KEY` or `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1`)
- `LLM_MODEL` (default: `gpt-4o-mini`)
- `POSTHOG_ENABLED`
- `POSTHOG_API_KEY`
- `POSTHOG_HOST` (default: `https://us.i.posthog.com`)
- `SESSION_SECRET`
- `MAX_CSV_BYTES` (default: `10000000`)
- `ALLOWED_CSV_HOSTS` (comma-separated)
- `WEB_ORIGIN` (default: `http://localhost:3000`)
- `LLM_DISABLED` (set to `true` to force fallback plots)

Frontend (`apps/web/.env.local`):
- `NEXT_PUBLIC_API_URL` (default: `http://localhost:8000`)
- `NEXT_PUBLIC_POSTHOG_ENABLED`
- `NEXT_PUBLIC_POSTHOG_KEY`
- `NEXT_PUBLIC_POSTHOG_HOST`

## API Endpoints
- `POST /api/datasets/uci` — load curated dataset
- `POST /api/datasets/url` — load CSV from URL
- `POST /api/chat` — request a visualization
- `GET /api/health`

## Testing

Backend:
```bash
cd apps/api
pytest
```

Frontend (requires running web + api):
```bash
pnpm -C apps/web test:e2e
```

## Notes
- CSV loading enforces max size and blocks non-http(s) URLs and localhost/private IPs.
- LLM calls are optional; fallback charts render when no API key is provided.
- PostHog events include `session_id` and `$ai_span_name = plot_agent` for LLM traces.
