from __future__ import annotations

import json
import re
import subprocess

from agents.base import BaseAgent
from storage import store

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


class SecurityAgent(BaseAgent):
    name = "security"
    display_name = "Security Agent"

    def _scan_secrets(self) -> list[dict]:
        findings = []
        project_dir = store.project_dir(self.run_id)
        for path in project_dir.rglob("*"):
            if path.is_file() and "node_modules" not in path.parts:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for pattern in SECRET_PATTERNS:
                    for match in pattern.finditer(text):
                        findings.append({"file": str(path.relative_to(project_dir)), "match": match.group()[:80]})
        return findings

    def _npm_audit(self) -> dict:
        project_dir = store.project_dir(self.run_id)
        if not (project_dir / "node_modules").exists():
            return {"skipped": True, "reason": "node_modules not installed yet"}
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return json.loads(result.stdout or "{}")
        except Exception as exc:
            return {"error": str(exc)}

    def _read_all_project_files(self, limit_chars: int = 8000) -> dict[str, str]:
        files: dict[str, str] = {}
        project_dir = store.project_dir(self.run_id)
        if not project_dir.exists():
            return files
        for path in sorted(project_dir.rglob("*")):
            if path.is_file() and "node_modules" not in path.parts:
                try:
                    files[str(path.relative_to(project_dir))] = path.read_text(encoding="utf-8", errors="ignore")[
                        :limit_chars
                    ]
                except Exception:
                    continue
        return files

    def audit(self, user_request: str, architecture: dict) -> dict:
        """Full-code security audit. Returns architecture-level concerns and
        code-level findings. Genuine concerns can be escalated to a Supervisor
        debate; minor issues are forwarded to the Planner for patching."""
        self.status("running", 10)
        self.log("Scanning the whole codebase for vulnerabilities...")

        files = self._read_all_project_files()
        secrets = self._scan_secrets()
        audit = self._npm_audit()

        system = (
            "You are the Security Agent inside Forge AI. Review the WHOLE codebase and the "
            "chosen architecture. Identify: (1) architecture-level problems that genuinely "
            "challenge the base tech stack, and (2) concrete code vulnerabilities in specific "
            "files. For architecture issues, explain why the chosen stack/framework is risky "
            "for this use case and recommend an alternative. For code issues, specify the file, "
            "the vulnerability, severity (low/medium/high), which agent should fix it "
            "(backend/frontend/security), exact patch instructions, and whether this issue is "
            "significant enough to require a debate with that agent (requires_debate). "
            "Only set requires_debate=true for genuine, non-trivial disagreements. Minor issues can be skipped for debate. Debate only when issue is major enough"
            "Respond as strict JSON: "
            '{"architecture_issue": {"present": bool, "description": str, "recommended_change": str}, '
            '"code_findings": [{"severity": str, "file": str, "description": str, '
            '"target_agent": str, "patch_instructions": str, "requires_debate": bool}], '
            '"secrets_found": int, "npm_audit_summary": str}'
        )
        user = (
            f"Software request: {user_request}\n"
            f"Architecture: {json.dumps(architecture, default=str)[:2000]}\n"
            f"Files: {json.dumps(files, default=str)[:6000]}\n"
            f"Secrets scan found {len(secrets)} literal(s): {json.dumps(secrets, default=str)[:1000]}\n"
            f"npm audit: {json.dumps(audit, default=str)[:1000]}"
        )
        data = self.ask_json(system, user, max_tokens=3500)

        findings = data.get("code_findings", [])
        arch_issue = data.get("architecture_issue", {}) or {}

        debate_findings = [f for f in findings if f.get("requires_debate")]
        patch_findings = [f for f in findings if not f.get("requires_debate")]

        self.decide(
            topic="security_audit",
            chosen="audit_complete",
            justification=f"Found {len(findings)} code finding(s), {len(debate_findings)} debated. Architecture issue: {arch_issue.get('present', False)}.",
            findings=findings,
            debate_findings=debate_findings,
            patch_findings=patch_findings,
            architecture_issue=arch_issue,
        )

        self.log(f"Security audit complete. Total findings: {len(findings)}")
        if arch_issue.get("present"):
            self.log(f"Architecture issue: {arch_issue.get('description', '')}")
            self.log(f"Recommended architecture change: {arch_issue.get('recommended_change', '')}")
        for f in debate_findings:
            self.log(
                f"Debate-worthy [{f.get('severity', '?').upper()}] finding in {f.get('file')}: "
                f"{f.get('description', '')} — target: {f.get('target_agent')}"
            )
        for f in patch_findings:
            self.log(
                f"Patchable [{f.get('severity', '?').upper()}] finding in {f.get('file')}: "
                f"{f.get('description', '')} — target: {f.get('target_agent')}"
            )
        if secrets:
            self.log(f"Secrets scan found {len(secrets)} potential literal(s).")
        if data.get("npm_audit_summary"):
            self.log(f"npm audit summary: {data['npm_audit_summary']}")

        findings_md = "\n".join(
            f"- **[{f.get('severity', '?').upper()}] {f.get('file')}** — {f.get('description')}\n"
            f"  - Target agent: {f.get('target_agent')}\n"
            f"  - Fix: {f.get('patch_instructions')}\n"
            f"  - Requires debate: {f.get('requires_debate', False)}"
            for f in findings
        )
        doc = (
            "# Security Audit Report\n\n"
            f"## Architecture Issue\n"
            f"Present: {arch_issue.get('present', False)}\n"
            f"{arch_issue.get('description', 'None')}\n"
            f"Recommended change: {arch_issue.get('recommended_change', 'None')}\n\n"
            f"## Code Findings\n{findings_md or 'None'}\n\n"
            f"## Secrets Scan\nFound {len(secrets)} potential literal(s).\n\n"
            f"## npm Audit\n{data.get('npm_audit_summary', '')}\n"
        )
        self.write_doc("security_audit_report.md", doc)
        self.commit("Completed full security audit", ["docs/security_audit_report.md"])

        if arch_issue.get("present"):
            self.log("Architecture-level security concern flagged. Escalating to Supervisor debate.", "warning")
        if debate_findings:
            self.log(f"{len(debate_findings)} finding(s) require debate with the authoring agent(s).", "warning")
        if patch_findings:
            self.log(f"{len(patch_findings)} minor finding(s) forwarded to Planner for patching.", "warning")
        if not findings and not arch_issue.get("present"):
            self.log("No security findings requiring action.", "success")

        self.status("success", 100)
        return {
            "architecture_issue": arch_issue,
            "code_findings": findings,
            "debate_findings": debate_findings,
            "patch_findings": patch_findings,
            "secrets_found": len(secrets),
        }

    def _autofix_secrets(self, secrets: list[dict]) -> None:
        project_dir = store.project_dir(self.run_id)
        for finding in secrets:
            path = project_dir / finding["file"]
            try:
                text = path.read_text(encoding="utf-8")
                for pattern in SECRET_PATTERNS:
                    text = pattern.sub(
                        lambda m: re.sub(r"['\"][A-Za-z0-9_\-]{8,}['\"]", "process.env.SECRET_VALUE", m.group()),
                        text,
                    )
                path.write_text(text, encoding="utf-8")
            except Exception:
                continue
        self.commit("Auto-fixed hardcoded secrets", [f["file"] for f in secrets])

    def run_static(self, user_request: str, backend_result: dict, frontend_result: dict) -> dict:
        """Backward-compatible static pass kept for external callers."""
        self.status("running", 10)
        self.log("Scanning for hardcoded secrets...")
        secrets = self._scan_secrets()
        audit = self._npm_audit()
        self.log("Building threat model and RBAC/permission analysis...")
        system = (
            "You are the Security Agent inside Forge AI performing an OWASP-style review, "
            "threat modelling and permission/RBAC analysis on a newly generated app. Also "
            "critically evaluate the Backend Agent's data-access approach and state honestly "
            "whether you would recommend a different approach (only disagree if you "
            "genuinely think it's warranted). Respond as strict JSON: "
            '{"owasp_findings": [{"category": str, "risk": "low"|"medium"|"high", '
            '"description": str, "recommendation": str}], '
            '"threat_model": str, "permission_analysis": str, '
            '"data_access_review": {"chosen": str, "justification": str}, '
            '"secrets_found": int, "requires_autofix": bool}'
        )
        user = (
            f"Software request: {user_request}\n"
            f"Backend routes: {json.dumps(backend_result.get('api', {}).get('routes', []), default=str)[:1500]}\n"
            f"Secrets scan found {len(secrets)} literal(s): {json.dumps(secrets, default=str)[:1000]}\n"
            f"npm audit summary: {json.dumps(audit, default=str)[:1000]}"
        )
        data = self.ask_json(system, user, max_tokens=2500)
        if secrets and data.get("requires_autofix"):
            self.log("Auto-fixing hardcoded secrets found in code...", "info")
            self._autofix_secrets(secrets)
        self.decide(
            topic="data_access_pattern",
            chosen=data.get("data_access_review", {}).get("chosen", "unspecified"),
            justification=data.get("data_access_review", {}).get("justification", ""),
        )
        findings_md = "\n".join(
            f"- **[{f.get('risk', '?').upper()}] {f.get('category')}** — {f.get('description')}\n"
            f" - Recommendation: {f.get('recommendation')}"
            for f in data.get("owasp_findings", [])
        )
        doc = (
            "# Security Report (Static Analysis)\n\n## OWASP Findings\n"
            + findings_md
            + f"\n\n## Threat Model\n{data.get('threat_model', '')}\n\n"
            f"## Permission Analysis\n{data.get('permission_analysis', '')}\n\n"
            f"## Secrets Scan\nFound {len(secrets)} potential literal(s).\n\n"
            f"## Dependency Audit\n```json\n{json.dumps(audit, indent=2, default=str)[:2000]}\n```\n"
        )
        self.write_doc("security_static_report.md", doc)
        self.commit("Completed static security analysis", ["docs/security_static_report.md"])
        self.log("Static security analysis complete.", "success")
        self.status("success", 60)
        return data

    def run_dynamic(self, base_url: str) -> dict:
        self.status("running", 70)
        self.log(f"Probing live deployment at {base_url} for security headers...")
        import requests

        try:
            resp = requests.get(base_url, timeout=5)
            headers_report = dict(resp.headers)
        except Exception as exc:
            headers_report = {"error": str(exc)}
        system = (
            "You are the Security Agent inside Forge AI reviewing HTTP response headers from "
            "a freshly deployed app for missing security headers (CSP, X-Content-Type-Options, "
            "HSTS, X-Frame-Options, etc.) and general dynamic risks. Respond as strict JSON: "
            '{"missing_headers": [str], "risk_summary": str, "recommendations": [str]}'
        )
        user = f"Observed response headers: {json.dumps(headers_report, default=str)}"
        data = self.ask_json(system, user, max_tokens=1200)
        doc = (
            "# Security Report (Dynamic Analysis)\n\n## Missing Headers\n"
            + "\n".join(f"- {h}" for h in data.get("missing_headers", []))
            + f"\n\n## Risk Summary\n{data.get('risk_summary', '')}\n\n"
            + "## Recommendations\n"
            + "\n".join(f"- {r}" for r in data.get("recommendations", []))
        )
        self.write_doc("security_dynamic_report.md", doc)
        self.log(f"Dynamic security scan complete. Missing headers: {', '.join(data.get('missing_headers', []))}")
        self.status("success", 100)
        return data

    def apply_patch(self, instructions: str, current_files: dict[str, str]) -> dict:
        system = (
            "You are the Security Agent applying a security fix to the given files. Return "
            "FULL updated content for every changed file. Respond as strict JSON: "
            '{"files": {"<path>": "<content>"}, "explanation": str}'
        )
        user = f"Instructions: {instructions}\n\nCurrent files:\n{json.dumps(current_files, default=str)[:6000]}"
        data = self.ask_json(system, user, max_tokens=3000)
        for p, c in data.get("files", {}).items():
            self.write_file(p, c)
        self.commit(f"Security fix: {instructions[:60]}", list(data.get("files", {}).keys()))
        self.log(f"Applied security patch affecting {len(data.get('files', {}))} file(s).")
        return data
