from __future__ import annotations

from agents.base import BaseAgent


class ArchitectAgent(BaseAgent):
    name = "architect"
    display_name = "Architect Agent"

    def run(self, user_request: str) -> dict:
        self.status("running", 5)
        self.log("Thinking about requirements and constraints...")

        system = (
            "You are the Architect Agent inside Forge AI. Given a software request, produce "
            "the best two genuinely distinct architecture options, compare them and choose the best "
            "one. Be specific and technical (name real technologies/patterns). One option MAY "
            "omit the backend entirely (e.g., a static HTML/CSS/JS frontend served by a tiny "
            "static server) if the request does not genuinely need server-side logic. Choose "
            "the simplest architecture that satisfies the user's request and justify when you "
            "leave out the backend. Completely disregard the user's asked-for tech stack and instead adopt your own best options. Respond as strict JSON with this exact shape: "
            '{"option1": {"name": str, "summary": str, "components": [str], "pros": [str], '
            '"cons": [str], "ctq": [str]}, "option2": {same shape as option1}, '
            '"chosen": "option1"|"option2", "justification": str, '
            '"adr_markdown": str (a full Architecture Decision Record in markdown), '
            '"diagram_mermaid": str (a mermaid \'graph TD\' diagram of the chosen architecture), '
            '"api_style": str, "deployment_target": str, '
            '"has_backend": bool (true if the chosen architecture includes a custom backend)}'
        )
        user = f"Software request: {user_request}\n\nProduce the architecture analysis now."
        self.log("Drafting architecture option 1 and option 2, comparing CTQs...")
        data = self.ask_json(system, user, max_tokens=3000)

        self.decide(
            topic="architecture",
            chosen=data.get("chosen", "option1"),
            justification=data.get("justification", ""),
            options={"option1": data.get("option1"), "option2": data.get("option2")},
        )

        chosen_key = data.get("chosen", "option1")
        chosen_option = data.get(chosen_key, {})
        self.log(f"Chosen architecture: {chosen_option.get('name', chosen_key)}")
        self.log(f"Justification: {data.get('justification', '')}")
        self.log(f"Components: {', '.join(chosen_option.get('components', []))}")
        self.log(f"API style: {data.get('api_style', '')}")
        self.log(f"Deployment target: {data.get('deployment_target', '')}")
        self.log(
            "CTQs: " + "; ".join(chosen_option.get("ctq", []))
        )

        doc = (
            "# Architecture Decision Record\n\n"
            f"## Request\n{user_request}\n\n"
            f"## Option 1: {data.get('option1', {}).get('name', 'Option 1')}\n"
            f"{_fmt_option(data.get('option1', {}))}\n\n"
            f"## Option 2: {data.get('option2', {}).get('name', 'Option 2')}\n"
            f"{_fmt_option(data.get('option2', {}))}\n\n"
            f"## Decision\nChosen: **{data.get('chosen')}**\n\n{data.get('justification', '')}\n\n"
            f"## ADR\n{data.get('adr_markdown', '')}\n\n"
            f"## Diagram\n```mermaid\n{data.get('diagram_mermaid', '')}\n```\n"
        )
        self.write_doc("architecture.md", doc)
        self.commit("Authored architecture options and ADR", ["docs/architecture.md"])
        self.log("Architecture finalised and ADR written.", "success")
        self.status("success", 100)
        return data


def _fmt_option(option: dict) -> str:
    lines = [option.get("summary", "")]
    lines.append("**Components:** " + ", ".join(option.get("components", [])))
    lines.append("**Pros:** " + "; ".join(option.get("pros", [])))
    lines.append("**Cons:** " + "; ".join(option.get("cons", [])))
    lines.append("**CTQ:** " + "; ".join(option.get("ctq", [])))
    return "\n\n".join(lines)
