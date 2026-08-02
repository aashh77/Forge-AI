"""Shared data shapes for the Forge AI agent engine.

Plain dictionaries are used (instead of an ORM) so the entire state of a
run can be persisted as a single human-readable JSON document and served
directly to the dashboard.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

AGENT_NAMES = [
    "architect",
    "planner",
    "backend",
    "frontend",
    "qa",
    "security",
    "reviewer",
    "supervisor",
    "deploy",
]

STATUS_IDLE = "idle"
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def now() -> float:
    return time.time()


def new_agent_state(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": STATUS_IDLE,
        "progress": 0,
        "logs": [],
        "decisions": [],
        "commits": [],
        "started_at": None,
        "finished_at": None,
        "retries": 0,
        "error": None,
    }


def new_run_state(run_id: str, prompt: str) -> dict[str, Any]:
    return {
        "id": run_id,
        "prompt": prompt,
        "status": STATUS_PENDING,
        "error": None,
        "created_at": now(),
        "updated_at": now(),
        "paused_at": None,
        "agents": {name: new_agent_state(name) for name in AGENT_NAMES},
        "checkpoints": [],
        "debates": [],
        "chat_history": {name: [] for name in AGENT_NAMES},
        "deployment": {
            "status": "not_started",
            "url": None,
            "port": None,
            "attempts": 0,
            "logs": [],
        },
        "reliability": {},
        "stats": {},
        "incidents": [],
        "active_debug": None,
        "_usage": [],
        "control": {
            "paused": False,
            "stopped": False,
            "resume_stage": 0,
        },
        "pipeline_context": {},
    }
