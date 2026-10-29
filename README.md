# Chumba Labs

Chumba Labs is an autonomous HPLC/GC-MS method-development agent. HPLC is the working demo. GC-MS is a thin plugin: a boiling-point proxy and a rule score, not a spectral library. RDKit descriptors and a linear solvent strength (LSS) style model produce retention, resolution, and run time. [Muse Spark](https://dev.meta.ai/docs/overview) (`muse-spark-1.3`) plans and calls tools. Those numbers come from code, not from the model.

The built-in HPLC demo separates three public structures (ethanol, acetic acid, and benzene) on a reversed-phase C18 gradient. The agent may change column, flow, temperature, and gradient. `simulate_hplc` and `score_hplc` return the metrics. The system prompt tells the model to cite only those tool results.

## What this does not claim

The HPLC retention model is an offline LSS approximation, `log k(φ) = log k_w − S·φ`, with `log k_w` and `S` from RDKit (MolLogP, TPSA, molecular weight, hydrogen-bond donor/acceptor counts, and aromatic ring count). Higher MolLogP elutes later in reversed phase. Flow and column size set the void time. It is a rank-order aid for method search. It is not a validated chromatographic model, it does not control an instrument, and it is not a GxP or 21 CFR Part 11 system. Confirm any method on the instrument.

GC-MS elution uses a separate boiling-point proxy from the same descriptors. It does not call the network, and it is not an experimental boiling point.

## Stack

Python 3.13+ with [uv](https://docs.astral.sh/uv/). Package name: `chumba-labs`.

- **RDKit** computes the descriptors used by HPLC simulation and the GC-MS proxy.
- **LangChain tool calling** ([LangChain](https://docs.langchain.com/)) binds HPLC tools to Chat Completions. The Spark loop is capped (about five simulate/score rounds, plus a few extra model turns).
- **Meta Model API** ([overview](https://dev.meta.ai/docs/overview)): base URL `https://api.meta.ai/v1`, model `muse-spark-1.3`.
- **Modal** ([intro](https://modal.com/docs/guide/intro)): CPU image (`debian_slim`, Python 3.13) runs RDKit simulate and score. No GPU.

## Repository layout

| Path | Role |
| --- | --- |
| `main.py` | CLI: `health` and `hplc-demo`. |
| `agent/` | Spark tool loop and the offline method search that uses the same HPLC tools. |
| `api/` | FastAPI server (`api/server.py`) and route handlers used by the CLI and UI. |
| `chromatography/` | Shared types and SMILES descriptors; HPLC catalog, simulation, and scoring; GC-MS plugin. |
| `modal/` | Modal app `chumba-labs`: remote HPLC score plus small HTTP score endpoints. |
| `tests/` | Pytest for HPLC scoring, the GC-MS proxy, and the agent loop. |
| `chumbalabs/` | Vite + Vue + TypeScript method-development workstation (local dev). |
| `context/` | Hackathon scope and event notes. |

Run commands from the repository root.

## Prerequisites

- Python 3.13 or newer (`.python-version` is `3.13`).
- [uv](https://docs.astral.sh/uv/).
- A Meta Model API key for the live Spark path.
- A Modal account only if you run the remote chemistry function. Modal login is separate from the Meta key.

## How to run

`uv run` syncs dependencies before it starts. `uv sync` does the install on its own.

```powershell
uv sync
```

Put the key in a `.env` file at the repository root. `main.py` loads it at startup. Use either name:

```text
MODEL_API_KEY=your-api-key-here
```

`META_API_KEY` is accepted as well. Do not commit `.env`.

```powershell
uv run main.py health
uv run main.py hplc-demo
uv run pytest
```

`hplc-demo` writes one line to stderr:

- `hplc path: spark` — a key was set and Muse Spark returned a `score_hplc` result.
- `hplc path: local` — neither `MODEL_API_KEY` nor `META_API_KEY` is set. No model call. The demo walks a fixed set of HPLC methods and keeps the best score from the same simulate and score tools.
- `hplc path: spark-fallback` — a key was set, the Spark call failed, and the demo continued on that local search. Stderr also prints `spark failed:` plus the exception type.

Modal, after `uv run modal setup` (or an existing token):

```powershell
uv run modal run modal/deploy.py
```

That runs `hplc_demo` on Modal CPU and prints resolution, run time, `passed`, penalties, and peak times for the default three analytes. It does not call Muse Spark. The app also defines HTTP score endpoints; `modal run` only executes the local entrypoint.

The commands above are the same in bash. To set the key in the shell instead of `.env`: PowerShell uses `$env:MODEL_API_KEY = "your-api-key-here"`; bash uses `export MODEL_API_KEY="your-api-key-here"`.

## Frontend

Local UI in `chumbalabs/`: a three-column workstation (input, method/scores/chromatogram, agent timeline). Layout and API types are documented in [chumbalabs/README.md](chumbalabs/README.md).

Run the API and the dev server in **two terminals** from the repository root.

Terminal 1 — FastAPI on port 8000:

```powershell
uv run uvicorn api.server:app --reload --port 8000
```

Terminal 2 — Vite (proxies `/api` → `http://127.0.0.1:8000`):

```powershell
cd chumbalabs
npm install
npm run dev
```

Open http://localhost:5173. **Run agent** sends `POST /api/hplc/run` with analytes and goals; the UI renders method parameters, score cards, a chromatogram, and Spark tool steps. Root `.env` supplies `MODEL_API_KEY` / `META_API_KEY` to the API process, not to Vite.

## Demo output

`health` prints `{"status": "ok"}`.

`hplc-demo` prints JSON. Fields:

| Field | Meaning |
| --- | --- |
| `path` | `spark`, `local`, or `spark-fallback`. |
| `modality` | `hplc` for this demo. |
| `min_resolution` | Smallest adjacent-peak resolution from the scorer. |
| `total_time_min` | Simulated run time in minutes. |
| `passed` | True only when the score has no penalties. |
| `penalties` | `resolution` if min resolution is under 1.5; `run_time` if the run exceeds 12 minutes. Values are the shortfall. |
| `iterations` | How many `score_hplc` calls ran. |
| `explanation` | Present when Spark returned text. It is commentary on tool output. |

`passed: false` still means the command worked. On `path: spark` it means the API and the tools ran, and this method missed the resolution target, the time target, or both. The demo goals are minimum resolution 1.5 and maximum run time 12 minutes.

## Hackathon

This repo is the Meta Global AI Developer Hackathon build (27 Oct–4 Nov 2026): HPLC carries the demo, GC-MS shows the same plugin shape, and Muse Spark is the planner. Scope and event rules are in [context/hackathon_mvp_scope.md](context/hackathon_mvp_scope.md) and [context/event_details.md](context/event_details.md).
