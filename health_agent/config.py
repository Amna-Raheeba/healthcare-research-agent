"""Configuration loaded from environment, with sane local defaults.

No secret is required to run this project. The defaults point at the
bundled sample corpus so a fresh clone works offline.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_ROOT.parent


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    corpus_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get("HEALTH_AGENT_CORPUS", str(_PROJECT_ROOT / "data" / "corpus.jsonl"))
        )
    )
    top_k_per_query: int = 4
    max_chunks: int = 6
    min_support_ratio: float = 0.32
    # Selective answering: below this evidence-strength score the agent
    # abstains instead of composing an answer (see health_agent/abstention.py).
    abstention_threshold: float = field(
        default_factory=lambda: _env_float("HEALTH_AGENT_ABSTAIN_THRESHOLD", 0.62)
    )
    enable_llm: bool = field(default_factory=lambda: _env_bool("HEALTH_AGENT_ENABLE_LLM", False))
    llm_provider: str = field(default_factory=lambda: os.environ.get("HEALTH_AGENT_LLM_PROVIDER", "openai"))
    llm_model: str = field(default_factory=lambda: os.environ.get("HEALTH_AGENT_LLM_MODEL", "gpt-4o-mini"))
    trace_enabled: bool = field(default_factory=lambda: _env_bool("HEALTH_AGENT_TRACE", True))

    @classmethod
    def from_env(cls) -> "Config":
        return cls()
