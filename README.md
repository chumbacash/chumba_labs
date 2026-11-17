# Chumba Labs

HPLC/GC-MS method-development agent. HPLC is the main path; GC-MS is a thin boiling-point proxy, not a spectral library. RDKit descriptors and a linear solvent strength (LSS) model produce retention, resolution, and run time. An LLM tool-calling loop plans and calls tools. Metrics come from code, not the model.

The HPLC demo separates acetaminophen, caffeine, and aspirin on a reversed-phase C18 gradient. The agent may change column, flow, temperature, and gradient. `simulate_hplc` and `score_hplc` return the metrics; the model is told to cite only those results.

## What this does not claim

The HPLC model is an offline LSS approximation (`log k(φ) = log k_w − S·φ`) from RDKit descriptors. It ranks methods for search. It is not a validated chromatographic model, does not control an instrument, and is not GxP / 21 CFR Part 11. Confirm methods on the instrument.

## Stack

Python 3.13+ with [uv](https://docs.astral.sh/uv/). Package: `chumba-labs`.

- **RDKit** — descriptors for HPLC simulation and the GC-MS proxy
- **LangChain tool calling** — binds HPLC tools to Chat Completions; capped at five scored methods; retries when goals are missed or resolution is below 2.0
- **Model API** (optional) — Chat Completions-compatible Meta Model API (`META_API_KEY` / `MODEL_API_KEY`)
- **Modal** — CPU image runs RDKit simulate/score (no GPU)

## Layout

```text
main.py           CLI (health, hplc-demo)
agent/            tool loop and offline method search
api/              FastAPI server
chromatography/   types, descriptors, HPLC, GC-MS plugin
modal/            Modal app and score endpoints
tests/            pytest
frontend/         Vue + TypeScript workstation
Dockerfile        API image
```

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Model API key for the live agent path
- Modal account only if you run the remote chemistry function

## How to run

```powershell
uv sync
```

Copy `.env.example` to `.env` and set:

```text
META_API_KEY=your-api-key-here
```

`MODEL_API_KEY` works as a legacy alias. Do not commit `.env`.

```powershell
uv run main.py health
uv run main.py hplc-demo
uv run pytest
```

`hplc-demo` stderr paths:

- `spark` — key set; agent returned a scored method
- `local` — no key; fixed offline search over the same tools
- `spark-fallback` — key set but agent failed; continued on local search

Modal (separate from `.env`):

```powershell
uv run modal setup
uv run modal run modal/deploy.py
```

Runs `hplc_demo` on Modal CPU (no LLM). Shell key instead of `.env`: `$env:META_API_KEY = "..."` (PowerShell) or `export META_API_KEY="..."` (bash).

## Docker and CI

```powershell
docker build -t chumba-labs .
docker run --rm -p 8000:8000 --env-file .env chumba-labs
```

`GET /api/health` returns `{"status":"ok"}`.

- `ci.yml` — pytest, Vue build, Docker health smoke
- `publish.yml` — GHCR on `main` and `v*` tags

```powershell
docker run --rm -p 8000:8000 -e META_API_KEY=your-api-key-here ghcr.io/chumbacash/chumba-labs:latest
```

## Demo output

`health` → `{"status": "ok"}`.

`hplc-demo` prints JSON with `path`, `modality`, `min_resolution`, `total_time_min`, `passed`, `penalties`, `iterations`, and optional `explanation`. Demo goals: min resolution 1.5, max run time 12 minutes. `passed: false` means the method missed a target; the command still succeeded.
