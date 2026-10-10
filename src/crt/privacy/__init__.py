"""Privacy enforcement and output face-redaction baseline."""

from crt.config import Settings
from crt.privacy.redact import FaceRedactor, RedactionStats, require_synthetic_media


class PrivacyViolation(RuntimeError):
    """Operation blocked until consent and privacy prerequisites are met."""


def require_recording_consent(*, consent_confirmed: bool, settings: Settings) -> None:
    if not settings.require_consent or not consent_confirmed:
        raise PrivacyViolation("Recording blocked: consent must be verified privately beforehand")


def require_media_publication_allowed(*, settings: Settings) -> None:
    if not settings.blur_faces:
        raise PrivacyViolation("Publication blocked: face redaction disabled")
    raise PrivacyViolation("Publication blocked: face-redaction verification not implemented")


__all__ = [
    "FaceRedactor", "RedactionStats", "PrivacyViolation", "require_recording_consent",
    "require_media_publication_allowed", "require_synthetic_media",
]
