"""FastAPI server exposing the Forge AI agent engine to the Next.js
dashboard (or any HTTP client). Run with:

    python server.py
    # or
    uvicorn server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.architect import ArchitectAgent
from agents.backend import BackendAgent
from agents.frontend import FrontendAgent
from agents.planner import PlannerAgent
from agents.qa import QAAgent
from agents.security import SecurityAgent
from config import settings
from llm_client import llm_client
from models import new_id
from pipeline import pause_run, redeploy_run, resume_run, run_debug, run_pipeline, stop_run
from storage import store
from zipper import build_zip_bytes

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


def _refresh_deployment_status(run_id: str) -> None:
    """Update deployment.status based on whether the live URL is reachable."""
    state = store.load(run_id)
    deployment = state.get("deployment", {})
    url = deployment.get("url")
    if not url:
        return
    live = False
    if requests:
        try:
            resp = requests.get(url, timeout=3)
            live = resp.status_code < 500
        except Exception:
            live = False
    new_status = "running" if live else "not_live"
    if deployment.get("status") != new_status:
        deployment["status"] = new_status
        store.mutate(run_id, lambda s: s.__setitem__("deployment", deployment))

app = FastAPI(title="Forge AI Agent Engine", version="1.0.0")

origins = ["*"] if settings.cors_origins.strip() == "*" else [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_REGISTRY = {
    "architect": ArchitectAgent,
    "planner": PlannerAgent,
    "backend": BackendAgent,
    "frontend": FrontendAgent,
    "qa": QAAgent,
    "security": SecurityAgent,
}


class CreateRunRequest(BaseModel):
    prompt: str
    run_id: str | None = None


class ChatRequest(BaseModel):
    agent: str
    question: str


class RollbackRequest(BaseModel):
    checkpoint_id: str


class DebugRequest(BaseModel):
    question: str


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "hi"
    target_lang: str = "en"


@app.get("/health")
def health():
    return {
        "ok": True,
        "llm_configured": llm_client.is_configured,
        "llm_problems": llm_client.configuration_problems(),
        "provider": settings.llm_provider,
        "model": settings.openai_model,
    }


@app.get("/runs")
def list_runs():
    return {"runs": store.list_runs()}


@app.post("/runs")
def create_run(payload: CreateRunRequest, background_tasks: BackgroundTasks):
    if not payload.prompt or not payload.prompt.strip():
        raise HTTPException(400, "prompt is required")
    run_id = payload.run_id or new_id("run-")
    if store.exists(run_id):
        raise HTTPException(409, "run_id already exists")
    store.create_run(payload.prompt.strip(), run_id)
    background_tasks.add_task(run_pipeline, run_id, payload.prompt.strip())
    return {"run_id": run_id}


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    _refresh_deployment_status(run_id)
    return store.load(run_id)


@app.get("/runs/{run_id}/deployment-status")
def deployment_status(run_id: str):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    _refresh_deployment_status(run_id)
    return store.load(run_id)["deployment"]


@app.post("/runs/{run_id}/pause")
def pause(run_id: str):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    try:
        return pause_run(run_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/runs/{run_id}/resume")
def resume(run_id: str, background_tasks: BackgroundTasks):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")

    def _resume():
        try:
            resume_run(run_id)
        except ValueError as exc:
            store.mutate(run_id, lambda s: s.__setitem__("error", str(exc)))

    background_tasks.add_task(_resume)
    return {"status": "resuming"}


@app.post("/runs/{run_id}/stop")
def stop(run_id: str):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    try:
        return stop_run(run_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/runs/{run_id}/redeploy")
def redeploy(run_id: str):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    try:
        return redeploy_run(run_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/runs/{run_id}/chat")
def chat(run_id: str, payload: ChatRequest):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    agent_cls = AGENT_REGISTRY.get(payload.agent)
    if not agent_cls:
        raise HTTPException(400, f"unknown agent '{payload.agent}'")
    agent = agent_cls(run_id)
    try:
        answer = agent.answer_question(payload.question)
    except Exception as exc:
        raise HTTPException(502, str(exc))
    return {"agent": payload.agent, "question": payload.question, "answer": answer}


@app.get("/runs/{run_id}/checkpoints")
def list_checkpoints(run_id: str):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    return {"checkpoints": store.load(run_id)["checkpoints"]}


@app.post("/runs/{run_id}/rollback")
def rollback(run_id: str, payload: RollbackRequest):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    try:
        cp = store.rollback(run_id, payload.checkpoint_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"restored": cp}


@app.post("/runs/{run_id}/debug")
def debug(run_id: str, payload: DebugRequest, background_tasks: BackgroundTasks):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    background_tasks.add_task(run_debug, run_id, payload.question)
    return {"status": "started"}


@app.post("/translate")
def translate(payload: TranslateRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    try:
        data, _ = llm_client.chat_json(
            f"Translate the user's text from {payload.source_lang} to {payload.target_lang}. "
            "Preserve the original intent, tone, and technical meaning as closely as possible. "
            "Respond with a single JSON object containing exactly two keys: "
            "translated (string) and intent_note (a short explanation of the preserved intent).",
            text,
        )
        return {
            "original": text,
            "translated": data.get("translated", ""),
            "intent_note": data.get("intent_note", ""),
        }
    except Exception as exc:
        raise HTTPException(502, str(exc))


@app.get("/runs/{run_id}/download")
def download(run_id: str):
    if not store.exists(run_id):
        raise HTTPException(404, "run not found")
    data = build_zip_bytes(run_id)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="forge-ai-{run_id}.zip"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
