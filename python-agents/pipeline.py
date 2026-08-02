"""Planner-driven Forge AI pipeline.

The Architect runs first and locks in the architecture. The Planner then
produces a schedule of agent steps. The Executor runs those steps, respecting
dependencies. Security and Reviewer findings can trigger short Supervisor
debates or Planner replans. Pause/resume/stop are checked between steps.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from typing import Any

from agents.architect import ArchitectAgent
from agents.backend import BackendAgent
from agents.frontend import FrontendAgent
from agents.planner import PlannerAgent
from agents.qa import QAAgent
from agents.reviewer import ReviewerAgent
from agents.security import SecurityAgent
from agents.supervisor import SupervisorAgent
from builder import DeploymentManager, get_manager
from config import settings
from llm_client import LLMConfigurationError, LLMOutputError
from storage import store

RESUME_WINDOW_SECONDS = 20 * 60


def _set_run_status(run_id: str, status: str) -> None:
    store.mutate(run_id, lambda s: s.__setitem__("status", status))


def _fail_run(run_id: str, reason: str) -> None:
    def _mut(state: dict[str, Any]) -> None:
        state["status"] = "failed"
        state["error"] = reason

    store.mutate(run_id, _mut)


def _read_project_files(run_id: str, limit: int = 14, chars: int = 4000) -> dict[str, str]:
    proj = store.project_dir(run_id)
    files: dict[str, str] = {}
    if not proj.exists():
        return files
    for path in sorted(proj.rglob("*")):
        if path.is_file() and "node_modules" not in path.parts:
            try:
                files[str(path.relative_to(proj))] = path.read_text(encoding="utf-8", errors="ignore")[:chars]
            except Exception:
                continue
            if len(files) >= limit:
                break
    return files


def _update_readme(run_id: str, step: str, detail: str) -> None:
    state = store.load(run_id)
    lines = [
        f"# Forge AI Project README\n\n**Original request:** {state['prompt']}\n",
        f"## Current Progress — {step}\n\n{detail}\n",
        "## Agent Status\n\n| Agent | Status | Progress |",
        "|-------|--------|----------|",
    ]
    for name, agent_state in state["agents"].items():
        lines.append(f"| {name} | {agent_state['status']} | {agent_state.get('progress', 0)}% |")
    lines.append("\n## Key Decisions & Justifications\n")
    for name, agent_state in state["agents"].items():
        for decision in agent_state.get("decisions", []):
            topic = decision.get("topic", "?")
            chosen = decision.get("chosen", "?")
            justification = decision.get("justification", "")
            lines.append(f"- **{name} / {topic}**: {chosen} — {justification}")
            if decision.get("alternatives"):
                lines.append(
                    f"  - *Alternatives rejected:* {json.dumps(decision['alternatives'], default=str)}"
                )
    lines.append("\n## Quick Start\n")
    project_dir = store.project_dir(run_id)
    if (project_dir / "package.json").exists():
        lines.append(
            "```bash\n"
            f"cd {project_dir}\n"
            "npm install\n"
            "npm start\n"
            "```\n\n"
            "The server listens on `process.env.PORT` (default 4100). "
            "Visit `http://localhost:<PORT>/api/health` to verify it is running."
        )
    else:
        lines.append("Project files are still being generated. Check back after the Backend step.")
    lines.append(
        "\n## Production Deployment\n"
        "See `docs/DEPLOYMENT.md` for detailed instructions for Vercel, Netlify, "
        "GitHub Pages, Render, Railway, Fly.io, Docker and external databases."
    )
    lines.append("\n---\n*This README is regenerated after every agent step.*")
    store.write_doc(run_id, "README.md", "\n".join(lines))


def _generate_deployment_readme(run_id: str, ctx: dict[str, Any]) -> None:
    """Writes a comprehensive deployment guide tailored to the generated project."""
    state = store.load(run_id)
    architecture = ctx.get("architecture", {})
    deployment = ctx.get("deployment", {}) or state.get("deployment", {})
    outputs = ctx.get("outputs", {})

    backend_output: dict[str, Any] | None = None
    frontend_output: dict[str, Any] | None = None
    for value in outputs.values():
        if isinstance(value, dict):
            if "database" in value and "api" in value:
                backend_output = value
            elif "files" in value and "state_management" in value:
                frontend_output = value

    db_choice = backend_output.get("database", {}) if backend_output else {}
    db_name = db_choice.get("database", "in-memory / JSON file") if isinstance(db_choice, dict) else str(db_choice)
    has_backend = bool(architecture.get("has_backend", bool(backend_output)))
    api_style = architecture.get("api_style", "none (static)")
    deployment_target = architecture.get("deployment_target", "localhost")

    env_vars = set()
    project_dir = store.project_dir(run_id)
    if project_dir.exists():
        for path in project_dir.rglob("*.js"):
            if "node_modules" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                for match in re.finditer(r"process\.env\.(\w+)", text):
                    env_vars.add(match.group(1))
            except Exception:
                continue

    env_table = "| Variable | Required | Notes |\n|----------|----------|-------|\n"
    for var in sorted(env_vars):
        env_table += f"| `{var}` | {'✅' if var in ('PORT', 'DATABASE_URL', 'NODE_ENV') else '❌ (set if used)'} | Used by generated server |\n"
    if not env_vars:
        env_table += "| — | — | No `process.env` references detected. |\n"

    live_url = deployment.get("url", "")
    backend_deploy = "" if not has_backend else (
        "### Render / Railway / Fly.io / Heroku\n\n"
        "1. Push the `project/` folder to a new GitHub repository.\n"
        "2. Create a web service with:\n"
        "   - **Build command:** `npm install`\n"
        "   - **Start command:** `npm start`\n"
        "3. Set environment variables (see table below).\n"
        "4. Ensure the host forwards traffic to the port set by `PORT` (default `4100`).\n\n"
        "### Docker (single container)\n\n"
        "```dockerfile\n"
        "FROM node:20-alpine\n"
        "WORKDIR /app\n"
        "COPY package*.json ./\n"
        "RUN npm install --omit=dev\n"
        "COPY . .\n"
        "EXPOSE 4100\n"
        "CMD [\"npm\", \"start\"]\n"
        "```\n\n"
        "Build and run:\n"
        "```bash\n"
        "docker build -t forge-ai-app .\n"
        "docker run -p 4100:4100 -e PORT=4100 forge-ai-app\n"
        "```\n\n"
    )

    frontend_deploy = (
        "### Vercel\n\n"
        "1. Import the `project/public` folder (or drag-and-drop in the dashboard).\n"
        "2. Framework preset: **Other**.\n"
        "3. The publish directory is `public/`.\n"
        "4. Add any required environment variables under **Settings > Environment Variables**.\n\n"
        "### Netlify\n\n"
        "1. Create a new site and deploy the `project/public` folder.\n"
        "2. Build command: leave empty.\n"
        "3. Publish directory: `public/`.\n\n"
        "### GitHub Pages\n\n"
        "1. Push the `project/public` contents to a repository.\n"
        "2. Enable GitHub Pages from the repository settings.\n"
        "3. Choose the branch/folder that contains the static files.\n\n"
    )

    db_section = (
        f"## Database — {db_name}\n\n"
        + (
            "This project uses an embedded or in-memory store. No external database server is "
            "required. Data is persisted to JSON files or lives only for the lifetime of the process.\n\n"
            if "in-memory" in db_name.lower() or "json" in db_name.lower()
            else (
                f"The project expects a running {db_name} server. Set the connection string in the "
                "environment (e.g. `DATABASE_URL`) and run any schema migrations before starting the app.\n\n"
            )
        )
    )

    health_section = (
        "## Health Verification\n\n"
        "Once the server is running, verify it with:\n"
        "```bash\n"
        "curl http://localhost:4100/api/health\n"
        "```\n\n"
        + (
            f"Live deployment URL recorded by Forge AI: `{live_url}`\n\n"
            if live_url
            else ""
        ) +
        "Run the generated smoke tests (if available) with:\n"
        "```bash\n"
        "npx vitest run\n"
        "npx playwright test\n"
        "```\n\n"
    )

    reliability = state.get("reliability", {})
    qa_stats = state.get("stats", {})
    signals = (
        f"- QA status: `{state['agents'].get('qa', {}).get('status', 'unknown')}`\n"
        f"- Deployment status: `{deployment.get('status', 'unknown')}`\n"
        f"- Reliability average: `{qa_stats.get('reliability_avg', 'n/a')}`\n"
        f"- Estimated bugs: `{reliability.get('estimated_bugs', 'n/a')}`\n"
    )

    doc = (
        f"# Forge AI Deployment Guide\n\n"
        f"**Generated for:** {state['prompt']}\n\n"
        f"**Architecture:** {architecture.get('chosen', 'unknown')} — {architecture.get('justification', '')}\n\n"
        f"**API style:** {api_style}\n"
        f"**Deployment target:** {deployment_target}\n"
        f"**Has backend:** {'yes' if has_backend else 'no'}\n\n"
        "## Local Development\n\n"
        "```bash\n"
        f"cd {project_dir}\n"
        "npm install\n"
        "npm start\n"
        "```\n\n"
        "The server listens on `process.env.PORT` (default `4100`).\n\n"
        f"{db_section}\n"
        f"{backend_deploy}"
        f"{frontend_deploy}"
        f"{health_section}"
        "## Environment Variables\n\n"
        f"{env_table}\n\n"
        "## Run Signals\n\n"
        f"{signals}\n"
        "---\n"
        "*This guide is generated automatically by Forge AI and reflects the final checkpoint.*"
    )
    store.write_doc(run_id, "DEPLOYMENT.md", doc)


def _check_control(run_id: str) -> bool:
    state = store.load(run_id)
    control = state.get("control", {"paused": False, "stopped": False})
    if control.get("stopped"):
        store.log(run_id, "supervisor", "Run stopped by user request.", "warning")
        _set_run_status(run_id, "stopped")
        return False
    if control.get("paused"):
        store.mutate(run_id, lambda s: s.__setitem__("paused_at", time.time()))
        store.log(run_id, "supervisor", "Run paused between agent steps.", "info")
        _set_run_status(run_id, "paused")
        return False
    return True


def _save_context(run_id: str, ctx: dict[str, Any]) -> None:
    store.set_pipeline_context(run_id, **ctx)


def _clear_project(run_id: str) -> None:
    proj = store.project_dir(run_id)
    if proj.exists():
        shutil.rmtree(proj)
    proj.mkdir(parents=True, exist_ok=True)


class PipelineExecutor:
    def __init__(self, run_id: str, prompt: str) -> None:
        self.run_id = run_id
        self.prompt = prompt
        self.agents = {
            "architect": ArchitectAgent(run_id),
            "planner": PlannerAgent(run_id),
            "backend": BackendAgent(run_id),
            "frontend": FrontendAgent(run_id),
            "qa": QAAgent(run_id),
            "security": SecurityAgent(run_id),
            "reviewer": ReviewerAgent(run_id),
            "supervisor": SupervisorAgent(run_id),
        }

    def run(self, resume_from_stage: int = 0) -> None:
        _set_run_status(self.run_id, "running")
        store.set_control(self.run_id, paused=False, stopped=False)
        store.mutate(self.run_id, lambda s: s.__setitem__("error", None))

        try:
            ctx = store.load(self.run_id).get("pipeline_context", {})

            if resume_from_stage <= 0:
                if not _check_control(self.run_id):
                    return
                ctx = self._run_architect(ctx)

            if resume_from_stage <= 1:
                if not _check_control(self.run_id):
                    return
                ctx = self._run_planner(ctx)

            ctx = self._execute_schedule(ctx)
            if ctx is None:
                return

            # Reviewer requirements check after the schedule has run.
            if not _check_control(self.run_id):
                return
            ctx = self._run_reviewer_review(ctx)
            if ctx is None:
                return

            if not _check_control(self.run_id):
                return
            self.agents["supervisor"].score_reliability()
            self.agents["supervisor"].compute_final_stats()
            _generate_deployment_readme(self.run_id, ctx)
            _update_readme(self.run_id, "Complete", "All agents finished. Download the ZIP or inspect the project/ folder.")
            store.create_checkpoint(self.run_id, "Run complete: deployment README added", tag="final")
            _set_run_status(self.run_id, "completed")
        except LLMConfigurationError as exc:
            _fail_run(self.run_id, f"LLM not configured: {exc}")
        except LLMOutputError as exc:
            _fail_run(self.run_id, f"LLM produced invalid output: {exc}")
        except Exception as exc:
            _fail_run(self.run_id, f"Pipeline error: {exc}")

    def _run_architect(self, ctx: dict[str, Any]) -> dict[str, Any]:
        state = store.load(self.run_id)
        if state.get("restart_architecture"):
            _clear_project(self.run_id)
            ctx = {}
            store.mutate(self.run_id, lambda s: s.__setitem__("restart_architecture", False))
            store.log(self.run_id, "supervisor", "Restarting architecture with recommendations.", "warning")

        store.log(self.run_id, "architect", "Deciding architecture, tech stack, ADR and CTQs...")
        architecture = self.agents["architect"].run(self.prompt)
        ctx["architecture"] = architecture
        ctx["outputs"] = {}
        ctx["step_index"] = 0
        ctx["schedule"] = []
        ctx["deployment"] = {"success": False}
        _save_context(self.run_id, ctx)
        store.create_checkpoint(self.run_id, "Architecture decided", tag="architecture")
        _update_readme(
            self.run_id,
            "Architecture",
            f"Architect selected **{architecture.get('chosen')}**. ADR, CTQs and Mermaid diagram written.",
        )
        return ctx

    def _run_planner(self, ctx: dict[str, Any]) -> dict[str, Any]:
        architecture = ctx["architecture"]
        store.log(self.run_id, "planner", "Creating agent execution schedule...")
        result = self.agents["planner"].create_schedule(self.prompt, architecture)
        ctx["schedule"] = result["schedule"]
        ctx["plan"] = {"issues": result.get("issues", [])}
        ctx["step_index"] = 0
        ctx["outputs"] = {}
        _save_context(self.run_id, ctx)
        store.create_checkpoint(self.run_id, "Planner schedule created", tag="planning")
        _update_readme(
            self.run_id,
            "Planning",
            f"Planner created a {len(ctx['schedule'])}-step schedule: {result.get('summary', '')}",
        )
        return ctx

    def _normalize_action(self, agent_name: str, action: str) -> str:
        if agent_name == "deploy":
            # Anything the planner calls the deploy step should actually deploy.
            return "deploy"
        if action != "generate":
            return action
        mapping = {
            "backend": "generate",
            "frontend": "generate",
            "security": "audit",
            "qa": "test",
            "reviewer": "review",
            "supervisor": "resolve",
        }
        return mapping.get(agent_name, action)

    def _execute_schedule(self, ctx: dict[str, Any]) -> dict[str, Any] | None:
        schedule = ctx.get("schedule", [])
        step_index = ctx.get("step_index", 0)
        outputs = ctx.get("outputs", {})

        while step_index < len(schedule):
            if not _check_control(self.run_id):
                ctx["step_index"] = step_index
                _save_context(self.run_id, ctx)
                return None

            raw_step = schedule[step_index]
            step = dict(raw_step)
            step["action"] = self._normalize_action(step["agent"], step["action"])

            missing = [dep for dep in step.get("depends_on", []) if dep not in outputs]
            if missing:
                if step["agent"] == "deploy":
                    store.log(
                        self.run_id,
                        "planner",
                        f"Deploy step {step['id']} has missing dependencies {missing}; "
                        "running it anyway because a live deployment is required for QA.",
                        "warning",
                    )
                else:
                    store.log(
                        self.run_id,
                        "planner",
                        f"Skipping step {step['id']}: missing dependencies {missing}.",
                        "warning",
                    )
                    step_index += 1
                    ctx["step_index"] = step_index
                    _save_context(self.run_id, ctx)
                    continue

            store.log(
                self.run_id,
                step["agent"],
                f"Scheduled step {step['id']}: {step['action']} — {step.get('context', '')}",
            )
            result = self._execute_step(step, ctx)
            outputs[step["id"]] = result
            ctx["outputs"] = outputs

            if step["agent"] == "deploy" and isinstance(result, dict):
                ctx["deployment"] = result

            step_index += 1
            ctx["step_index"] = step_index
            _save_context(self.run_id, ctx)

            # Checkpoint after every agent step so logs, reasoning and outputs are snapshotted.
            cp_description = f"{step['agent'].title()} step '{step['id']}' ({step['action']}) complete"
            cp_tag = step["agent"]
            store.create_checkpoint(self.run_id, cp_description, tag=cp_tag)
            self.agents["supervisor"].log(
                f"Checkpoint {len(store.load(self.run_id)['checkpoints'])} recorded for {step['agent']} step {step['id']}.",
                "info",
            )

            if step["agent"] == "security" and step["action"] == "audit":
                ctx = self._handle_security_audit(ctx, result)
                if ctx is None:
                    return None
                schedule = ctx.get("schedule", [])
                step_index = ctx.get("step_index", step_index)
                outputs = ctx.get("outputs", outputs)

        return ctx

    def _execute_step(self, step: dict[str, Any], ctx: dict[str, Any]) -> Any:
        agent_name = step["agent"]
        action = step["action"]
        instructions = step.get("instructions", "")
        architecture = ctx.get("architecture", {})
        outputs = ctx.get("outputs", {})

        try:
            if agent_name == "backend":
                if action == "generate":
                    return self.agents["backend"].generate(self.prompt, architecture, instructions)
                if action == "patch":
                    files = _read_project_files(self.run_id, limit=50)
                    return self.agents["backend"].apply_patch(instructions, files)

            if agent_name == "frontend":
                backend_api = {}
                for dep in step.get("depends_on", []):
                    dep_out = outputs.get(dep)
                    if isinstance(dep_out, dict) and "api" in dep_out:
                        backend_api = dep_out["api"]
                if action == "generate":
                    return self.agents["frontend"].generate(self.prompt, architecture, backend_api, instructions)
                if action == "patch":
                    files = _read_project_files(self.run_id, limit=50)
                    return self.agents["frontend"].apply_patch(instructions, files)

            if agent_name == "security":
                if action == "audit":
                    return self.agents["security"].audit(self.prompt, architecture)
                if action == "patch":
                    files = _read_project_files(self.run_id, limit=50)
                    return self.agents["security"].apply_patch(instructions, files)
                if action == "dynamic":
                    deployment = ctx.get("deployment", {})
                    url = deployment.get("url")
                    if not url:
                        raise RuntimeError("Dynamic security scan scheduled before deployment URL is available")
                    return self.agents["security"].run_dynamic(url)

            if agent_name == "qa":
                if action == "quality":
                    return self.agents["qa"].quality_check(self.prompt)
                if action in ("test", "generate"):
                    deployment = ctx.get("deployment", {})
                    if not deployment.get("success"):
                        store.log(self.run_id, "qa", "Deployment not ready yet; attempting an emergency deploy before QA...", "warning")
                        deployment = _deploy_with_retries(self.run_id, self.agents["backend"])
                        ctx["deployment"] = deployment
                        _save_context(self.run_id, ctx)
                    if not deployment.get("success"):
                        store.log(self.run_id, "qa", "Deployment did not succeed; skipping QA tests.", "warning")
                        store.set_status(self.run_id, "qa", "failed", 0)
                        return {"skipped": True, "reason": "deployment_failed"}
                    base_url = deployment.get("url")
                    try:
                        self.agents["qa"].generate_tests(self.prompt)
                    except Exception as exc:
                        store.log(self.run_id, "qa", f"Test generation failed: {exc}; continuing with fallback tests.", "warning")
                    smoke_result = self.agents["qa"].execute_tests(base_url)
                    fuzz_result = self.agents["qa"].fuzz(base_url)
                    try:
                        quality_result = self.agents["qa"].quality_check(self.prompt)
                    except Exception as exc:
                        store.log(self.run_id, "qa", f"Quality check failed: {exc}; continuing.", "warning")
                        quality_result = {"success": False, "score": 0, "summary": str(exc)}

                    # Quality check currently forces the QA agent status to "success".
                    # Correct the status here so it reflects whether the smoke tests actually passed.
                    qa_success = smoke_result.get("success", False)
                    store.set_status(
                        self.run_id,
                        "qa",
                        "success" if qa_success else "failed",
                        100 if qa_success else 70,
                    )
                    return {
                        "smoke": smoke_result,
                        "fuzz": fuzz_result,
                        "quality": quality_result,
                        "success": qa_success,
                    }

            if agent_name == "reviewer":
                if action in ("review", "generate"):
                    return self.agents["reviewer"].run()
                if action == "requirements":
                    return self.agents["reviewer"].review_codebase(self.prompt, architecture)

            if agent_name == "supervisor":
                if action in ("debate", "resolve"):
                    return self.agents["supervisor"].detect_and_resolve_conflicts()

            if agent_name == "deploy":
                if action in ("deploy", "generate"):
                    result = _deploy_with_retries(self.run_id, self.agents["backend"])
                    store.set_status(
                        self.run_id,
                        "deploy",
                        "success" if result.get("success") else "failed",
                        100,
                    )
                    return result

            raise ValueError(f"Unknown step: {agent_name}.{action}")
        except Exception:
            store.log(self.run_id, agent_name, f"Step {step['id']} failed.", "error")
            if agent_name in store.load(self.run_id)["agents"]:
                store.set_status(self.run_id, agent_name, "failed", 100)
            raise

    def _handle_security_audit(
        self, ctx: dict[str, Any], audit_result: dict[str, Any]
    ) -> dict[str, Any] | None:
        arch_issue = audit_result.get("architecture_issue", {}) or {}
        debate_findings = audit_result.get("debate_findings", [])
        patch_findings = audit_result.get("patch_findings", [])

        # Architecture-level concern
        if arch_issue.get("present"):
            verdict = self.agents["supervisor"].mediate_architecture_security(
                ctx["architecture"], arch_issue
            )
            if verdict.get("winner") == "security":
                ctx["architecture_recommendation"] = verdict.get("recommended_action", "")
                store.mutate(self.run_id, lambda s: s.__setitem__("restart_architecture", True))
                return self._restart_from_architect(ctx)
            else:
                mitigations = verdict.get("recommended_action", "")
                if mitigations:
                    patch_findings.append(
                        {
                            "severity": "medium",
                            "file": "architecture",
                            "description": mitigations,
                            "target_agent": "backend",
                            "patch_instructions": mitigations,
                        }
                    )

        # Component-level concerns that warrant a debate
        winning_patches = []
        for finding in debate_findings:
            target = finding.get("target_agent")
            if target not in ("backend", "frontend"):
                winning_patches.append(finding)
                continue
            verdict = self.agents["supervisor"].mediate_dispute(
                topic=f"security_{target}_concern",
                agent_a="security",
                agent_b=target,
                position_a={
                    "chosen": "fix_vulnerability",
                    "justification": finding.get("description", ""),
                    "recommended_change": finding.get("patch_instructions", ""),
                },
                position_b={
                    "chosen": "keep_existing_code",
                    "justification": f"{target} agent believes the current implementation is acceptable.",
                },
                context={
                    "source": "security_component_concern",
                    "finding": finding,
                    "affected_files": finding.get("file"),
                },
            )
            if verdict.get("winner") == "security":
                winning_patches.append(finding)
                store.log(
                    self.run_id,
                    "supervisor",
                    f"Security won debate vs {target}; {finding.get('file')} must be patched.",
                    "warning",
                )
            else:
                store.log(
                    self.run_id,
                    "supervisor",
                    f"{target.title()} won debate vs security; no patch required for {finding.get('file')}.",
                    "info",
                )

        all_patch_findings = patch_findings + winning_patches
        if all_patch_findings:
            affected = list({f.get("target_agent") for f in all_patch_findings if f.get("target_agent")})
            reason = "Security audit findings: " + "; ".join(
                f"[{f.get('severity', '?').upper()}] {f.get('file')}: {f.get('description')}"
                for f in all_patch_findings
            )
            store.log(self.run_id, "planner", f"Re-planning patches for: {', '.join(affected)}")
            existing_files = _read_project_files(self.run_id, limit=50)
            replan = self.agents["planner"].replan(
                self.prompt,
                ctx["architecture"],
                reason,
                affected,
                existing_files,
                ctx.get("schedule", []),
            )
            current_index = ctx.get("step_index", 0)
            new_steps = replan.get("schedule", [])
            schedule = ctx.get("schedule", [])
            for i, s in enumerate(new_steps):
                s["id"] = f"patch-{current_index}-{i}"
            ctx["schedule"] = schedule[:current_index] + new_steps + schedule[current_index:]
            _save_context(self.run_id, ctx)
            _update_readme(
                self.run_id,
                "Re-planning",
                f"Security raised {len(all_patch_findings)} issue(s). Planner added {len(new_steps)} patch step(s) for {', '.join(affected)}.",
            )
        else:
            store.log(self.run_id, "security", "No security findings requiring patches.", "success")

        return ctx

    def _run_reviewer_review(self, ctx: dict[str, Any]) -> dict[str, Any] | None:
        """Runs reviewer requirements check after schedule execution."""
        store.log(self.run_id, "reviewer", "Reviewing whole codebase against user requirements...")
        report = self.agents["reviewer"].review_codebase(self.prompt, ctx["architecture"])

        if not report.get("architecture_adequate", True):
            store.log(
                self.run_id,
                "reviewer",
                "Reviewer believes the architecture is inadequate. Starting debate with Architect.",
                "warning",
            )
            verdict = self.agents["supervisor"].mediate_dispute(
                topic="architecture_adequacy",
                agent_a="reviewer",
                agent_b="architect",
                position_a={
                    "chosen": "restart_architecture",
                    "justification": "; ".join(report.get("missing_requirements", []))
                    or "Architecture cannot satisfy user requirements.",
                },
                position_b={
                    "chosen": ctx["architecture"].get("chosen", "option1"),
                    "justification": ctx["architecture"].get("justification", ""),
                },
                context={
                    "source": "reviewer_architecture_concern",
                    "missing_requirements": report.get("missing_requirements", []),
                    "architecture": ctx["architecture"],
                },
            )
            if verdict.get("winner") == "reviewer":
                store.log(
                    self.run_id,
                    "supervisor",
                    "Reviewer won architecture debate. Restarting pipeline.",
                    "warning",
                )
                ctx["architecture_recommendation"] = verdict.get("recommended_action", "")
                store.mutate(self.run_id, lambda s: s.__setitem__("restart_architecture", True))
                return self._restart_from_architect(ctx)
            else:
                store.log(
                    self.run_id,
                    "supervisor",
                    "Architect won debate. Reviewer changes will be patched instead.",
                    "info",
                )
                # Force recommended changes into patch queue.
                for change in report.get("recommended_changes", []):
                    change["severity"] = "medium"
                    change["description"] = change.get("description", "")
                    change["patch_instructions"] = change.get("patch_instructions", "")

        if not report.get("requirements_met", True) or report.get("recommended_changes"):
            changes = report.get("recommended_changes", [])
            if changes:
                affected = list({c.get("agent") for c in changes if c.get("agent")})
                reason = "Reviewer findings: " + "; ".join(
                    f"[{c.get('agent')}] {c.get('description')}" for c in changes
                )
                store.log(self.run_id, "planner", f"Re-planning reviewer fixes for: {', '.join(affected)}")
                existing_files = _read_project_files(self.run_id, limit=50)
                replan = self.agents["planner"].replan(
                    self.prompt,
                    ctx["architecture"],
                    reason,
                    affected,
                    existing_files,
                    ctx.get("schedule", []),
                )
                current_index = ctx.get("step_index", 0)
                new_steps = replan.get("schedule", [])
                schedule = ctx.get("schedule", [])
                for i, s in enumerate(new_steps):
                    s["id"] = f"reviewer-patch-{current_index}-{i}"
                ctx["schedule"] = schedule[:current_index] + new_steps + schedule[current_index:]
                _save_context(self.run_id, ctx)
                _update_readme(
                    self.run_id,
                    "Re-planning (Reviewer)",
                    f"Reviewer found unmet requirements. Planner added {len(new_steps)} patch step(s).",
                )
                # Run the new patch steps before final scoring.
                return self._execute_schedule(ctx)
        else:
            store.log(self.run_id, "reviewer", "All requirements appear met.", "success")

        return ctx

    def _restart_from_architect(self, ctx: dict[str, Any]) -> dict[str, Any] | None:
        _clear_project(self.run_id)
        ctx["outputs"] = {}
        ctx["step_index"] = 0
        ctx["schedule"] = []
        ctx["deployment"] = {"success": False}
        recommendation = ctx.get("architecture_recommendation", "")
        _save_context(self.run_id, ctx)
        store.mutate(self.run_id, lambda s: s.__setitem__("restart_architecture", False))

        if not _check_control(self.run_id):
            return None

        system = (
            "You are the Architect Agent. A review of your previous architecture "
            "identified a weakness. Produce a revised architecture that addresses the concern "
            "while still meeting the user's request. Respond with the standard architecture "
            "JSON shape including option1, option2, chosen, justification, adr_markdown, "
            "diagram_mermaid, api_style and deployment_target."
        )
        user = (
            f"Software request: {self.prompt}\n"
            f"Reviewer/Security recommendation: {recommendation}\n"
            "Produce the revised architecture now."
        )
        architecture = self.agents["architect"].ask_json(system, user, max_tokens=3000)
        ctx["architecture"] = architecture
        self.agents["architect"].status("success", 100)
        self.agents["architect"].write_doc(
            "architecture_revised.md",
            f"# Revised Architecture\n\n**Reason:** {recommendation}\n\n"
            f"**Chosen:** {architecture.get('chosen')}\n\n"
            f"## Justification\n{architecture.get('justification', '')}\n\n"
            f"## ADR\n{architecture.get('adr_markdown', '')}\n",
        )
        store.create_checkpoint(self.run_id, "Architecture revised after debate", tag="architecture")
        _update_readme(
            self.run_id,
            "Architecture (revised)",
            f"Architecture restarted after debate. New choice: {architecture.get('chosen')}.",
        )

        return self._run_planner(ctx)


def _deploy_with_retries(run_id: str, backend: BackendAgent) -> dict[str, Any]:
    manager = get_manager(run_id)
    has_backend = manager._has_backend()
    store.log(run_id, "backend", f"Project has backend: {has_backend}. Deploying {'backend server' if has_backend else 'static frontend'}.")
    store.mutate(run_id, lambda s: s.setdefault("pipeline_context", {}).__setitem__("has_backend", has_backend))
    attempts = 0
    last_result: dict[str, Any] = {"success": False}
    while attempts < settings.max_build_retries:
        attempts += 1
        store.log(run_id, "backend", f"Deployment attempt {attempts}: installing & starting server...")
        last_result = manager.deploy()
        if last_result.get("success"):
            store.log(run_id, "backend", f"Deployed successfully at {last_result['url']}", "success")
            return last_result
        store.log(run_id, "backend", f"Deployment attempt {attempts} failed. Diagnosing...", "error")

        def _bump_retries(state: dict[str, Any]) -> None:
            state["agents"]["backend"]["retries"] = state["agents"]["backend"].get("retries", 0) + 1

        store.mutate(run_id, _bump_retries)

        if attempts >= settings.max_build_retries:
            break
        current_files = _read_project_files(run_id)
        instructions = (
            f"The generated project failed to build/start (stage={last_result.get('stage')}). "
            f"Server/install logs:\n{last_result.get('logs', '')[-2000:]}\n"
            "Fix the code so `npm install` succeeds and the server starts and listens on "
            "process.env.PORT, responding with status < 500 on GET /api/health."
        )
        store.log(run_id, "backend", "Fixing...", "info")
        try:
            backend.apply_patch(instructions, current_files)
            store.log(run_id, "backend", "Applied automatic fix. Retrying deployment...", "info")
        except LLMConfigurationError:
            raise
        except Exception as exc:
            store.log(run_id, "backend", f"Auto-fix attempt failed: {exc}", "error")
    store.log(run_id, "backend", "Exhausted retry limit; deployment failed.", "error")
    store.set_status(run_id, "backend", "failed", 100)
    return last_result


def run_pipeline(run_id: str, prompt: str, resume_from_stage: int = 0) -> None:
    PipelineExecutor(run_id, prompt).run(resume_from_stage)


def pause_run(run_id: str) -> dict[str, Any]:
    state = store.load(run_id)
    if state["status"] not in ("running", "pending"):
        raise ValueError(f"Cannot pause run with status '{state['status']}'")
    store.set_control(run_id, paused=True)
    store.log(run_id, "supervisor", "Pause requested. Will pause after the current agent step.", "info")
    return {"status": "pause_requested"}


def resume_run(run_id: str) -> dict[str, Any]:
    state = store.load(run_id)
    if state["status"] != "paused":
        raise ValueError(f"Cannot resume run with status '{state['status']}'")
    paused_at = state.get("paused_at")
    if paused_at and (time.time() - paused_at) > RESUME_WINDOW_SECONDS:
        store.set_control(run_id, paused=False)
        _set_run_status(run_id, "suspended")
        raise ValueError("Resume window expired. The run has been permanently suspended.")

    ctx = state.get("pipeline_context", {})
    resume_stage = 2 if ctx.get("schedule") else (1 if ctx.get("architecture") else 0)
    store.set_control(run_id, paused=False, stopped=False)
    store.log(run_id, "supervisor", f"Resuming pipeline from stage {resume_stage}.", "info")
    PipelineExecutor(run_id, state["prompt"]).run(resume_from_stage=resume_stage)
    return {"status": "resumed", "stage": resume_stage}


def stop_run(run_id: str) -> dict[str, Any]:
    state = store.load(run_id)
    if state["status"] not in ("running", "pending", "paused"):
        raise ValueError(f"Cannot stop run with status '{state['status']}'")
    store.set_control(run_id, stopped=True, paused=False)
    get_manager(run_id).stop()
    _set_run_status(run_id, "stopped")
    store.log(run_id, "supervisor", "Run stopped by user. Cannot be resumed.", "warning")
    return {"status": "stopped"}


def redeploy_run(run_id: str) -> dict[str, Any]:
    state = store.load(run_id)
    if not store.project_dir(run_id).exists() or not (store.project_dir(run_id) / "package.json").exists():
        raise ValueError("Deployment stage has not been reached yet. No project files to deploy.")
    deployment = state.get("deployment", {})
    url = deployment.get("url")
    if url:
        import requests
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code < 500:
                raise ValueError(f"Deployment is already live at {url}")
        except requests.RequestException:
            pass
    manager = get_manager(run_id)
    manager.stop()
    result = manager.deploy()
    if result.get("success"):
        store.log(run_id, "backend", f"Re-deployed successfully at {result['url']}", "success")
    else:
        store.log(run_id, "backend", "Re-deployment failed.", "error")
    return result


def run_debug(run_id: str, question: str) -> dict[str, Any]:
    """Natural Language Debugger (kept for compatibility)."""
    store.create_checkpoint(run_id, f"Pre-debug snapshot: {question}", tag="pre-debug")

    from agents.backend import BackendAgent as _Backend
    from agents.frontend import FrontendAgent as _Frontend
    from agents.qa import QAAgent as _QA
    from agents.security import SecurityAgent as _Security

    trace_path = [
        ("frontend", "Browser/UI layer and client-side state management", _Frontend(run_id)),
        ("backend", "API layer and business logic", _Backend(run_id)),
        ("security", "Data access, auth, permission checks and external services", _Security(run_id)),
        ("qa", "Runtime behaviour, latency and test coverage", _QA(run_id)),
    ]

    def _set_debug(payload: dict[str, Any]) -> None:
        store.mutate(run_id, lambda s: s.__setitem__("active_debug", payload))

    trace_results = []
    bottleneck = None
    for name, description, agent in trace_path:
        _set_debug({"question": question, "status": "tracing", "step": name, "trace": trace_results})
        analysis = agent.trace(question, description)
        trace_results.append({"layer": name, **analysis})
        if analysis.get("is_bottleneck") and not bottleneck:
            bottleneck = {"layer": name, **analysis}

    fix_result = None
    if bottleneck and bottleneck.get("suggested_fix"):
        _set_debug({"question": question, "status": "fixing", "trace": trace_results, "bottleneck": bottleneck})
        current_files = _read_project_files(run_id)
        target = {"frontend": trace_path[0][2], "backend": trace_path[1][2], "security": trace_path[2][2]}.get(
            bottleneck["layer"], trace_path[1][2]
        )
        if hasattr(target, "apply_patch"):
            fix_result = target.apply_patch(bottleneck["suggested_fix"], current_files)

    _set_debug({"question": question, "status": "benchmarking", "trace": trace_results, "bottleneck": bottleneck})
    manager = get_manager(run_id)
    redeploy = manager.deploy()
    benchmark: dict[str, Any] = {"redeployed": redeploy.get("success", False)}
    if redeploy.get("success"):
        import requests as _requests

        try:
            t0 = time.time()
            _requests.get(redeploy["url"] + "/api/health", timeout=5)
            benchmark["response_time_ms"] = round((time.time() - t0) * 1000, 1)
        except Exception:
            benchmark["response_time_ms"] = None

    incident_md = (
        f"# Incident Report\n\n**Question:** {question}\n\n## Trace\n"
        + "\n".join(
            f"- **{t['layer']}**: {t.get('analysis', '')} (bottleneck={t.get('is_bottleneck')})"
            for t in trace_results
        )
        + f"\n\n## Root Cause\n{bottleneck.get('analysis') if bottleneck else 'No clear bottleneck identified.'}\n\n"
        f"## Fix Applied\n{bottleneck.get('suggested_fix') if bottleneck else 'None'}\n\n"
        f"## Benchmark After Fix\n{json.dumps(benchmark)}\n"
    )
    fname = f"incident_{int(time.time())}.md"
    store.write_doc(run_id, fname, incident_md)

    def _mut(state: dict[str, Any]) -> None:
        state["incidents"].append(
            {
                "question": question,
                "trace": trace_results,
                "bottleneck": bottleneck,
                "benchmark": benchmark,
                "report": f"docs/{fname}",
                "ts": time.time(),
            }
        )
        state["active_debug"] = {
            "question": question,
            "status": "done",
            "trace": trace_results,
            "bottleneck": bottleneck,
            "benchmark": benchmark,
        }

    store.mutate(run_id, _mut)
    store.create_checkpoint(run_id, f"Post-debug fix: {question}", tag="post-debug")
    _update_readme(run_id, "Debug Fix", f"Natural Language Debugger addressed: {question}")

    return {
        "trace": trace_results,
        "bottleneck": bottleneck,
        "fix": fix_result,
        "benchmark": benchmark,
        "report": f"docs/{fname}",
    }
