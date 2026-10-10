"""M0 defaults and privacy fail-closed behavior."""

import pytest
from pydantic import ValidationError

from crt.config import Settings
from crt.privacy import (
    PrivacyViolation,
    require_media_publication_allowed,
    require_recording_consent,
)


def test_defaults_are_privacy_preserving(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CRT_BLUR_FACES", raising=False)
    monkeypatch.delenv("CRT_REQUIRE_CONSENT", raising=False)
    monkeypatch.delenv("CRT_STORE_RAW_FRAMES", raising=False)
    monkeypatch.delenv("CRT_RETENTION_SECONDS", raising=False)
    settings = Settings(_env_file=None)
    assert settings.blur_faces is True
    assert settings.require_consent is True
    assert settings.store_raw_frames is False
    assert settings.retention_seconds == 0


@pytest.mark.parametrize(
    "values",
    [
        {"store_raw_frames": True},
        {"retention_seconds": 1},
        {"require_consent": False},
        {"retention_seconds": -1},
    ],
)
def test_unsafe_settings_rejected(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


def test_capture_requires_external_consent() -> None:
    settings = Settings(_env_file=None)
    with pytest.raises(PrivacyViolation, match="consent"):
        require_recording_consent(consent_confirmed=False, settings=settings)
    require_recording_consent(consent_confirmed=True, settings=settings)


def test_media_cannot_be_published_yet() -> None:
    for blur in (True, False):
        with pytest.raises(PrivacyViolation, match="Publication blocked"):
            require_media_publication_allowed(settings=Settings(blur_faces=blur, _env_file=None))
