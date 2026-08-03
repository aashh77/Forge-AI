"""Supervisor Agent: watches every other agent, resolves disputes via short,
focussed LLM debates, and produces the AI Reliability Scorecard + final run
statistics.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from agents.base import BaseAgent
from config import settings
from storage import store

_REGRESSION_LOCK = threading.Lock()


def _regression_file() -> Path:
    return settings.workspace_dir / "regression_history.json"


def _append_regression(entry: dict) -> list[dict]:
    with _REGRESSION_LOCK:
        path = _regression_file()
        history = []
        if path.exists():
            try:
                history = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                history = []
        history.append(entry)
        history = history[-50:]
        path.write_text(json.dumps(history, indent=2), encoding="utf-8")
        return history


def _normalize(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum())


class SupervisorAgent(BaseAgent):
    name = "supervisor"
    display_name = "Supervisor Agent"

    def detect_and_resolve_conflicts(self) -> list[dict]:
        self.status("running", 10)
        state = store.load(self.run_id)
        by_topic: dict[str, list[dict]] = {}
        for agent_name, agent_state in state["agents"].items():
            if agent_name == "supervisor":
                continue
            for d in agent_state.get("decisions", []):
                topic = d.get("topic")
                if not topic:
                    continue
                by_topic.setdefault(topic, []).append({"agent": agent_name, **d})

        conflicts_found = []
        for topic, decisions in by_topic.items():
            if len(decisions) < 2:
                continue
            distinct = {_normalize(d.get("chosen", "")) for d in decisions}
            distinct.discard("")
            distinct.discard("unspecified")
            if len(distinct) > 1:
                conflicts_found.append((topic, decisions))

        for topic, decisions in conflicts_found:
            self.log(f"Conflict detected on '{topic}'. Calling short debate...", "warning")
            agents = [d["agent"] for d in decisions]
            self.mediate_dispute(
                topic=topic,
                agent_a=agents[0],
                agent_b=agents[1] if len(agents) > 1 else agents[0],
                position_a=decisions[0],
                position_b=decisions[1] if len(decisions) > 1 else decisions[0],
                context={"source": "decision_conflict", "prompt": state["prompt"]},
            )
        if not conflicts_found:
            self.log("No conflicts detected among agent decisions.", "info")
        self.status("success", 100)
        return conflicts_found

    def mediate_dispute(
        self,
        topic: str,
        agent_a: str,
        agent_b: str,
        position_a: dict[str, Any],
        position_b: dict[str, Any],
        context: dict[str, Any],
    ) -> dict:
        """Short, focused debate between two agents. Limited to 2-3 turns each.
        The winner and full transcript are recorded in the debate log."""
        self.status("running", 10)
        state = store.load(self.run_id)
        self.log(
            f"Moderating dispute '{topic}' between {agent_a} and {agent_b}. "
            "Each side gets up to 3 short arguments.",
            "warning",
        )

        transcript: list[dict] = []
        positions = {
            agent_a: {"agent": agent_a, **position_a},
            agent_b: {"agent": agent_b, **position_b},
        }

        # Limit debate to 3 rounds max; stop early on concession.
        for round_no in range(1, 3):
            round_turns = []
            for agent_name, position in positions.items():
                system = (
                    f"You are the {agent_name.title()} Agent in a short, focused Forge AI debate "
                    f"about '{topic}'. You have full project context. State ONE concrete argument, "
                    "counter the opponent's last point if any, and concede honestly if their logic "
                    "is stronger. Keep it brief. Respond as strict JSON: "
                    '{"argument": str, "concede": bool}'
                )
                history = "\n".join(
                    f"[{t['agent']} round {t['round']}] {t['argument']}" for t in transcript[-4:]
                )
                user = (
                    f"Project prompt: {state['prompt']}\n"
                    f"Issue context: {json.dumps(context, default=str)[:1500]}\n"
                    f"Your position: {json.dumps(position, default=str)[:800]}\n"
                    f"Debate so far:\n{history if history else '(debate just started)'}"
                )
                data = self.ask_json(system, user, temperature=0.5, max_tokens=700)
                turn = {
                    "round": round_no,
                    "agent": agent_name,
                    "argument": data.get("argument", ""),
                    "concede": bool(data.get("concede")),
                }
                transcript.append(turn)
                round_turns.append(turn)
                self.log(f"[Debate:{topic}] {agent_name} (round {round_no}): {turn['argument'][:160]}")
            if any(t["concede"] for t in round_turns):
                self.log(f"Debate '{topic}' ended early due to concession.", "info")
                break

        system = (
            "You are the Supervisor Agent with full project context. Review the short debate and "
            "declare a winner based on technical facts and logic. Be decisive. Respond as strict "
            'JSON: {"winner": str, "loser": str, "justification": str, "confidence": int, '
            '"recommended_action": str}'
        )
        user = (
            f"Topic: {topic}\n"
            f"Context: {json.dumps(context, default=str)[:2000]}\n"
            f"Transcript:\n{json.dumps(transcript, default=str)[:5000]}"
        )
        verdict = self.ask_json(system, user, max_tokens=900)

        doc_name = f"debate_{_normalize(topic)}_{int(time.time())}.md"
        positions_md = "\n".join(
            f"- **{agent}**: {pos.get('chosen', pos.get('description', ''))} — "
            f"{pos.get('justification', pos.get('recommended_change', ''))}"
            for agent, pos in positions.items()
        )
        transcript_md = "\n\n".join(
            f"**Round {t['round']} — {t['agent']}:**\n{t['argument']}" for t in transcript
        )
        doc = (
            f"# Debate: {topic}\n\n## Sides\n{positions_md}\n\n## Transcript\n{transcript_md}\n\n"
            f"## Verdict\n**Winner:** {verdict.get('winner')}\n"
            f"**Loser:** {verdict.get('loser')}\n\n"
            f"{verdict.get('justification', '')}\n\n"
            f"Confidence: {verdict.get('confidence')}%\n\n"
            f"**Recommended action:** {verdict.get('recommended_action', '')}\n"
        )
        self.write_doc(doc_name, doc)

        debate_record = {
            "topic": topic,
            "positions": list(positions.values()),
            "transcript": transcript,
            "verdict": verdict,
            "doc": f"docs/{doc_name}",
            "ts": time.time(),
        }

        def _mut(s: dict) -> None:
            s["debates"].append(debate_record)

        store.mutate(self.run_id, _mut)
        self.log(
            f"Dispute '{topic}' resolved. Winner: {verdict.get('winner')}; "
            f"action: {verdict.get('recommended_action', 'none')}",
            "success",
        )
        self.status("success", 100)
        return verdict

    def mediate_architecture_security(
        self, architecture: dict, security_issue: dict
    ) -> dict:
        """Uses the generic short debate to resolve architecture vs. security."""
        return self.mediate_dispute(
            topic="architecture_security",
            agent_a="architect",
            agent_b="security",
            position_a={
                "chosen": architecture.get("chosen", "option1"),
                "justification": architecture.get("justification", ""),
            },
            position_b={
                "chosen": security_issue.get("recommended_change", "change_architecture"),
                "justification": security_issue.get("description", ""),
                "recommended_change": security_issue.get("recommended_change", ""),
            },
            context={
                "source": "security_architecture_concern",
                "architecture": architecture,
                "security_issue": security_issue,
            },
        )

    def score_reliability(self) -> dict:
        """Produces a deterministic, calibrated reliability scorecard from the
        actual observed signals (deployment success, test results, retries,
        debates, review acceptance, generated project size)."""
        state = store.load(self.run_id)
        self.log("Scoring reliability from observed signals...")

        agents = state["agents"]
        deploy_status = state.get("deployment", {}).get("status")
        qa_status = agents["qa"].get("status")
        security_status = agents["security"].get("status")
        backend_retries = agents["backend"].get("retries", 0)
        qa_retries = agents["qa"].get("retries", 0)
        pr_acceptance = state.get("stats", {}).get("pr_acceptance_pct")
        num_debates = len(state.get("debates", []))
        num_issues = len(
            (state.get("pipeline_context", {}).get("plan") or {}).get("issues", [])
        )
        num_project_files = len(
            list(store.project_dir(self.run_id).rglob("*"))
            if store.project_dir(self.run_id).exists()
            else []
        )

        code_quality = 70
        if deploy_status == "running":
            code_quality += 20
        if pr_acceptance is not None:
            code_quality = int((code_quality + pr_acceptance) / 2)
        code_quality = max(0, min(100, code_quality - backend_retries * 10))

        security = 60
        if security_status == "success":
            security += 30
        if num_debates == 0:
            security += 5
        security = max(0, min(100, security))

        architecture = 75 if agents["architect"].get("status") == "success" else 40
        architecture = max(0, min(100, architecture - num_debates * 5))

        if qa_status == "success":
            test_coverage = 95 - qa_retries * 15
        elif qa_status == "failed":
            test_coverage = 30
        else:
            test_coverage = 0
        test_coverage = max(0, min(100, test_coverage))

        hallucination_risk = 30
        if deploy_status == "running" and qa_status == "success":
            hallucination_risk -= 20
        hallucination_risk += num_debates * 5 + backend_retries * 3
        hallucination_risk = max(0, min(100, hallucination_risk))

        if num_project_files < 8 and num_issues <= 5:
            complexity = "low"
        elif num_project_files < 20 and num_issues <= 12:
            complexity = "medium"
        else:
            complexity = "high"

        estimated_bugs = 0
        if qa_status == "failed":
            estimated_bugs += 2
        estimated_bugs += backend_retries + qa_retries + num_debates
        if complexity == "high":
            estimated_bugs += 2
        estimated_bugs = max(0, min(10, estimated_bugs))

        data = {
            "code_quality": code_quality,
            "security": security,
            "architecture": architecture,
            "test_coverage": test_coverage,
            "hallucination_risk": hallucination_risk,
            "complexity": complexity,
            "estimated_bugs": estimated_bugs,
        }

        def _mut(s: dict) -> None:
            s["reliability"] = data

        store.mutate(self.run_id, _mut)
        self.write_doc(
            "reliability_scorecard.md",
            "# AI Reliability Scorecard\n\n```json\n" + json.dumps(data, indent=2) + "\n```\n",
        )
        return data

    def compute_final_stats(self) -> dict:
        state = store.load(self.run_id)
        usage = state.get("_usage", [])
        total_tokens = sum(u.get("prompt_tokens", 0) + u.get("completion_tokens", 0) for u in usage)
        total_cost = sum(u.get("cost_usd", 0) for u in usage)
        total_latency = sum(u.get("latency", 0) for u in usage)
        qa_status = state["agents"]["qa"].get("status")
        deploy_status = state.get("deployment", {}).get("status")

        reliability = state.get("reliability", {})

        def _score(key: str) -> float | None:
            value = reliability.get(key)
            if not isinstance(value, (int, float)):
                return None
            if key == "estimated_bugs":
                # estimated_bugs is on a 0-10 scale; normalize to 0-100 so it
                # can be averaged with the other percentage metrics.
                return max(0.0, 100.0 - value * 10.0)
            return float(value)

        numeric_scores = [score for key in reliability.keys() if (score := _score(key)) is not None]
        reliability_avg = round(sum(numeric_scores) / len(numeric_scores), 1) if numeric_scores else None

        stats = {
            "compilation_success_pct": 100 if deploy_status == "running" else 0,
            "tests_passed_pct": 100 if qa_status == "success" else (0 if qa_status == "failed" else None),
            "pr_acceptance_pct": state.get("stats", {}).get("pr_acceptance_pct"),
            "latency_seconds": round(total_latency, 2),
            "token_usage": total_tokens,
            "cost_usd": round(total_cost, 4),
            "reliability_avg": reliability_avg,
        }

        history_entry = {
            "run_id": self.run_id,
            "ts": time.time(),
            "tests_passed_pct": stats["tests_passed_pct"],
            "compilation_success_pct": stats["compilation_success_pct"],
            "reliability_avg": reliability_avg,
        }
        history = _append_regression(history_entry)
        stats["regression_history"] = history

        def _mut(s: dict) -> None:
            s.setdefault("stats", {}).update(stats)

        store.mutate(self.run_id, _mut)
        return stats
