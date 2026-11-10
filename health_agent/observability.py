"""Minimal tracing: every agent step is timed and recorded on the state.

This is not a replacement for OpenTelemetry in production; it exists so
a run can be inspected locally (`--show-trace`) and so tests can assert
that the planner actually ran before the retriever.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from .state import AgentState, TraceStep


@contextmanager
def traced(state: AgentState, agent: str, action: str, detail: str = "") -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        state.trace.append(
            TraceStep(agent=agent, action=action, detail=detail, duration_ms=round(elapsed_ms, 3))
        )


def format_trace(state: AgentState) -> str:
    if not state.trace:
        return "(no trace steps recorded)"
    lines = []
    for step in state.trace:
        suffix = f" — {step.detail}" if step.detail else ""
        lines.append(f"[{step.agent}] {step.action} ({step.duration_ms:.1f} ms){suffix}")
    return "\n".join(lines)
