"""Deploys the generated project on localhost and verifies it is reachable.

This module contains no AI/agent logic — it only runs real shell commands
and real HTTP health checks, and reports back what actually happened so the
agents can decide how to react.
"""
from __future__ import annotations

import atexit
import json
import os
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import requests

from config import settings
from storage import store


# Common server-side frameworks that indicate a runnable backend.
_BACKEND_FRAMEWORKS = {
    "express",
    "fastify",
    "koa",
    "hapi",
    "restify",
    "connect",
    "polka",
    "micro",
    "hono",
}

# Node.js built-in modules that should never be added to package.json.
_NODE_BUILTINS = {
    "assert", "buffer", "child_process", "cluster", "console", "constants",
    "crypto", "dgram", "dns", "domain", "events", "fs", "http", "http2",
    "https", "inspector", "module", "net", "os", "path", "perf_hooks",
    "process", "punycode", "querystring", "readline", "repl", "stream",
    "string_decoder", "sys", "timers", "tls", "trace_events", "tty",
    "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
}

# Sensible default semver ranges for commonly required packages.
_DEFAULT_DEPS = {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "sqlite3": "^5.1.6",
    "pg": "^8.11.0",
    "dotenv": "^16.3.1",
    "bcrypt": "^5.1.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.0",
    "uuid": "^9.0.0",
    "redis": "^4.6.0",
    "mongodb": "^5.0.0",
    "axios": "^1.6.0",
    "node-fetch": "^3.3.0",
    "vitest": "^1.0.0",
    "@playwright/test": "^1.40.0",
    "playwright": "^1.40.0",
}


def _find_free_port() -> int:
    for port in range(settings.deploy_port_range_start, settings.deploy_port_range_end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free port available in the configured DEPLOY_PORT_RANGE.")


class DeploymentManager:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.project_dir = store.project_dir(run_id)
        self.process: subprocess.Popen | None = None
        self._log_path = store.run_dir(run_id) / "server.log"

    def _log(self, message: str) -> None:
        def _mut(state: dict[str, Any]) -> None:
            state["deployment"]["logs"].append({"ts": time.time(), "message": message})
            state["deployment"]["logs"] = state["deployment"]["logs"][-100:]

        store.mutate(self.run_id, _mut)

    def _set(self, **kwargs: Any) -> None:
        def _mut(state: dict[str, Any]) -> None:
            state["deployment"].update(kwargs)

        store.mutate(self.run_id, _mut)

    def _preflight_fixes(self) -> None:
        """Deterministic self-healing that runs before `npm install`.

        Fixes the most common reasons generated projects fail to deploy:
        missing package.json, missing start script, missing runnable entry,
        and missing GET /api/health.  These fixes do not require an LLM call,
        so they work even when the generated code is imperfect.
        """
        self._ensure_package_json()
        has_backend = self._has_backend()
        entry = self._resolve_entry(has_backend)
        if not (self.project_dir / entry).exists():
            self._log(f"Entry file '{entry}' missing; creating a static-file fallback server.")
            self._create_static_server()
            return
        if has_backend and entry == "server.js":
            self._ensure_health_endpoint()

    def _ensure_package_json(self) -> None:
        pkg_path = self.project_dir / "package.json"
        if pkg_path.exists():
            try:
                pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            except Exception:
                self._log("package.json is invalid JSON; rewriting a minimal one.")
                pkg = {}
        else:
            self._log("No package.json found; creating a minimal one.")
            pkg = {}

        if not pkg.get("scripts"):
            pkg["scripts"] = {}
        scripts = pkg["scripts"]
        if not scripts.get("start"):
            scripts["start"] = "node server.js"

        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
        has_backend = self._has_backend()
        if has_backend:
            for dep in ("express", "cors"):
                if dep not in deps:
                    pkg.setdefault("dependencies", {})[dep] = "^4.18.2" if dep == "express" else "^2.8.5"

        # Merge any dependencies declared by the Backend Agent.
        try:
            state = store.load(self.run_id)
            for output in (state.get("pipeline_context", {}) or {}).get("outputs", {}).values():
                if not isinstance(output, dict):
                    continue
                backend_deps = output.get("dependencies") or output.get("api", {}).get("dependencies")
                if isinstance(backend_deps, dict):
                    for dep, version in backend_deps.items():
                        if dep not in deps:
                            pkg.setdefault("dependencies", {})[dep] = version
                            deps[dep] = version
        except Exception:
            pass

        # Scan JS files for require()/import statements and inject missing packages.
        required_packages = self._scan_required_packages()
        for dep in required_packages:
            if dep not in deps:
                version = _DEFAULT_DEPS.get(dep, "^1.0.0")
                pkg.setdefault("dependencies", {})[dep] = version
                deps[dep] = version
                self._log(f"Injecting missing dependency '{dep}' ({version}) into package.json.")

        # If the QA agent generated tests, make sure the test toolchain is present.
        if any(
            (self.project_dir / "tests").glob(pattern)
            for pattern in ("*.test.*", "*.spec.*")
        ):
            for dep, version in (
                ("vitest", _DEFAULT_DEPS.get("vitest", "^1.0.0")),
                ("@playwright/test", _DEFAULT_DEPS.get("@playwright/test", "^1.40.0")),
                ("playwright", _DEFAULT_DEPS.get("playwright", "^1.40.0")),
            ):
                if dep not in deps:
                    pkg.setdefault("devDependencies", {})[dep] = version
                    deps[dep] = version

        pkg["main"] = pkg.get("main") or "server.js"
        pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")

    def _scan_required_packages(self) -> set[str]:
        """Find external packages imported via require() or ESM import in JS files."""
        packages: set[str] = set()
        if not self.project_dir.exists():
            return packages
        require_re = re.compile(r"require\(['\"]([^'\"]+)['\"]\)")
        import_re = re.compile(r"import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]")
        for path in self.project_dir.rglob("*.js"):
            if "node_modules" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for match in require_re.findall(text):
                self._maybe_add_package(match, packages)
            for match in import_re.findall(text):
                self._maybe_add_package(match, packages)
        return packages

    @staticmethod
    def _maybe_add_package(spec: str, packages: set[str]) -> None:
        """Only add real package names (not relative paths or built-ins)."""
        if spec.startswith(".") or spec.startswith("/"):
            return
        # Scoped packages keep the scope/name; bare sub-path imports keep the package root.
        name = spec.split("/")[0] if not spec.startswith("@") else "/".join(spec.split("/")[:2])
        if not name or name in _NODE_BUILTINS:
            return
        packages.add(name)

    def _ensure_health_endpoint(self) -> None:
        """If server.js does not expose /api/health, append a guarded route so the
        deployment manager can verify liveness without crashing if the generated
        code declares `app` in a non-global scope."""
        server_path = self.project_dir / "server.js"
        if not server_path.exists():
            return
        code = server_path.read_text(encoding="utf-8", errors="ignore")
        if "/api/health" in code:
            return
        self._log("server.js is missing GET /api/health; injecting a guarded health route.")
        injection = (
            "\n// Injected by Forge AI deployment manager\n"
            "try {\n"
            "  if (typeof app !== 'undefined' && app && typeof app.get === 'function') {\n"
            "    app.get('/api/health', (req, res) => {\n"
            "      res.setHeader('Content-Type', 'application/json');\n"
            "      res.statusCode = 200;\n"
            "      res.end(JSON.stringify({ status: 'ok' }));\n"
            "    });\n"
            "  }\n"
            "} catch (e) {\n"
            "  console.error('[Forge AI] Could not inject /api/health:', e.message);\n"
            "}\n"
        )
        server_path.write_text(code + injection, encoding="utf-8")

    def _read_pkg(self) -> dict[str, Any] | None:
        pkg = self.project_dir / "package.json"
        if not pkg.exists():
            return None
        try:
            return json.loads(pkg.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _has_backend(self) -> bool:
        """A project is treated as backend-driven when there is a clear
        server-side entry point or a backend framework in package.json.
        Otherwise it is served as a static frontend."""
        srv = self.project_dir / "server.js"
        if srv.exists():
            return True

        pkg = self._read_pkg()
        if pkg is None:
            return False

        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
        if any(fw in deps for fw in _BACKEND_FRAMEWORKS):
            return True

        scripts = pkg.get("scripts") or {}
        start = scripts.get("start", "")
        if start and re.search(r"\bnode\b", start):
            return True

        main = pkg.get("main", "")
        if main and isinstance(main, str) and (self.project_dir / main).exists():
            return True

        return False

    def _resolve_entry(self, has_backend: bool) -> str:
        """Pick the file to run with Node."""
        srv = self.project_dir / "server.js"
        if has_backend:
            pkg = self._read_pkg()
            if pkg:
                scripts = pkg.get("scripts") or {}
                start = scripts.get("start", "")
                # e.g. "node server.js" or "node index.js"
                match = re.search(r"\bnode\s+(['\"]?)([^'\"\s]+)\1", start)
                if match:
                    candidate = match.group(2)
                    if (self.project_dir / candidate).exists():
                        return candidate
                main = pkg.get("main", "")
                if main and (self.project_dir / main).exists():
                    return main
            if srv.exists():
                return "server.js"
            # Fallback to any JS file in the project root.
            for candidate in self.project_dir.glob("*.js"):
                return candidate.name
            return "server.js"

        # Static projects always get our generated server.js.
        return "server.js"

    def _create_static_server(self) -> None:
        """Writes a minimal Node.js static-file server for frontend-only
        projects. It serves the public/ folder if it exists, otherwise the
        project root, exposes GET /api/health, and synthesises an index.html
        if one is missing so the root URL is never a 404."""
        static_root: str
        if (self.project_dir / "public" / "index.html").exists():
            static_root = "public"
        elif (self.project_dir / "public").exists():
            static_root = "public"
        else:
            static_root = "."

        index_path = self.project_dir / static_root / "index.html"
        if not index_path.exists():
            # Try to find any HTML file to use as a landing page.
            candidates = sorted((self.project_dir / static_root).glob("*.html"))
            if candidates:
                shutil.copy2(candidates[0], index_path)
                self._log(f"Copied {candidates[0].name} to index.html for static root.")
            else:
                index_path.write_text(
                    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                    "<title>Forge AI Deployment</title></head>"
                    "<body style='font-family:sans-serif;padding:2rem'>"
                    "<h1>Deployment is live</h1>"
                    "<p>The generated app is being served statically.</p>"
                    "</body></html>",
                    encoding="utf-8",
                )
                self._log("Created a fallback index.html for static deployment.")

        server_code = (
            "const http = require('http');\n"
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            f"const STATIC_ROOT = path.join(__dirname, {json.dumps(static_root)});\n"
            "const PORT = process.env.PORT || 4100;\n"
            "const MIME = {\n"
            "  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',\n"
            "  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',\n"
            "  '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webp': 'image/webp'\n"
            "};\n"
            "const server = http.createServer((req, res) => {\n"
            "  if (req.url === '/api/health') {\n"
            "    res.writeHead(200, { 'Content-Type': 'application/json' });\n"
            "    return res.end(JSON.stringify({ status: 'ok' }));\n"
            "  }\n"
            "  let rel = req.url === '/' ? 'index.html' : req.url;\n"
            "  rel = path.normalize(rel).replace(/^(\\.\\/)+/, '');\n"
            "  if (rel.startsWith('..')) {\n"
            "    res.writeHead(403, { 'Content-Type': 'text/plain' });\n"
            "    return res.end('Forbidden');\n"
            "  }\n"
            "  let filePath = path.join(STATIC_ROOT, rel);\n"
            "  if (!path.extname(filePath)) filePath += '.html';\n"
            "  fs.readFile(filePath, (err, data) => {\n"
            "    if (err) {\n"
            "      if (req.url === '/') {\n"
            "        res.writeHead(200, { 'Content-Type': 'text/html' });\n"
            "        return res.end(\"<h1>Forge AI Deployment</h1><p>The generated app is being served statically.</p>\");\n"
            "      }\n"
            "      res.writeHead(404, { 'Content-Type': 'text/plain' });\n"
            "      return res.end('Not found');\n"
            "    }\n"
            "    const ext = path.extname(filePath).toLowerCase();\n"
            "    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });\n"
            "    res.end(data);\n"
            "  });\n"
            "});\n"
            "server.listen(PORT, '127.0.0.1', () => console.log('Static server listening on port ' + PORT));\n"
        )
        (self.project_dir / "server.js").write_text(server_code, encoding="utf-8")

    def install_dependencies(self) -> tuple[bool, str]:
        if not (self.project_dir / "package.json").exists():
            return True, "No package.json found; nothing to install."
        self._log("Running npm install...")
        try:
            result = subprocess.run(
                ["npm", "install", "--no-audit", "--no-fund"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=settings.build_timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            self._log(f"npm install timed out after {settings.build_timeout_seconds}s.")
            return False, f"npm install timed out: {exc}"
        except Exception as exc:
            self._log(f"npm install could not be executed: {exc}")
            return False, f"npm install could not be executed: {exc}"
        ok = result.returncode == 0
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        self._log(output[-2000:])
        self._log("npm install succeeded." if ok else f"npm install failed (exit code {result.returncode}).")
        return ok, output[-4000:]

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def start(self, port: int) -> subprocess.Popen:
        has_backend = self._has_backend()
        self._set(has_backend=has_backend)
        store.mutate(self.run_id, lambda s: s.setdefault("pipeline_context", {}).__setitem__("has_backend", has_backend))

        entry = self._resolve_entry(has_backend)

        if not has_backend:
            self._log("No backend detected; creating static-file server for frontend.")
            self._create_static_server()
            entry = "server.js"
        else:
            self._log(f"Backend detected; deploying with entry '{entry}'.")

        env = {**os.environ, "PORT": str(port)}
        log_file = open(self._log_path, "w", encoding="utf-8", buffering=1)
        self._log(f"Starting node process: node {entry} (port {port})")
        try:
            self.process = subprocess.Popen(
                ["node", entry], cwd=self.project_dir, stdout=log_file, stderr=subprocess.STDOUT, env=env
            )
            self._log(f"Node process started with PID {self.process.pid}.")
        except Exception as exc:
            log_file.write(f"Failed to start server: {exc}\n")
            log_file.close()
            self._log(f"Failed to start node process for '{entry}': {exc}")
            raise RuntimeError(f"Failed to start node process for '{entry}': {exc}") from exc
        return self.process

    def read_logs(self, max_chars: int = 8000) -> str:
        file_logs = ""
        if self._log_path.exists():
            try:
                file_logs = self._log_path.read_text(encoding="utf-8", errors="ignore")[-max_chars:]
            except Exception:
                pass
        state_logs = store.load(self.run_id).get("deployment", {}).get("logs", [])
        deployment_logs = "\n".join(f"[{l.get('ts', '?')}] {l.get('message', '')}" for l in state_logs[-50:])
        combined = f"{deployment_logs}\n--- process stdout/stderr ---\n{file_logs}".strip()
        return combined[-max_chars:]

    def wait_healthy(self, port: int) -> bool:
        deadline = time.time() + settings.health_check_timeout_seconds
        has_backend = self._has_backend()
        # Require /api/health to return HTTP 200. Only fall back to the root URL
        # for frontend-only projects that cannot have a backend-style health route.
        checks = [
            (f"http://127.0.0.1:{port}/api/health", 200),
        ]
        if not has_backend:
            checks.append((f"http://127.0.0.1:{port}/", None))
        while time.time() < deadline:
            if self.process and self.process.poll() is not None:
                self._log("Node process exited before becoming healthy.")
                return False
            for url, expected in checks:
                try:
                    resp = requests.get(url, timeout=2)
                    ok = resp.status_code == expected if expected is not None else resp.status_code < 500
                    if ok:
                        self._log(f"Health check succeeded for {url} (status {resp.status_code}).")
                        return True
                except requests.RequestException:
                    pass
            time.sleep(settings.health_check_interval_seconds)
        self._log("Health check deadline reached without a successful response.")
        return False

    def deploy(self) -> dict[str, Any]:
        self.stop()
        self._set(status="installing", attempts=self._current_attempts() + 1)
        self._preflight_fixes()
        ok, log = self.install_dependencies()
        if not ok:
            self._set(status="failed")
            self._log(f"Install failed:\n{log[-800:]}")
            logs = self.read_logs()
            return {"success": False, "stage": "install", "logs": logs}

        port = _find_free_port()
        self._set(status="starting", port=port)
        self.start(port)
        healthy = self.wait_healthy(port)
        logs = self.read_logs()
        if healthy:
            url = f"http://localhost:{port}"
            self._set(status="running", url=url, port=port)
            self._log(f"Server is reachable at {url}")
            return {"success": True, "url": url, "port": port, "logs": logs}
        self.stop()
        self._set(status="failed")
        self._log(f"Health check failed. Server logs:\n{logs[-800:]}")
        return {"success": False, "stage": "runtime", "logs": logs}

    def _current_attempts(self) -> int:
        try:
            return store.load(self.run_id)["deployment"].get("attempts", 0)
        except Exception:
            return 0


_ACTIVE_MANAGERS: dict[str, DeploymentManager] = {}


def get_manager(run_id: str) -> DeploymentManager:
    mgr = _ACTIVE_MANAGERS.get(run_id)
    if mgr is None:
        mgr = DeploymentManager(run_id)
        _ACTIVE_MANAGERS[run_id] = mgr
    return mgr


def _cleanup_all() -> None:
    for mgr in list(_ACTIVE_MANAGERS.values()):
        mgr.stop()


atexit.register(_cleanup_all)
