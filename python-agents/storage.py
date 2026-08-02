"""Filesystem-backed persistence for agent runs.

Every run gets its own folder under WORKSPACE_DIR:

  workspace/<run_id>/
    state.json          full run state: agent statuses, logs, decisions,
                         checkpoints, debates, chat history, deployment info
    project/             the actual generated application code
    docs/                architecture docs, ADRs, justification & incident
                         reports, review notes, debate transcripts
    checkpoints/<n>/     snapshot of project/ + state.json at that point
    server.log           stdout/stderr of the currently deployed app
"""
from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path
from typing import Any, Callable

from config import settings
from models import new_agent_state, new_run_state, now


class RunStore:
    def __init__(self) -> None:
        self._locks: dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()
        settings.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _lock_for(self, run_id: str) -> threading.RLock:
        with self._global_lock:
            if run_id not in self._locks:
                self._locks[run_id] = threading.RLock()
            return self._locks[run_id]

    def run_dir(self, run_id: str) -> Path:
        return settings.workspace_dir / run_id

    def project_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "project"

    def docs_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "docs"

    def checkpoints_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "checkpoints"

    def state_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "state.json"

    def create_run(self, prompt: str, run_id: str) -> dict[str, Any]:
        state = new_run_state(run_id, prompt)
        self.run_dir(run_id).mkdir(parents=True, exist_ok=True)
        self.project_dir(run_id).mkdir(parents=True, exist_ok=True)
        self.docs_dir(run_id).mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir(run_id).mkdir(parents=True, exist_ok=True)
        self.save(run_id, state)
        return state

    def exists(self, run_id: str) -> bool:
        return self.state_path(run_id).exists()

    def load(self, run_id: str) -> dict[str, Any]:
        with self._lock_for(run_id):
            with open(self.state_path(run_id), "r", encoding="utf-8") as fh:
                return json.load(fh)

    def save(self, run_id: str, state: dict[str, Any]) -> None:
        with self._lock_for(run_id):
            state["updated_at"] = now()
            tmp = self.state_path(run_id).with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(state, fh, indent=2, default=str)
            tmp.replace(self.state_path(run_id))

    def mutate(self, run_id: str, fn: Callable[[dict[str, Any]], Any]) -> dict[str, Any]:
        """Load -> mutate in place with fn(state) -> save. Returns the new state."""
        with self._lock_for(run_id):
            state = self.load(run_id)
            fn(state)
            self.save(run_id, state)
            return state

    def list_runs(self) -> list[dict[str, Any]]:
        runs = []
        if not settings.workspace_dir.exists():
            return runs
        for d in sorted(settings.workspace_dir.iterdir()):
            if (d / "state.json").exists():
                try:
                    state = self.load(d.name)
                    runs.append(
                        {
                            "id": state["id"],
                            "prompt": state["prompt"],
                            "status": state["status"],
                            "created_at": state["created_at"],
                            "updated_at": state["updated_at"],
                        }
                    )
                except Exception:
                    continue
        return sorted(runs, key=lambda r: r["created_at"], reverse=True)

    # ---------- log / decision / commit helpers ----------

    def _ensure_agent(self, state: dict[str, Any], agent: str) -> dict[str, Any]:
        """Return the agent state slice, creating it on the fly if the agent
        name is not part of the initial run state. This prevents KeyError
        crashes when the planner schedules meta-steps such as 'deploy'."""
        if agent not in state["agents"]:
            state["agents"][agent] = new_agent_state(agent)
            state["chat_history"].setdefault(agent, [])
        return state["agents"][agent]

    def log(self, run_id: str, agent: str, message: str, level: str = "info") -> None:
        def _mut(state: dict[str, Any]) -> None:
            self._ensure_agent(state, agent)["logs"].append({"ts": now(), "message": message, "level": level})

        self.mutate(run_id, _mut)

    def set_status(self, run_id: str, agent: str, status: str, progress: int | None = None) -> None:
        def _mut(state: dict[str, Any]) -> None:
            a = self._ensure_agent(state, agent)
            a["status"] = status
            if progress is not None:
                a["progress"] = progress
            if status == "running" and not a["started_at"]:
                a["started_at"] = now()
            if status in ("success", "failed"):
                a["finished_at"] = now()

        self.mutate(run_id, _mut)

    def add_decision(self, run_id: str, agent: str, decision: dict[str, Any]) -> None:
        record = {"id": decision.get("id") or f"dec-{int(now() * 1000)}", "ts": now(), **decision}

        def _mut(state: dict[str, Any]) -> None:
            self._ensure_agent(state, agent)["decisions"].append(record)

        self.mutate(run_id, _mut)

    def add_commit(self, run_id: str, agent: str, commit: dict[str, Any]) -> None:
        record = {"id": commit.get("id") or f"commit-{int(now() * 1000)}", "ts": now(), **commit}

        def _mut(state: dict[str, Any]) -> None:
            self._ensure_agent(state, agent)["commits"].append(record)

        self.mutate(run_id, _mut)

    def write_doc(self, run_id: str, filename: str, content: str) -> str:
        path = self.docs_dir(run_id) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(self.run_dir(run_id)))

    def write_project_file(self, run_id: str, rel_path: str, content: str) -> str:
        path = self.project_dir(run_id) / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return rel_path

    def set_control(self, run_id: str, **kwargs: Any) -> dict[str, Any]:
        def _mut(state: dict[str, Any]) -> None:
            state.setdefault("control", {"paused": False, "stopped": False, "resume_stage": 0})
            state["control"].update(kwargs)
        return self.mutate(run_id, _mut)

    def set_pipeline_context(self, run_id: str, **kwargs: Any) -> dict[str, Any]:
        def _mut(state: dict[str, Any]) -> None:
            state.setdefault("pipeline_context", {})
            state["pipeline_context"].update(kwargs)
        return self.mutate(run_id, _mut)

    # ---------- checkpoints (self-healing rollback) ----------

    def create_checkpoint(self, run_id: str, description: str, tag: str = "") -> dict[str, Any]:
        with self._lock_for(run_id):
            state = self.load(run_id)
            idx = len(state["checkpoints"]) + 1
            cp_dir = self.checkpoints_dir(run_id) / str(idx)
            if cp_dir.exists():
                shutil.rmtree(cp_dir)
            cp_dir.mkdir(parents=True, exist_ok=True)
            if self.project_dir(run_id).exists():
                shutil.copytree(self.project_dir(run_id), cp_dir / "project", dirs_exist_ok=True)
            if self.docs_dir(run_id).exists():
                shutil.copytree(self.docs_dir(run_id), cp_dir / "docs", dirs_exist_ok=True)
            shutil.copy2(self.state_path(run_id), cp_dir / "state.json")
            checkpoint = {
                "number": idx,
                "id": f"cp-{idx}",
                "description": description,
                "tag": tag,
                "ts": now(),
            }
            state["checkpoints"].append(checkpoint)
            self.save(run_id, state)
            return checkpoint

    def rollback(self, run_id: str, checkpoint_id: str) -> dict[str, Any]:
        with self._lock_for(run_id):
            state = self.load(run_id)
            cp = next((c for c in state["checkpoints"] if c["id"] == checkpoint_id), None)
            if not cp:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")
            cp_dir = self.checkpoints_dir(run_id) / str(cp["number"])
            if not cp_dir.exists():
                raise ValueError(f"Checkpoint snapshot missing for {checkpoint_id}")
            if self.project_dir(run_id).exists():
                shutil.rmtree(self.project_dir(run_id))
            shutil.copytree(cp_dir / "project", self.project_dir(run_id))
            if (cp_dir / "docs").exists():
                docs_dir = self.docs_dir(run_id)
                if docs_dir.exists():
                    shutil.rmtree(docs_dir)
                shutil.copytree(cp_dir / "docs", docs_dir)
            restored_state = json.loads((cp_dir / "state.json").read_text(encoding="utf-8"))
            restored_state["checkpoints"] = state["checkpoints"]
            restored_state["status"] = "rolled_back"
            self.save(run_id, restored_state)
            return cp


store = RunStore()
