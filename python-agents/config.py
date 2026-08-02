"""
Central configuration for the Forge AI agent engine.

Every value here is read from environment variables (`.env`). There is no
hardcoded AI logic or canned responses anywhere in this file — it only
loads configuration so the rest of the codebase can call a real LLM API.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_THIS_DIR = Path(__file__).resolve().parent

# Load python-agents/.env first, then fall back to a repo-root .env so a
# single shared file can be used if preferred.
load_dotenv(dotenv_path=_THIS_DIR / ".env", override=False)
load_dotenv(dotenv_path=_THIS_DIR.parent / ".env", override=False)


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    val = os.getenv(name)
    try:
        return int(val) if val not in (None, "") else default
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    val = os.getenv(name)
    try:
        return float(val) if val not in (None, "") else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str | None = os.getenv("OPENAI_BASE_URL") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm_temperature: float = _float("LLM_TEMPERATURE", 0.3)
    llm_max_tokens: int = _int("LLM_MAX_TOKENS", 2000)
    price_input_per_1k: float = _float("PRICE_INPUT_PER_1K_USD", 0.15)
    price_output_per_1k: float = _float("PRICE_OUTPUT_PER_1K_USD", 0.60)
    llm_timeout_seconds: float = _float("LLM_TIMEOUT_SECONDS", 120.0)
    llm_max_retries: int = _int("LLM_MAX_RETRIES", 2)

    host: str = os.getenv("AGENT_ENGINE_HOST", "0.0.0.0")
    port: int = _int("AGENT_ENGINE_PORT", 8000)
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    max_build_retries: int = _int("MAX_BUILD_RETRIES", 3)
    max_test_retries: int = _int("MAX_TEST_RETRIES", 3)
    max_security_retries: int = _int("MAX_SECURITY_RETRIES", 2)
    max_debate_rounds: int = _int("MAX_DEBATE_ROUNDS", 3)
    build_timeout_seconds: int = _int("BUILD_TIMEOUT_SECONDS", 180)
    health_check_timeout_seconds: int = _int("HEALTH_CHECK_TIMEOUT_SECONDS", 30)
    health_check_interval_seconds: float = _float("HEALTH_CHECK_INTERVAL_SECONDS", 1.0)
    deploy_port_range_start: int = _int("DEPLOY_PORT_RANGE_START", 4100)
    deploy_port_range_end: int = _int("DEPLOY_PORT_RANGE_END", 4200)

    workspace_dir: Path = Path(os.getenv("WORKSPACE_DIR", str(_THIS_DIR / "workspace")))

    def validate(self) -> list[str]:
        problems = []
        if self.llm_provider == "openai" and not self.openai_api_key:
            problems.append(
                "OPENAI_API_KEY is not set. Copy python-agents/.env.example to "
                "python-agents/.env and add your key, then restart the agent engine."
            )
        return problems


settings = Settings()
settings.workspace_dir.mkdir(parents=True, exist_ok=True)
