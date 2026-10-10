"""Tracking/event/cart evaluators; HOTA requires external TrackEval integration."""

from dataclasses import dataclass
from collections.abc import Sequence


@dataclass(frozen=True)
class EventLabel:
    time: float
    kind: str
    sku: str
    quantity: int


def event_metrics(
    truth: Sequence[EventLabel], predicted: Sequence[EventLabel], *, tolerance: float = 1.0
) -> dict[str, float | int | None]:
    """Greedy one-to-one event matching; exact kind, SKU, qty and temporal window."""
    if tolerance < 0:
        raise ValueError("tolerance must be nonnegative")
    candidates = sorted(
        (abs(gt.time - pred.time), i, j)
        for i, gt in enumerate(truth)
        for j, pred in enumerate(predicted)
        if gt.kind == pred.kind
        and gt.sku == pred.sku
        and gt.quantity == pred.quantity
        and abs(gt.time - pred.time) <= tolerance
    )
    chosen_gt: set[int] = set()
    chosen_pred: set[int] = set()
    for _, i, j in candidates:
        if i not in chosen_gt and j not in chosen_pred:
            chosen_gt.add(i)
            chosen_pred.add(j)
    tp = len(chosen_gt)
    fp = len(predicted) - tp
    fn = len(truth) - tp
    precision = tp / (tp + fp) if tp + fp > 0 else None
    recall = tp / (tp + fn) if tp + fn > 0 else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall > 0
        else None
    )
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def cart_metrics(
    truth: Sequence[dict[str, int]], predicted: Sequence[dict[str, int]]
) -> dict[str, float | int | None]:
    if len(truth) != len(predicted):
        raise ValueError("Cart lists require matched session counts")
    if not truth:
        return {
            "sessions": 0,
            "exact_matches": 0,
            "exact_match_rate": None,
            "mean_absolute_quantity_error": None,
            "missed_items": 0,
            "phantom_items": 0,
        }
    exact = 0
    absolute = 0
    missed = 0
    phantom = 0
    for gt, pred in zip(truth, predicted, strict=True):
        if any(q < 0 for q in list(gt.values()) + list(pred.values())):
            raise ValueError("Negative quantities invalid")
        exact += gt == pred
        for sku in set(gt) | set(pred):
            delta = pred.get(sku, 0) - gt.get(sku, 0)
            absolute += abs(delta)
            missed += max(-delta, 0)
            phantom += max(delta, 0)
    return {
        "sessions": len(truth),
        "exact_matches": exact,
        "exact_match_rate": exact / len(truth),
        "mean_absolute_quantity_error": absolute / len(truth),
        "missed_items": missed,
        "phantom_items": phantom,
    }


def mota_counts(
    *, ground_truth_detections: int, misses: int, false_positives: int, id_switches: int
) -> dict[str, int | float | None]:
    """MOTA only; for validated HOTA and IDF1 use official TrackEval on real annotations."""
    if min(ground_truth_detections, misses, false_positives, id_switches) < 0:
        raise ValueError("Counts must be nonnegative")
    mota = (
        1 - (misses + false_positives + id_switches) / ground_truth_detections
        if ground_truth_detections > 0
        else None
    )
    return {
        "gt": ground_truth_detections,
        "misses": misses,
        "false_positives": false_positives,
        "id_switches": id_switches,
        "mota": mota,
    }
