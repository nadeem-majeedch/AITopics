"""Short-term state and persistent memory, with provenance and a purge switch.

Two memories, two jobs:

``ShortTermMemory``
    The working transcript. Bounded by turns *and* characters, because a long
    tool result can blow a context window in one step. When it overflows, older
    turns are replaced by an extractive summary; the summary is marked so the
    model knows it is compressed rather than verbatim.

``PersistentMemory``
    A JSON file of small facts across sessions. Every entry stores ``source``
    (who or what produced it), ``trust`` (``user`` or ``tool``/``document``), a
    timestamp, and a TTL. Two rules make it defensible:

    * retrieval filters by trust, so a fact written from a web page cannot be
      served as if the user had stated it;
    * :meth:`forget_untrusted` removes everything not written by the user, which
      is the recovery step for the memory-contamination lab.

This is not a database. Concurrent writers can lose an update; the docs say so.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .model import Message

# Ordered most trusted first. A caller passing ``min_trust`` accepts that level
# and anything above it, never anything below it.
TRUST_LEVELS = ("user", "tool", "document", "model")


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


@dataclass
class Turn:
    role: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """Bounded conversation window with summarisation on overflow."""

    def __init__(self, max_turns: int = 8, max_chars: int = 4000) -> None:
        self.max_turns = max_turns
        self.max_chars = max_chars
        self.turns: list[Turn] = []
        self.summaries: list[str] = []

    def add(self, role: str, content: str, **meta: Any) -> None:
        self.turns.append(Turn(role=role, content=content, meta=meta))
        self._trim()

    def extend(self, messages: Iterable[Message]) -> None:
        for message in messages:
            self.add(message.get("role", "user"), message.get("content", ""))

    def _size(self) -> int:
        return sum(len(turn.content) for turn in self.turns)

    def _trim(self) -> None:
        while self.turns and (
            len(self.turns) > self.max_turns or self._size() > self.max_chars
        ):
            dropped = self.turns.pop(0)
            self.summaries.append(self._summarise(dropped))
            if len(self.summaries) > 6:
                self.summaries = self.summaries[-6:]

    @staticmethod
    def _summarise(turn: Turn) -> str:
        text = re.sub(r"\s+", " ", turn.content).strip()
        if len(text) > 140:
            text = text[:137] + "..."
        return f"{turn.role}: {text}"

    def context(self) -> str:
        parts: list[str] = []
        if self.summaries:
            parts.append("[SUMMARY OF EARLIER TURNS] " + " | ".join(self.summaries[-3:]))
        for turn in self.turns:
            parts.append(f"{turn.role}: {turn.content}")
        return "\n".join(parts)

    def clear(self) -> None:
        self.turns.clear()
        self.summaries.clear()


@dataclass
class MemoryEntry:
    key: str
    value: str
    source: str = "user"
    trust: str = "user"
    created: float = field(default_factory=time.time)
    expires: float | None = None

    def expired(self, now: float | None = None) -> bool:
        if self.expires is None:
            return False
        return (now if now is not None else time.time()) >= self.expires

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class PersistentMemory:
    """Small JSON-backed store with provenance and a purge path."""

    def __init__(self, path: str | Path, *, max_entries: int = 50,
                 default_ttl_s: float | None = None, clock=time.time) -> None:
        self.path = Path(path)
        self.max_entries = max_entries
        self.default_ttl_s = default_ttl_s
        self.clock = clock
        self.entries: dict[str, MemoryEntry] = {}
        self._load()

    # -- persistence -----------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            rows = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for row in rows if isinstance(rows, list) else []:
            try:
                entry = MemoryEntry(**row)
            except TypeError:
                continue
            if entry.trust not in TRUST_LEVELS:
                continue
            if not entry.expired(self.clock()):
                self.entries[entry.key] = entry

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = [entry.to_json() for entry in self.entries.values()]
        self.path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")

    # -- writing ---------------------------------------------------------
    def remember(self, key: str, value: str, *, source: str = "user",
                 trust: str = "user", ttl_s: float | None = None) -> MemoryEntry:
        if trust not in TRUST_LEVELS:
            raise ValueError(f"trust must be one of {TRUST_LEVELS}")
        if not key or len(key) > 80:
            raise ValueError("key must be 1-80 characters")
        if len(value) > 2000:
            raise ValueError("value is too long for persistent memory")
        ttl = ttl_s if ttl_s is not None else self.default_ttl_s
        entry = MemoryEntry(
            key=key,
            value=value,
            source=source,
            trust=trust,
            created=self.clock(),
            expires=(self.clock() + ttl) if ttl else None,
        )
        self.entries[key] = entry
        while len(self.entries) > self.max_entries:
            oldest = min(self.entries.values(), key=lambda item: item.created)
            self.entries.pop(oldest.key, None)
        return entry

    # -- reading ---------------------------------------------------------
    def recall(self, key: str, *, min_trust: str = "user") -> str | None:
        """Return a value only if its trust level meets the caller's bar."""

        order = {level: rank for rank, level in enumerate(TRUST_LEVELS)}
        entry = self.entries.get(key)
        if entry is None or entry.expired(self.clock()):
            return None
        if order[entry.trust] > order[min_trust]:
            return None
        return entry.value

    def search(self, query: str, *, min_trust: str = "user", limit: int = 5) -> list[MemoryEntry]:
        terms = set(_words(query))
        if not terms:
            return []
        order = {level: rank for rank, level in enumerate(TRUST_LEVELS)}
        hits: list[tuple[int, MemoryEntry]] = []
        for entry in self.entries.values():
            if entry.expired(self.clock()):
                continue
            if order[entry.trust] > order[min_trust]:
                continue
            overlap = len(terms & set(_words(entry.key + " " + entry.value)))
            if overlap:
                hits.append((overlap, entry))
        hits.sort(key=lambda pair: (-pair[0], pair[1].key))
        return [entry for _, entry in hits[:limit]]

    def untrusted(self) -> list[MemoryEntry]:
        return [entry for entry in self.entries.values() if entry.trust != "user"]

    # -- recovery --------------------------------------------------------
    def forget(self, key: str) -> bool:
        return self.entries.pop(key, None) is not None

    def forget_untrusted(self) -> int:
        """Remove every non-user entry. The recovery step after contamination."""

        doomed = [entry.key for entry in self.untrusted()]
        for key in doomed:
            self.entries.pop(key, None)
        return len(doomed)

    def clear(self) -> None:
        self.entries.clear()

    def __len__(self) -> int:
        return len(self.entries)
