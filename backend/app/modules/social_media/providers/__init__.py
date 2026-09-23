"""Provider adapters for Social Media AI publishing and analytics."""

from .meta import MetaGraphClient
from .instagram import InstagramGraphClient
from .threads import ThreadsPublisherAdapter
from .contracts import PublishContext, PublishResult, PublisherUnavailableError, SocialPublisherAdapter
from .registry import InstagramPublisherAdapter, MetaPublisherAdapter, SocialPublisherRegistry, publisher_registry
from .omnichannel import (
    LinkedInPublisherAdapter,
    TikTokPublisherAdapter,
    XPublisherAdapter,
    YouTubePublisherAdapter,
)

__all__ = [
    "MetaGraphClient",
    "InstagramGraphClient",
    "ThreadsPublisherAdapter",
    "InstagramPublisherAdapter",
    "MetaPublisherAdapter",
    "PublishContext",
    "PublishResult",
    "PublisherUnavailableError",
    "SocialPublisherAdapter",
    "SocialPublisherRegistry",
    "publisher_registry",
    "LinkedInPublisherAdapter",
    "TikTokPublisherAdapter",
    "XPublisherAdapter",
    "YouTubePublisherAdapter",
]
