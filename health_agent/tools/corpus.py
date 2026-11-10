"""Loading and validation for the JSONL corpus."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    source: str
    year: int
    text: str
    tags: tuple[str, ...] = ()

    @property
    def searchable_text(self) -> str:
        return f"{self.title} {' '.join(self.tags)} {self.text}"


def load_corpus(path: str | Path) -> list[Document]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Corpus not found: {path}")
    docs: list[Document] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            for field_name in ("id", "title", "source", "year", "text"):
                if field_name not in row:
                    raise ValueError(f"{path}:{lineno}: missing field {field_name!r}")
            if row["id"] in seen:
                raise ValueError(f"{path}:{lineno}: duplicate id {row['id']!r}")
            seen.add(row["id"])
            docs.append(
                Document(
                    doc_id=str(row["id"]),
                    title=str(row["title"]),
                    source=str(row["source"]),
                    year=int(row["year"]),
                    text=str(row["text"]),
                    tags=tuple(row.get("tags", [])),
                )
            )
    if not docs:
        raise ValueError(f"Corpus is empty: {path}")
    return docs
