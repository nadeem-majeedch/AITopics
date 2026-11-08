"""Conversation state and context-window management.

History is where a chatbot usually degrades quietly: the oldest turns fall off the
end of the window and a constraint stated in turn one is silently forgotten. This
module makes trimming explicit and reportable instead of implicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationHistory:
    """Bounded turn history with an explicit, reportable trimming policy.

    ``max_turns`` counts messages (user + assistant), not exchanges. ``max_chars``
    is a coarse proxy for tokens that avoids depending on a tokenizer: it is
    honest about being approximate, and it is enough to demonstrate the failure
    mode a real token budget causes.
    """

    max_turns: int = 8
    max_chars: int = 4000
    turns: list[dict[str, str]] = field(default_factory=list)
    dropped_turns: int = 0
    summarized: str = ""

    def add(self, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")
        if not content.strip():
            raise ValueError("content cannot be empty")
        self.turns.append({"role": role, "content": content.strip()})
        self._trim()

    def add_exchange(self, question: str, answer: str) -> None:
        self.add("user", question)
        self.add("assistant", answer)

    def _trim(self) -> None:
        while len(self.turns) > self.max_turns:
            self._drop_oldest()

        while self._char_count() > self.max_chars and len(self.turns) > 2:
            self._drop_oldest()

    def _char_count(self) -> int:
        return sum(len(turn["content"]) for turn in self.turns) + len(self.summarized)

    def _drop_oldest(self) -> None:
        dropped = self.turns.pop(0)
        self.dropped_turns += 1
        snippet = dropped["content"][:80].replace("\n", " ")
        self.summarized = (self.summarized + f" Earlier: {snippet}").strip()[-240:]

    def messages(self) -> list[dict[str, str]]:
        """History ready for the prompt, with a visible note about dropped turns."""
        messages: list[dict[str, str]] = []
        if self.summarized:
            messages.append(
                {
                    "role": "system",
                    "content": f"Summary of earlier conversation (older turns removed):{self.summarized}",
                }
            )
        messages.extend(dict(turn) for turn in self.turns)
        return messages

    def reset(self) -> None:
        self.turns.clear()
        self.dropped_turns = 0
        self.summarized = ""

    def __len__(self) -> int:
        return len(self.turns)
