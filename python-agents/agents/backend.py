from __future__ import annotations

import json

from agents.base import BaseAgent


class BackendAgent(BaseAgent):
    name = "backend"
    display_name = "Backend Agent"

    def choose_database(self, user_request: str, architecture: dict) -> dict:
        self.log("Evaluating database options against requirements...")
        system = (
            "You are the Backend Agent inside Forge AI choosing a datastore for a project "
            "that must run entirely on a developer's localhost with zero paid/external "
            "infrastructure by default. Prefer an embedded/file-based or in-memory store "
            "(e.g. a JSON-file store) unless the request explicitly demands a networked "
            "datastore (Redis, Postgres, etc.) — in that case choose it anyway but flag that "
            "an external service must be running separately. Overall, design the backend such that it will work locally definitely. Respond as strict JSON: "
            '{"database": str, "justification": str, "ctq": [str], '
            '"alternatives": [{"name": str, "why_rejected": str}], '
            '"requires_external_service": bool, "confidence": int}'
        )
        user = (
            f"Software request: {user_request}\n"
            f"Chosen architecture: {json.dumps(architecture, default=str)[:2500]}"
        )
        data = self.ask_json(system, user, max_tokens=1500)
        self.decide(
            topic="database",
            chosen=data.get("database", "unknown"),
            justification=data.get("justification", ""),
            ctq=data.get("ctq"),
            alternatives=data.get("alternatives"),
            confidence=data.get("confidence"),
        )
        alt_md = "\n".join(
            f"- **{a.get('name')}** — rejected because {a.get('why_rejected')}"
            for a in data.get("alternatives", [])
        )
        doc = (
            "# Backend Datastore Justification\n\n"
            f"**Chosen:** {data.get('database')}\n\n"
            f"## Justification\n{data.get('justification', '')}\n\n"
            "## CTQ (Critical To Quality)\n" + "\n".join(f"- {c}" for c in data.get("ctq", [])) +
            f"\n\n## Alternatives Considered\n{alt_md}\n"
        )
        self.write_doc("backend_database_justification.md", doc)
        self.log(f"Chose database: {data.get('database')} — {data.get('justification', '')}")
        if data.get("alternatives"):
            self.log(
                "Alternatives rejected: "
                + "; ".join(f"{a.get('name')} ({a.get('why_rejected')})" for a in data["alternatives"])
            )
        return data

    def build_api(
        self,
        user_request: str,
        architecture: dict,
        plan: dict,
        db_choice: dict,
        instructions: str = "",
    ) -> dict:
        self.log("Designing REST API surface...")
        system = (
            "You are the Backend Agent inside Forge AI. Generate a small, fully runnable "
            "Node.js Express backend implementing the requested feature. Hard requirements: "
            "1) package.json MUST include 'express' and 'cors' as dependencies, but you MAY list "
            "any additional packages the business logic legitimately needs (e.g. sqlite3, pg, "
            "dotenv, bcrypt, jsonwebtoken, uuid, etc.). Use 'main: server.js' and no build step. "
            "2) server.js MUST listen on process.env.PORT (fallback 4100), and MUST call "
            "app.use(express.static('public')). "
            '3) Expose GET /api/health returning JSON {"status":"ok"}. '
            "4) Implement REAL business logic (in-memory or JSON-file backed matching the "
            "chosen database strategy) for the requested feature — never placeholders. The database and such should be able to run locally"
            "5) Keep the code compact but complete and syntactically correct JavaScript "
            "(CommonJS, require/module.exports). "
            'Respond as strict JSON: {"files": {"<relative path>": "<file content>"}, '
            '"routes": [{"method": str, "path": str, "purpose": str}], '
            '"dependencies": {"<package-name>": "<semver>"}, '
            '"business_logic_summary": str}'
        )
        user_parts = [
            f"Software request: {user_request}",
            f"Architecture: {json.dumps(architecture, default=str)[:1500]}",
            f"Plan issues: {json.dumps(plan.get('issues', []), default=str)[:1500]}",
            f"Database decision: {json.dumps(db_choice, default=str)[:800]}",
        ]
        if instructions:
            user_parts.append(f"Additional instructions: {instructions}")
        user = "\n".join(user_parts)
        self.log("Creating Express routes and generating business logic...")
        data = self.ask_json(system, user, max_tokens=3800)
        files = data.get("files", {})
        written = [self.write_file(path, content) for path, content in files.items()]
        self.commit(f"Generated backend ({len(written)} files)", written)

        routes = data.get("routes", [])
        self.log(f"Generated {len(written)} backend files: {', '.join(files.keys())}")
        self.log(
            "Exposed routes: "
            + "; ".join(f"{r.get('method')} {r.get('path')} — {r.get('purpose')}" for r in routes)
        )
        self.log(f"Business logic summary: {data.get('business_logic_summary', '')}")

        routes_md = "\n".join(
            f"- `{r.get('method')} {r.get('path')}` — {r.get('purpose')}" for r in routes
        )
        doc = f"# Backend Implementation Summary\n\n## Routes\n{routes_md}\n\n## Business Logic\n{data.get('business_logic_summary', '')}\n"
        self.write_doc("backend_implementation.md", doc)

        self.decide(
            topic="api_style",
            chosen="REST/Express",
            justification="Express chosen for minimal footprint and fast local install/build.",
        )
        self.log(f"Wrote {len(written)} backend files.", "success")
        return data

    def run(self, user_request: str, architecture: dict, plan: dict) -> dict:
        self.status("running", 5)
        db_choice = self.choose_database(user_request, architecture)
        self.status("running", 45)
        api = self.build_api(user_request, architecture, plan, db_choice)
        self.status("success", 100)
        return {"database": db_choice, "api": api}

    def generate(self, user_request: str, architecture: dict, instructions: str = "") -> dict:
        """Planner-scheduled backend generation entry point."""
        self.status("running", 5)
        db_choice = self.choose_database(user_request, architecture)
        self.status("running", 45)
        api = self.build_api(user_request, architecture, {"issues": []}, db_choice, instructions)
        self.status("success", 100)
        return {"database": db_choice, "api": api}

    def apply_patch(self, instructions: str, current_files: dict[str, str]) -> dict:
        """Used by the self-healing build/QA/security/debug loops to ask the
        Backend Agent to fix its own previously generated code."""
        system = (
            "You are the Backend Agent fixing your own previously generated code. Given the "
            "current files and a description of what must change, return the FULL updated "
            "content for every file you changed (never truncate). You may add new files if "
            "needed. Respond as strict JSON: {\"files\": {\"<relative path>\": "
            "\"<new full content>\"}, \"explanation\": str}"
        )
        user = f"Instructions: {instructions}\n\nCurrent files:\n{json.dumps(current_files, default=str)[:6000]}"
        data = self.ask_json(system, user, max_tokens=3800)
        for path, content in data.get("files", {}).items():
            self.write_file(path, content)
        self.commit(f"Patched backend: {instructions[:60]}", list(data.get("files", {}).keys()))
        self.log(f"Applied backend patch affecting {len(data.get('files', {}))} file(s).")
        return data
