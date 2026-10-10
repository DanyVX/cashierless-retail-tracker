"""Enforcement gates for recording and publication."""

from crt.config import Settings


class PrivacyViolation(RuntimeError):
    """Operation cannot proceed without confirmed privacy prerequisites."""


def require_recording_consent(*, consent_confirmed: bool, settings: Settings) -> None:
    """Reject unconsented capture; flag represents an external verified consent record."""
    if not settings.require_consent or not consent_confirmed:
        raise PrivacyViolation("Recording blocked: consent must be verified privately beforehand")


def require_media_publication_allowed(*, settings: Settings) -> None:
    """No published media until implementation and validation of face redaction in M7."""
    if not settings.blur_faces:
        raise PrivacyViolation("Publication blocked: face redaction disabled")
    raise PrivacyViolation("Publication blocked: face-redaction verification not implemented")
