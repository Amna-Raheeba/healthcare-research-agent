"""Optional LLM adapter.

The pipeline does not depend on this module. It exists so that, with a
key configured, the answer composer can be swapped for a generative one
*behind the same verifier* — generated sentences still have to pass
``agents/verifier.py`` before they are shown.

No SDK is imported at module load; imports happen inside the call so the
project stays stdlib-only by default.
"""
from __future__ import annotations

import os

from .config import Config


def llm_available(config: Config) -> bool:
    if not config.enable_llm:
        return False
    if config.llm_provider == "openai":
        return bool(os.environ.get("OPENAI_API_KEY"))
    if config.llm_provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    return False


def generate_with_llm(prompt: str, config: Config) -> str:
    """Call the configured provider. Raises if unavailable — callers must check first."""
    if config.llm_provider == "openai":
        from openai import OpenAI  # type: ignore

        client = OpenAI()
        resp = client.chat.completions.create(
            model=config.llm_model,
            messages=[
                {"role": "system", "content": "Answer only from the provided sources. Cite as [n]."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        return resp.choices[0].message.content or ""
    if config.llm_provider == "anthropic":
        import anthropic  # type: ignore

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=config.llm_model, max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if hasattr(block, "text"))
    raise ValueError(f"Unknown LLM provider: {config.llm_provider}")
