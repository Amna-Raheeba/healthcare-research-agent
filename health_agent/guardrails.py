"""Medical safety guardrails, checked before any retrieval or generation.

Three rules, in priority order:

1. Emergency language -> do not answer the research question, return a
   safe completion urging urgent care. We are not an emergency service.
2. A request for an individual diagnosis / personal treatment plan ->
   refuse that specific request and offer general information instead.
3. Everything else passes, but the final answer always carries the
   disclaimer in ``DISCLAIMER``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

DISCLAIMER = (
    "Disclaimer: This is general information from a small sample corpus, "
    "not medical advice. It does not replace a clinician who knows your "
    "history. If you are unwell or worried, speak to a qualified "
    "healthcare professional."
)

SAFE_COMPLETION_EMERGENCY = (
    "If this is happening now, please seek urgent help immediately — call your "
    "local emergency number or go to your nearest emergency department. "
    "Do not wait for information from this tool. If you can, tell someone "
    "nearby what is happening so they can help you get care."
)

_EMERGENCY_PATTERNS = [
    r"\bchest pain\b", r"\bcan(?:not|'t) breathe\b", r"\bdifficulty breathing\b",
    r"\bstroke\b.*\b(face|arm|speech)\b", r"\bsuicidal\b", r"\bwant to (?:die|kill myself)\b",
    r"\boverdose\b", r"\bsevere bleeding\b", r"\bunconscious\b", r"\bseizure\b.*\bnow\b",
    r"\bheart attack\b",
]

_PERSONAL_DIAGNOSIS_PATTERNS = [
    r"\bdo i have\b", r"\bdiagnose me\b", r"\bwhat is wrong with me\b",
    r"\bmy (?:blood pressure|blood sugar|hba1c|test result) is\b.*\bshould i\b",
    r"\bshould i (?:take|stop|start|increase|decrease)\b.*\b(mg|dose|dosage|medication|medicine|insulin|tablet)\b",
    r"\bam i (?:diabetic|hypertensive|sick|ill)\b",
    r"\bprescribe\b.*\bme\b",
]


@dataclass
class GuardrailResult:
    allowed: bool
    category: str  # "ok" | "emergency" | "personal_diagnosis"
    message: str = ""


def check_input(question: str) -> GuardrailResult:
    text = question.strip().lower()
    for pattern in _EMERGENCY_PATTERNS:
        if re.search(pattern, text):
            return GuardrailResult(False, "emergency", SAFE_COMPLETION_EMERGENCY)
    for pattern in _PERSONAL_DIAGNOSIS_PATTERNS:
        if re.search(pattern, text):
            return GuardrailResult(
                False,
                "personal_diagnosis",
                "I can't diagnose you or advise on your personal medication or dose. "
                "That needs a clinician who can examine you and see your full history. "
                "I can share general, published information on the condition or test "
                "you're asking about if that would help — please rephrase it as a "
                "general question.",
            )
    return GuardrailResult(True, "ok")
