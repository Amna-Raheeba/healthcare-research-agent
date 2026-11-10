"""Shared state passed between agents.

Deliberately plain dataclasses instead of a framework-specific state
object: the graph runner can be unit-tested without LangGraph, and the
same state can be serialised to JSON for tracing.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SubQuery:
    text: str
    rationale: str


@dataclass
class Plan:
    original_question: str
    sub_queries: list[SubQuery] = field(default_factory=list)
    is_comparison: bool = False
    requires_recent_guidance: bool = False


@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    source: str
    year: int
    text: str
    score: float
    matched_query: str


@dataclass
class Claim:
    text: str
    citation_index: int | None = None  # 1-based index into AgentState.chunks


@dataclass
class VerifiedClaim:
    claim: Claim
    supported: bool
    support_ratio: float
    supporting_doc_id: str | None
    reason: str


@dataclass
class TraceStep:
    agent: str
    action: str
    detail: str
    duration_ms: float


@dataclass
class AgentState:
    question: str
    plan: Plan | None = None
    chunks: list[RetrievedChunk] = field(default_factory=list)
    draft_claims: list[Claim] = field(default_factory=list)
    verified_claims: list[VerifiedClaim] = field(default_factory=list)
    answer: str = ""
    blocked: bool = False
    block_reason: str = ""
    abstained: bool = False
    evidence_strength: float = 0.0
    abstention_reason: str = ""
    trace: list[TraceStep] = field(default_factory=list)

    def citation_map(self) -> dict[int, RetrievedChunk]:
        return {i + 1: chunk for i, chunk in enumerate(self.chunks)}
