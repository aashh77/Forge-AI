from __future__ import annotations

import json

from agents.base import BaseAgent


# Architect is not scheduled; it runs first and feeds the planner.
SCHEDULABLE_AGENTS = [
    "backend",
    "frontend",
    "security",
    "qa",
    "reviewer",
    "supervisor",
    "deploy",
]


class PlannerAgent(BaseAgent):
    name = "planner"
    display_name = "Planner Agent"

    def create_schedule(self, user_request: str, architecture: dict) -> dict:
        """Produces the initial agent schedule based on the architecture."""
        self.status("running", 10)
        self.log("Designing the agent execution schedule...")

        has_backend = architecture.get("has_backend", True)
        backend_note = (
            "The chosen architecture explicitly omits a custom backend; do NOT schedule the "
            "backend agent. The frontend will be a standalone static app and the deploy step "
            "will serve it with a generated static-file server. "
            if not has_backend
            else ""
        )

        system = (
            "You are the Planner Agent inside Forge AI. Your ONLY job is to assign tasks to the "
            "other agents and decide execution order. You do NOT generate code. You may schedule "
            "agents sequentially, in parallel, or interleaved (e.g. run a security check in the "
            "middle of backend work, or activate frontend before security). "
            + backend_note +
            "Each schedule step must specify: agent, action, dependencies (step ids), and a clear "
            "reason grounded in the architecture. Valid agents: backend, frontend, security, qa, "
            "reviewer, deploy. Valid actions: generate, patch, audit, test, review, "
            "debate, score. Respond as strict JSON with this exact shape: "
            '{"schedule": [{"id": str, "agent": str, "action": str, "depends_on": [str], '
            '"instructions": str, "context": str, "reason": str}], '
            '"schedule_summary": str, "concurrency_notes": str}'
        )
        user = (
            f"Software request: {user_request}\n"
            f"Architecture decision: {json.dumps(architecture, default=str)[:2500]}"
        )
        data = self.ask_json(system, user, max_tokens=3000)
        schedule = self._normalize_schedule(data.get("schedule", []))

        self.decide(
            topic="schedule",
            chosen="agent_execution_schedule",
            justification=data.get("schedule_summary", ""),
            schedule=schedule,
            concurrency_notes=data.get("concurrency_notes", ""),
        )

        self.log(f"Schedule summary: {data.get('schedule_summary', '')}")
        if data.get("concurrency_notes"):
            self.log(f"Concurrency notes: {data['concurrency_notes']}")
        for step in schedule:
            self.log(
                f"Step {step['id']}: {step['agent']} ({step['action']}) — {step['reason']}"
            )

        schedule = self._ensure_deploy_step(schedule)
        self._write_schedule_doc(schedule, data.get("schedule_summary", ""))
        self.log("Initial agent schedule created.", "success")
        self.status("success", 100)
        return {"schedule": schedule, "summary": data.get("schedule_summary", ""), "issues": data.get("issues", [])}

    def _ensure_deploy_step(self, schedule: list[dict]) -> list[dict]:
        """The pipeline must always attempt to deploy the generated code,
        even if the LLM forgets to schedule a deploy step or gives it an
        action we cannot execute."""
        if any(step.get("agent") == "deploy" for step in schedule):
            return schedule

        # Find the last concrete build step to depend on.
        build_ids = [
            step["id"]
            for step in schedule
            if step.get("agent") in ("backend", "frontend")
        ]
        depends_on = build_ids[-1:] if build_ids else []

        deploy_step = {
            "id": f"deploy-{len(schedule) + 1}",
            "agent": "deploy",
            "action": "generate",
            "depends_on": depends_on,
            "instructions": "Deploy the generated project to localhost, verify it is reachable on GET /api/health, and report the URL.",
            "context": "Final deployment step so QA can run tests against a live URL.",
            "reason": "A runnable deployment is required before QA tests can execute.",
        }
        schedule.append(deploy_step)
        self.log("Planner omitted a deploy step; injecting one automatically.", "warning")
        return schedule

    def replan(
        self,
        user_request: str,
        architecture: dict,
        reason: str,
        affected_agents: list[str],
        existing_files: dict[str, str],
        previous_schedule: list[dict],
    ) -> dict:
        """Re-activated later (e.g. by security or reviewer). Schedules patch
        work on the existing code, supplying agents with the pre-existing files
        and the flagged issue so only the needed changes are made."""
        self.status("running", 10)
        self.log(f"Re-planning after: {reason[:120]}")

        system = (
            "You are the Planner Agent inside Forge AI, re-planning because a downstream agent "
            "found an issue. Produce a short schedule of patch steps targeting the affected agents. "
            "Each patch step must include the existing files and the exact change requested. "
            "If backend changes, also schedule a frontend patch step because the frontend may need "
            "to adapt. Valid agents: backend, frontend, security, qa. Valid actions: patch, audit, "
            "test. Respond as strict JSON: "
            '{"schedule": [{"id": str, "agent": str, "action": "patch", "depends_on": [str], '
            '"instructions": str, "context": str, "reason": str}], '
            '"replan_summary": str}'
        )
        user = (
            f"Software request: {user_request}\n"
            f"Architecture: {json.dumps(architecture, default=str)[:1200]}\n"
            f"Issue: {reason}\n"
            f"Affected agents: {', '.join(affected_agents)}\n"
            f"Existing files: {json.dumps(list(existing_files.keys()), default=str)}\n"
            f"Previous schedule: {json.dumps(previous_schedule, default=str)[:1500]}"
        )
        data = self.ask_json(system, user, max_tokens=3000)
        schedule = self._normalize_schedule(data.get("schedule", []))

        self.decide(
            topic="replan",
            chosen="patch_existing_code",
            justification=data.get("replan_summary", ""),
            affected_agents=affected_agents,
            schedule=schedule,
        )

        self.log(f"Replan summary: {data.get('replan_summary', '')}")
        for step in schedule:
            self.log(
                f"Patch step {step['id']}: {step['agent']} — {step['context'][:120]}"
            )

        self._write_schedule_doc(schedule, data.get("replan_summary", ""), filename="replan.md")
        self.log("Replan complete. Patch steps created for existing code.", "success")
        self.status("success", 100)
        return {"schedule": schedule, "summary": data.get("replan_summary", "")}

    def _normalize_schedule(self, schedule: list[dict]) -> list[dict]:
        normalized = []
        for step in schedule:
            agent = step.get("agent", "")
            if agent not in SCHEDULABLE_AGENTS:
                continue
            normalized.append(
                {
                    "id": step.get("id") or f"step-{len(normalized) + 1}",
                    "agent": agent,
                    "action": step.get("action", "generate"),
                    "depends_on": list(step.get("depends_on", []) or []),
                    "instructions": step.get("instructions", ""),
                    "context": step.get("context", ""),
                    "reason": step.get("reason", ""),
                }
            )
        return normalized

    def _write_schedule_doc(self, schedule: list[dict], summary: str, filename: str = "planning.md") -> None:
        lines = ["# Agent Execution Plan\n\n", f"## Summary\n{summary}\n\n", "## Schedule\n\n"]
        for step in schedule:
            lines.append(f"### {step['id']} — {step['agent']} ({step['action']})\n")
            lines.append(f"- **Reason:** {step['reason']}\n")
            lines.append(f"- **Context:** {step['context']}\n")
            lines.append(f"- **Instructions:** {step['instructions']}\n")
            lines.append(f"- **Depends on:** {', '.join(step['depends_on']) or 'none'}\n\n")
        self.write_doc(filename, "".join(lines))
        self.commit(f"Authored {filename}", [f"docs/{filename}"])
