"""Bounded, ephemeral event JSON buffer for optional HTTP integration."""

from collections import deque
from dataclasses import asdict

from crt.events import CartEvent


class EventBuffer:
    def __init__(self, *, max_items: int = 100) -> None:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        self.events: deque[dict[str, object]] = deque(maxlen=max_items)
        self.dropped_events = 0

    def publish(self, event: CartEvent) -> None:
        if len(self.events) == self.events.maxlen:
            self.dropped_events += 1
        self.events.append(asdict(event))

    def snapshot(self) -> dict[str, object]:
        return {"events": list(self.events), "dropped_events": self.dropped_events}
