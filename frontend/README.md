# Chumba Labs workstation

Browser UI for the Chumba Labs HPLC method-development agent: enter analytes and targets, run the agent against the local API, inspect each proposal (method, scores, chromatogram), and read the Spark tool timeline.

## Prerequisites

- Node.js 20+ (npm)
- Python API listening on port **8000** (see the root [README](../README.md))

## Run locally

From the repository root, start the API first:

```powershell
uv run uvicorn api.server:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to `http://127.0.0.1:8000`.

Other scripts: `npm run build` (production bundle to `dist/`), `npm run preview` (serve `dist/`).

## Stack

- Vue 3 (`<script setup>`)
- TypeScript
- Vite 8

## Layout and components

| Component | Role |
| --- | --- |
| `InputPanel.vue` | Analytes, modality, resolution/time goals, **Run agent** |
| `MethodTable.vue` | Column, flow, temperature, gradient table |
| `ScoreCards.vue` | Min resolution, run time, pass/fail vs targets |
| `Chromatogram.vue` | Simulated peak plot from tool output |
| `AgentTimeline.vue` | Spark path, tool steps, explanation |
| `HelloWorld.vue` | Unused Vite scaffold (safe to delete) |

`App.vue` wires the panes and calls the API.

## API contract

The UI uses relative URLs so the dev proxy works.

- **POST** `/api/hplc/run` — JSON body (`RunRequest` in `src/types/api.ts`):
  - `modality`: `"hplc"` or `"gc_ms"`
  - `analytes`: `{ name, smiles }[]`
  - `min_resolution`, `max_run_time_min`
  - optional `follow_up`: a note to Spark for a follow-up run; it requires a Meta Model API key
- **Response** (`RunResponse`): final method, simulation, score, optional `history` of proposals, `steps` from tool calls, `path` (`spark` / `local` / `spark-fallback`), and optional `explanation`.

Spark retries scored methods when the goals are missed or resolution is below 2.0, up to five scored methods. The simulator models only the listed C18 columns; it does not support conclusions about other stationary phases.

Types in `src/types/api.ts` should stay aligned with the FastAPI handlers in `api/`.
