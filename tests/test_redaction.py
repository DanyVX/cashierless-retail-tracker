import numpy as np
import pytest

from crt.privacy.redact import FaceRedactor, require_synthetic_media


def test_blank_scene_redaction_does_not_change_source() -> None:
    original = np.zeros((120, 120, 3), dtype=np.uint8)
    result, stats = FaceRedactor().redact(original)
    assert stats.applied_regions == 0
    assert np.array_equal(result, original)
    assert result is not original


def test_real_media_publication_blocked() -> None:
    with pytest.raises(PermissionError):
        require_synthetic_media(source_is_synthetic=False)
    require_synthetic_media(source_is_synthetic=True)


def test_invalid_redaction_inputs_rejected() -> None:
    with pytest.raises(ValueError):
        FaceRedactor().redact(np.zeros((30, 30), dtype=np.uint8))
