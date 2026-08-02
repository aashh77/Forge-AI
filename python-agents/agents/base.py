"""Base class shared by every Forge AI agent.

This class provides bookkeeping (status, logs, decisions, commits) and thin
helpers for calling the real LLM. It never fabricates an answer itself —
`ask_json` / `ask_text` always go through `llm_client`, which calls the
configured LLM API.
"""
from __future__ import annotations

import json
from typing import Any

from llm_client import LLMConfigurationError, llm_client
from storage import store


class BaseAgent:
    name: str = "base"
    display_name: str = "Base Agent"

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id

    # ---- state helpers -------------------------------------------------
    def log(self, message: str, level: str = "info") -> None:
        store.log(self.run_id, self.name, message, level)

    def status(self, status: str, progress: int | None = None) -> None:
        store.set_status(self.run_id, self.name, status, progress)

    def decide(self, topic: str, chosen: str, justification: str, **extra: Any) -> dict[str, Any]:
        decision = {"topic": topic, "chosen": chosen, "justification": justification, **extra}
        store.add_decision(self.run_id, self.name, decision)
        return decision

    def commit(self, message: str, files: list[str]) -> dict[str, Any]:
        c = {"message": message, "files": files}
        store.add_commit(self.run_id, self.name, c)
        return c

    def write_doc(self, filename: str, content: str) -> str:
        return store.write_doc(self.run_id, filename, content)

    def write_file(self, rel_path: str, content: str) -> str:
        return store.write_project_file(self.run_id, rel_path, content)

    # ---- LLM helpers -----------------------------------------------------
    def ask_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        if not llm_client.is_configured:
            raise LLMConfigurationError("; ".join(llm_client.configuration_problems()))
        data, result = llm_client.chat_json(
            system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens
        )

        def _record_usage(state: dict[str, Any]) -> None:
            state.setdefault("_usage", []).append(
                {
                    "agent": self.name,
                    "prompt_tokens": result.usage.prompt_tokens,
                    "completion_tokens": result.usage.completion_tokens,
                    "cost_usd": result.usage.cost_usd(),
                    "latency": result.latency_seconds,
                }
            )

        store.mutate(self.run_id, _record_usage)
        return data

    def ask_text(self, system_prompt: str, user_prompt: str, *, temperature: float | None = None) -> str:
        result = llm_client.chat(system_prompt, user_prompt, temperature=temperature)
        return result.content

    def answer_question(self, question: str) -> dict[str, Any]:
        """Powers the dashboard chat panel. Always calls the real LLM and is
        grounded ONLY in this agent's own recorded decisions, logs and commits
        so the user can ask 'why' it made a decision."""
        state = store.load(self.run_id)
        agent_state = state["agents"][self.name]
        context = {
            "project_prompt": state["prompt"],
            "this_agents_decisions": agent_state["decisions"],
            "this_agents_recent_logs": agent_state["logs"][-30:],
            "this_agents_commits": agent_state["commits"],
            "deployment": state.get("deployment", {}),
        }
        system = (
            f"You are the {self.display_name} inside Forge AI, a multi-agent software "
            "engineering system. The user is asking YOU a question. Ground your answer ONLY "
            "in your own recorded decisions, logs and commits. Be honest: if the context does "
            "not support an answer, say so. Respond as strict JSON with keys: reason (short "
            "string), evidence (string), confidence (0-100 integer), alternative (string "
            "describing an alternative approach that was considered)."
        )
        user = (
            f"Project prompt: {state['prompt']}\n\n"
            f"Your recorded context:\n{json.dumps(context, indent=2, default=str)[:8000]}\n\n"
            f"Question: {question}"
        )
        answer = self.ask_json(system, user)

        def _record(state_: dict[str, Any]) -> None:
            state_["chat_history"][self.name].append({"question": question, "answer": answer})
            # Append this Q&A to the latest checkpoint so it is versioned with the run state.
            if state_["checkpoints"]:
                latest = state_["checkpoints"][-1]
                summary = (
                    f"Q&A with {self.display_name}: Q: {question} | "
                    f"A: {answer.get('reason', '')[:120]}"
                )
                latest["description"] = f"{latest['description']}\n\n{summary}"

        store.mutate(self.run_id, _record)
        return answer

    def trace(self, question: str, layer_description: str) -> dict[str, Any]:
        """Used by the Natural Language Debugger to analyse this agent's
        layer of the stack for a reported problem, with full project context."""
        state = store.load(self.run_id)
        system = (
            f"You are the {self.display_name} participating in a live incident trace. "
            f"Your layer of the system is: {layer_description}. Analyse whether this layer "
            "is a likely bottleneck/cause for the reported issue, grounded in the WHOLE project "
            "context (all agents' decisions, deployment status, and reliability signals). "
            "Respond as strict JSON with keys: layer (string), "
            "is_bottleneck (boolean), analysis (string), evidence (string), "
            "suggested_fix (string, empty string if none)."
        )
        user = (
            f"Project prompt: {state['prompt']}\n"
            f"Reported issue: {question}\n"
            f"Full project decisions:\n"
            f"{json.dumps({name: state['agents'][name]['decisions'] for name in state['agents']}, default=str)[:6000]}\n"
            f"Deployment: {json.dumps(state.get('deployment', {}), default=str)[:1500]}\n"
            f"Reliability: {json.dumps(state.get('reliability', {}), default=str)[:1500]}"
        )
        return self.ask_json(system, user)
