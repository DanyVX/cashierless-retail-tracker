"""Confidence-aware virtual carts; ambiguous events do not bill a shopper."""

from dataclasses import dataclass
from typing import Literal

from crt.events.interactions import Interaction
from crt.shelf import ShelfChange

EventKind = Literal["PICK", "RETURN", "UNATTRIBUTED_CHANGE", "SESSION_END"]


@dataclass(frozen=True)
class CartEvent:
    kind: EventKind
    timestamp_seconds: float
    track_id: int | None
    zone_id: str | None
    sku: str | None
    quantity: int
    confidence: float
    status: Literal["applied", "review", "unattributed", "ended"]


class CartEngine:
    """Ephemeral per-track ledgers: no negative carts, no speculative attribution."""

    def __init__(self, *, minimum_confidence: float = 0.4, debounce_seconds: float = 0.3) -> None:
        if not 0 <= minimum_confidence <= 1 or debounce_seconds < 0:
            raise ValueError("Invalid cart thresholds")
        self.threshold = minimum_confidence
        self.debounce = debounce_seconds
        self.carts: dict[int, dict[str, int]] = {}
        self.review: list[CartEvent] = []
        self.history: list[CartEvent] = []
        self._last_event: dict[tuple[int | None, str | None, str | None, str], float] = {}
        self._last_timestamp: float = -1

    def apply(
        self, changes: list[ShelfChange], interaction: Interaction, *, timestamp_seconds: float
    ) -> list[CartEvent]:
        if timestamp_seconds < self._last_timestamp:
            raise ValueError("Out-of-order cart event: reject rather than reorder silently")
        self._last_timestamp = timestamp_seconds
        made: list[CartEvent] = []
        for change in changes:
            if change.quantity_delta == 0 and not change.unknown:
                continue
            direction: EventKind = (
                "UNATTRIBUTED_CHANGE"
                if change.unknown
                else "PICK"
                if change.quantity_delta < 0
                else "RETURN"
            )
            owner = interaction.track_id
            confidence = min(change.confidence, interaction.confidence)
            key = (owner, change.zone_id, change.sku, direction)
            prior = self._last_event.get(key)
            if prior is not None and timestamp_seconds - prior < self.debounce:
                continue
            self._last_event[key] = timestamp_seconds
            applied = owner is not None and confidence >= self.threshold and change.sku is not None
            status: Literal["applied", "review", "unattributed", "ended"]
            if change.unknown or owner is None:
                status = "unattributed"
            elif not applied:
                status = "review"
            else:
                status = "applied"
            event = CartEvent(
                direction,
                timestamp_seconds,
                owner,
                change.zone_id,
                change.sku,
                abs(change.quantity_delta),
                confidence,
                status,
            )
            if applied and change.sku is not None and owner is not None:
                cart = self.carts.setdefault(owner, {})
                if direction == "PICK":
                    cart[change.sku] = cart.get(change.sku, 0) + event.quantity
                elif direction == "RETURN":
                    held = cart.get(change.sku, 0)
                    if held < event.quantity:
                        event = CartEvent(
                            direction,
                            timestamp_seconds,
                            owner,
                            change.zone_id,
                            change.sku,
                            event.quantity,
                            confidence,
                            "review",
                        )
                        self.review.append(event)
                    else:
                        cart[change.sku] = held - event.quantity
                        if cart[change.sku] == 0:
                            del cart[change.sku]
            elif status == "review":
                self.review.append(event)
            made.append(event)
            self.history.append(event)
        return made

    def end_session(self, track_id: int, timestamp_seconds: float) -> CartEvent:
        if timestamp_seconds < self._last_timestamp:
            raise ValueError("Session end is out of order")
        self._last_timestamp = timestamp_seconds
        cart = self.carts.pop(track_id, {})
        event = CartEvent(
            "SESSION_END", timestamp_seconds, track_id, None, None, sum(cart.values()), 1.0, "ended"
        )
        self.history.append(event)
        return event

    def current_cart(self, track_id: int) -> dict[str, int]:
        return dict(self.carts.get(track_id, {}))
