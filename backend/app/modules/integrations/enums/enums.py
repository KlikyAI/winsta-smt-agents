"""Integrations module enums."""

from enum import Enum


class IntegrationType(str, Enum):
    """Downstream integration target."""
    SARAH_AGENT = "sarah_agent"
    SOCIAL_MEDIA_AGENT = "social_media_agent"


class DeliveryStatus(str, Enum):
    """Status of an integration delivery attempt."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
