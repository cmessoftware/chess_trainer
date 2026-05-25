from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RagChunk:
    source: str
    text: str


def chunk_text(text: str, chunk_size: int = 500) -> list[RagChunk]:
    text = text.strip()
    if not text:
        return []
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    return [RagChunk(source="inline", text=chunk) for chunk in chunks]
