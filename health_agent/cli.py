"""CLI:  python -m health_agent "your question" [--show-trace] [--json]"""
from __future__ import annotations

import argparse
import json
import sys

from .config import Config
from .graph import run
from .observability import format_trace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="health_agent", description="Verified healthcare research agent (sample corpus).")
    parser.add_argument("question", help="General healthcare research question")
    parser.add_argument("--show-trace", action="store_true", help="Print agent trace steps")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    state = run(args.question, Config.from_env())

    if args.json:
        payload = {
            "question": state.question,
            "blocked": state.blocked,
            "block_reason": state.block_reason,
            "answer": state.answer,
            "sources": [
                {"index": i + 1, "doc_id": c.doc_id, "title": c.title, "source": c.source, "year": c.year, "score": c.score}
                for i, c in enumerate(state.chunks)
            ],
            "claims_total": len(state.verified_claims),
            "claims_supported": sum(1 for v in state.verified_claims if v.supported),
            "trace": [
                {"agent": t.agent, "action": t.action, "duration_ms": t.duration_ms} for t in state.trace
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(state.answer)
        if args.show_trace:
            print("\n--- trace ---")
            print(format_trace(state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
