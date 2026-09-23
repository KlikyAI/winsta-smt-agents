"""Security helpers for provider webhook verification."""

import hashlib
import hmac
import json
from typing import Any


INSTAGRAM_SIGNATURE_PREFIX = "sha256="


def verify_instagram_challenge(*, mode: str | None, provided_token: str | None, expected_token: str) -> bool:
    """Validate Meta's webhook subscription handshake in constant time."""
    if mode != "subscribe" or not provided_token or not expected_token:
        return False
    return hmac.compare_digest(provided_token, expected_token)


def verify_instagram_signature(*, body: bytes, signature: str | None, app_secret: str) -> bool:
    """Validate an Instagram webhook body using Meta's SHA-256 signature."""
    if not signature or not signature.startswith(INSTAGRAM_SIGNATURE_PREFIX) or not app_secret:
        return False
    expected = INSTAGRAM_SIGNATURE_PREFIX + hmac.new(
        app_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def parse_instagram_event(body: bytes) -> dict[str, Any] | None:
    """Parse a webhook event while requiring a JSON object at the root."""
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def summarize_instagram_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Return non-sensitive metadata suitable for structured logs."""
    entries = payload.get("entry") if isinstance(payload.get("entry"), list) else []
    fields: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        changes = entry.get("changes") if isinstance(entry.get("changes"), list) else []
        fields.update(
            change["field"]
            for change in changes
            if isinstance(change, dict) and isinstance(change.get("field"), str)
        )
        if isinstance(entry.get("messaging"), list):
            fields.add("messaging")
    return {
        "object": payload.get("object") if isinstance(payload.get("object"), str) else "unknown",
        "entry_count": len(entries),
        "fields": sorted(fields),
    }
