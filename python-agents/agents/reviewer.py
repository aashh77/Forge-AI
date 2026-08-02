from __future__ import annotations

import json

from agents.base import BaseAgent
from storage import store


class ReviewerAgent(BaseAgent):
    name = "reviewer"
    display_name = "Reviewer Agent"

    def _read_project_files(self, limit: int = 50) -> dict[str, str]:
        files: dict[str, str] = {}
        project_dir = store.project_dir(self.run_id)
        if not project_dir.exists():
            return files
        for path in sorted(project_dir.rglob("*")):
            if path.is_file() and "node_modules" not in path.parts:
                try:
                    files[str(path.relative_to(project_dir))] = path.read_text(encoding="utf-8", errors="ignore")[:4000]
                except Exception:
                    continue
                if len(files) >= limit:
                    break
        return files

    def review_codebase(self, user_request: str, architecture: dict) -> dict:
        """Reviews the whole codebase against the original user request and
        architecture. Returns whether requirements are met, whether the
        architecture is adequate, and any missing requirements."""
        self.status("running", 10)
        self.log("Reviewing the whole codebase against the original request...")

        files = self._read_project_files()
        system = (
            "You are the Reviewer Agent inside Forge AI. Review the WHOLE generated codebase "
            "against the original user request and chosen architecture. Decide: (1) are all user "
            "requirements and conditions met? (2) is the chosen architecture adequate for those requirements? "
            "(3) what concrete changes are needed, and which agent should make them? Only flag "
            "architecture as inadequate if the high-level tech stack/framework genuinely cannot "
            "satisfy the request. Respond as strict JSON: "
            '{"requirements_met": bool, "architecture_adequate": bool, '
            '"missing_requirements": [str], "recommended_changes": [{"agent": str, '
            '"description": str, "patch_instructions": str}], '
            '"review_summary": str}'
        )
        user = (
            f"Software request: {user_request}\n"
            f"Architecture: {json.dumps(architecture, default=str)[:2000]}\n"
            f"Generated files: {json.dumps(files, default=str)[:6000]}"
        )
        data = self.ask_json(system, user, max_tokens=3500)

        self.decide(
            topic="requirements_review",
            chosen="requirements_review_complete",
            justification=data.get("review_summary", ""),
            requirements_met=data.get("requirements_met", False),
            architecture_adequate=data.get("architecture_adequate", True),
            missing_requirements=data.get("missing_requirements", []),
        )

        self.log(f"Requirements met: {data.get('requirements_met', False)}")
        self.log(f"Architecture adequate: {data.get('architecture_adequate', True)}")
        for req in data.get("missing_requirements", []):
            self.log(f"Missing requirement: {req}", "warning")
        for change in data.get("recommended_changes", []):
            self.log(
                f"Recommended change for {change.get('agent')}: {change.get('description')}",
                "warning",
            )

        changes = data.get("recommended_changes", [])
        changes_md = "\n".join(
            f"- **{c.get('agent')}**: {c.get('description')}\n  Fix: {c.get('patch_instructions')}"
            for c in changes
        )
        doc = (
            "# Requirements & Codebase Review\n\n"
            f"## Requirements Met\n{data.get('requirements_met', False)}\n\n"
            f"## Architecture Adequate\n{data.get('architecture_adequate', True)}\n\n"
            f"## Missing Requirements\n"
            + "\n".join(f"- {m}" for m in data.get("missing_requirements", []))
            + f"\n\n## Recommended Changes\n{changes_md or 'None'}\n\n"
            f"## Summary\n{data.get('review_summary', '')}\n"
        )
        self.write_doc("requirements_review.md", doc)
        self.commit("Reviewed codebase against user requirements", ["docs/requirements_review.md"])
        self.log("Requirements review complete.", "success")
        self.status("success", 100)
        return data

    def run(self) -> dict:
        """Backward-compatible commit review."""
        self.status("running", 20)
        self.log("Reviewing every commit from every agent...")
        state = store.load(self.run_id)
        commits = []
        for agent_name, agent_state in state["agents"].items():
            for c in agent_state.get("commits", []):
                commits.append({"agent": agent_name, **c})

        system = (
            "You are the Reviewer Agent inside Forge AI. Review each commit made by the "
            "other agents in this run. For each, decide approve or reject, explain why, and "
            "suggest concrete improvements. Respond as strict JSON: "
            '{"reviews": [{"agent": str, "commit_id": str, "approved": bool, '
            '"comments": str, "suggestions": str}], "overall_pr_acceptance_pct": number}'
        )
        user = f"Commits to review:\n{json.dumps(commits, default=str)[:6000]}"
        data = self.ask_json(system, user, max_tokens=3000)

        self.decide(
            topic="code_review",
            chosen=f"{data.get('overall_pr_acceptance_pct', 0)}% PR acceptance",
            justification="Aggregate of per-commit reviews across all agents.",
        )

        for r in data.get("reviews", []):
            status = "approved" if r.get("approved") else "rejected"
            self.log(f"Commit {r.get('commit_id')} by {r.get('agent')}: {status} — {r.get('comments', '')}")

        reviews_md = "\n\n".join(
            f"### {r.get('agent')} — {r.get('commit_id')} — "
            f"{'✅ Approved' if r.get('approved') else '❌ Rejected'}\n"
            f"{r.get('comments', '')}\n\nSuggestions: {r.get('suggestions', '')}"
            for r in data.get("reviews", [])
        )
        doc = f"# Code Review\n\n{reviews_md}\n\n## Overall PR Acceptance: {data.get('overall_pr_acceptance_pct', 0)}%\n"
        self.write_doc("review.md", doc)

        def _mut(s: dict) -> None:
            s.setdefault("stats", {})["pr_acceptance_pct"] = data.get("overall_pr_acceptance_pct", 0)

        store.mutate(self.run_id, _mut)
        self.log("Code review complete.", "success")
        self.status("success", 100)
        return data
