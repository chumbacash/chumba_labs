from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import health, hplc_run_from_body

app = FastAPI(title="Chumba Labs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def api_health():
    return health()


@app.get("/health")
def health_alias():
    return health()


@app.post("/api/hplc/run")
async def api_hplc_run(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid JSON body"})
    status, payload = await run_in_threadpool(
        hplc_run_from_body, body if isinstance(body, dict) else {}
    )
    return JSONResponse(status_code=status, content=payload)
