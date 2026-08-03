from __future__ import annotations

import json

from agents.base import BaseAgent


class FrontendAgent(BaseAgent):
    name = "frontend"
    display_name = "Frontend Agent"

    def run(self, user_request: str, architecture: dict, backend_api: dict) -> dict:
        self.status("running", 10)
        self.log("Designing UI and state management for the feature...")
        has_backend = architecture.get("has_backend", True)
        if not has_backend:
            system = (
                "You are the Frontend Agent inside Forge AI. The chosen architecture has NO "
                "custom backend. Build a complete, self-contained static frontend (vanilla "
                "HTML/CSS/JS, no build step, no framework, no bundler) under a 'public' directory. "
                "All application state must live in the browser (localStorage, in-memory, or "
                "JSON-file download/upload if persistence is needed). Requirements: "
                "1) public/index.html, public/styles.css, public/app.js at minimum. "
                "2) Basic accessibility: semantic HTML, form labels, aria attributes, visible "
                "focus states, sufficient color contrast. "
                "3) Use a simple, explicit state management pattern in plain JS and document it. "
                "4) Expose a small user-configurable settings object window.APP_CONFIG. "
                "5) For images, ALWAYS use placeholder URLs like https://picsum.photos/300/200 instead of local file paths. For icons, include FontAwesome or Lucide via CDN in the HTML head (e.g., <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>) and use icon classes (<i class='fas fa-user'></i>) instead of leaving empty boxes or missing files."
                "Respond as strict JSON: {\"files\": {\"<relative path>\": \"<content>\"}, "
                "\"state_management\": str, \"accessibility_notes\": str, "
                "\"user_configuration\": object}"
            )
        else:
            system = (
                "You are the Frontend Agent inside Forge AI. Build a small static frontend "
                "(vanilla HTML/CSS/JS, no build step, no framework, no bundler) under a 'public' "
                "directory that will be served by the existing Express backend via "
                "express.static. It must call the backend's REST API using same-origin relative "
                "paths like /api/.... Requirements: "
                "1) public/index.html, public/styles.css, public/app.js at minimum. "
                "2) Basic accessibility: semantic HTML, form labels, aria attributes, visible "
                "focus states, sufficient color contrast. "
                "3) Use a simple, explicit state management pattern in plain JS and document it. "
                "4) Expose a small user-configurable settings object window.APP_CONFIG. "
                "5) For images, ALWAYS use placeholder URLs like https://picsum.photos/300/200 instead of local file paths. For icons, include FontAwesome or Lucide via CDN in the HTML head (e.g., <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>) and use icon classes (<i class='fas fa-user'></i>) instead of leaving empty boxes or missing files."
                "Respond as strict JSON: {\"files\": {\"<relative path>\": \"<content>\"}, "
                "\"state_management\": str, \"accessibility_notes\": str, "
                "\"user_configuration\": object}"
            )
        user = (
            f"Software request: {user_request}\n"
            f"Architecture: {json.dumps(architecture, default=str)[:1200]}\n"
            f"Backend API routes: {json.dumps(backend_api.get('routes', []), default=str)[:2000]}"
        )
        self.log("Generating UI components and wiring them to the API...")
        data = self.ask_json(system, user, max_tokens=3800)
        written = [self.write_file(p, c) for p, c in data.get("files", {}).items()]
        self.commit(f"Generated frontend ({len(written)} files)", written)

        self.decide(
            topic="state_management",
            chosen=data.get("state_management", "vanilla-js"),
            justification="Kept dependency-free to guarantee zero-build local deployment.",
        )

        self.log(f"Generated {len(written)} frontend files: {', '.join(data.get('files', {}).keys())}")
        self.log(f"State management approach: {data.get('state_management', '')}")
        self.log(f"Accessibility notes: {data.get('accessibility_notes', '')}")
        self.log(f"User configuration: {json.dumps(data.get('user_configuration', {}), default=str)}")

        doc = (
            f"# Frontend Summary\n\n## State Management\n{data.get('state_management', '')}\n\n"
            f"## Accessibility Notes\n{data.get('accessibility_notes', '')}\n\n"
            f"## User Configuration\n```json\n{json.dumps(data.get('user_configuration', {}), indent=2)}\n```\n"
        )
        self.write_doc("frontend.md", doc)
        self.log(f"Wrote {len(written)} frontend files.", "success")
        self.status("success", 100)
        return data

    def generate(self, user_request: str, architecture: dict, backend_api: dict, instructions: str = "") -> dict:
        """Planner-scheduled frontend generation entry point."""
        self.status("running", 10)
        self.log("Generating frontend from schedule...")
        has_backend = architecture.get("has_backend", True)
        if not has_backend:
            system = (
                "You are the Frontend Agent inside Forge AI. The chosen architecture has NO "
                "custom backend. Build a complete, self-contained static frontend (vanilla "
                "HTML/CSS/JS, no build step, no framework) under a 'public' directory. All "
                "application state must live in the browser (localStorage, in-memory, or "
                "JSON-file download/upload if persistence is needed). Include public/index.html, "
                "public/styles.css, public/app.js at minimum. "
                "For images, ALWAYS use placeholder URLs like https://picsum.photos/300/200 instead of local file paths. For icons, include FontAwesome or Lucide via CDN in the HTML head (e.g., <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>) and use icon classes (<i class='fas fa-user'></i>) instead of leaving empty boxes or missing files."
                "Respond as strict JSON: {\"files\": {\"<relative path>\": \"<content>\"}, "
                "\"state_management\": str, \"accessibility_notes\": str, "
                "\"user_configuration\": object}"
            )
        else:
            system = (
                "You are the Frontend Agent inside Forge AI. Build a small static frontend "
                "(vanilla HTML/CSS/JS, no build step) under a 'public' directory. It must call the "
                "backend's REST API using same-origin relative paths like /api/.... Include "
                "public/index.html, public/styles.css, public/app.js at minimum. "
                "For images, ALWAYS use placeholder URLs like https://picsum.photos/300/200 instead of local file paths. For icons, include FontAwesome or Lucide via CDN in the HTML head (e.g., <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>) and use icon classes (<i class='fas fa-user'></i>) instead of leaving empty boxes or missing files."
                "Respond as strict JSON: {\"files\": {\"<relative path>\": \"<content>\"}, "
                "\"state_management\": str, \"accessibility_notes\": str, "
                "\"user_configuration\": object}"
            )
        user_parts = [
            f"Software request: {user_request}",
            f"Architecture: {json.dumps(architecture, default=str)[:1200]}",
            f"Backend API routes: {json.dumps(backend_api.get('routes', []), default=str)[:2000]}",
        ]
        if instructions:
            user_parts.append(f"Additional instructions: {instructions}")
        user = "\n".join(user_parts)
        data = self.ask_json(system, user, max_tokens=3800)
        written = [self.write_file(p, c) for p, c in data.get("files", {}).items()]
        self.commit(f"Generated frontend ({len(written)} files)", written)

        self.decide(
            topic="state_management",
            chosen=data.get("state_management", "vanilla-js"),
            justification="Dependency-free frontend scheduled by Planner.",
        )

        self.log(f"Generated {len(written)} frontend files: {', '.join(data.get('files', {}).keys())}")
        self.log(f"State management approach: {data.get('state_management', '')}")
        self.log(f"Accessibility notes: {data.get('accessibility_notes', '')}")
        self.log(f"User configuration: {json.dumps(data.get('user_configuration', {}), default=str)}")

        doc = (
            f"# Frontend Summary\n\n## State Management\n{data.get('state_management', '')}\n\n"
            f"## Accessibility Notes\n{data.get('accessibility_notes', '')}\n\n"
            f"## User Configuration\n```json\n{json.dumps(data.get('user_configuration', {}), indent=2)}\n```\n"
        )
        self.write_doc("frontend.md", doc)
        self.log(f"Wrote {len(written)} frontend files.", "success")
        self.status("success", 100)
        return data

    def apply_patch(self, instructions: str, current_files: dict[str, str]) -> dict:
        system = (
            "You are the Frontend Agent fixing your own previously generated code. Given the "
            "current files and required changes, return FULL updated file contents for every "
            "changed file. Respond as strict JSON: {\"files\": {\"<path>\": \"<content>\"}, "
            "\"explanation\": str}"
        )
        user = f"Instructions: {instructions}\n\nCurrent files:\n{json.dumps(current_files, default=str)[:6000]}"
        data = self.ask_json(system, user, max_tokens=3800)
        for p, c in data.get("files", {}).items():
            self.write_file(p, c)
        self.commit(f"Patched frontend: {instructions[:60]}", list(data.get("files", {}).keys()))
        self.log(f"Applied frontend patch affecting {len(data.get('files', {}))} file(s).")
        return data
