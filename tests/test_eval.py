import pytest

from eval.metrics import EventLabel, cart_metrics, event_metrics, mota_counts


def test_event_matching_one_to_one_and_tolerance() -> None:
    truth = [EventLabel(1, "PICK", "a", 1), EventLabel(3, "RETURN", "a", 1)]
    pred = [EventLabel(1.1, "PICK", "a", 1), EventLabel(1.2, "PICK", "a", 1)]
    result = event_metrics(truth, pred, tolerance=0.5)
    assert result["tp"] == 1
    assert result["fp"] == 1 and result["fn"] == 1
    assert result["f1"] == pytest.approx(0.5)


def test_event_no_truth_no_claim() -> None:
    assert event_metrics([], [])["f1"] is None
    with pytest.raises(ValueError):
        event_metrics([], [], tolerance=-1)


def test_cart_error_costs_and_empty() -> None:
    result = cart_metrics([{"x": 2, "y": 1}], [{"x": 1, "z": 3}])
    assert result["missed_items"] == 2
    assert result["phantom_items"] == 3
    assert result["mean_absolute_quantity_error"] == 5
    assert cart_metrics([], [])["exact_match_rate"] is None
    with pytest.raises(ValueError):
        cart_metrics([{}], [])


def test_mota_counts_well_defined() -> None:
    assert (
        mota_counts(ground_truth_detections=10, misses=2, false_positives=1, id_switches=1)["mota"]
        == 0.6
    )
    assert (
        mota_counts(ground_truth_detections=0, misses=0, false_positives=0, id_switches=0)["mota"]
        is None
    )
