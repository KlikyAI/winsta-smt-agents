"""Registry for active social publishing adapters."""

from app.modules.social_media.providers.contracts import (
    PublishContext,
    PublishResult,
    PublisherUnavailableError,
    SocialPublisherAdapter,
)
from app.modules.social_media.providers.meta import MetaGraphClient
from app.modules.social_media.providers.instagram import InstagramGraphClient
from app.modules.social_media.providers.threads import ThreadsPublisherAdapter
from app.modules.social_media.providers.omnichannel import (
    LinkedInPublisherAdapter,
    TikTokPublisherAdapter,
    XPublisherAdapter,
    YouTubePublisherAdapter,
)


class MetaPublisherAdapter(SocialPublisherAdapter):
    platforms = frozenset({"facebook"})
    requires_media = True

    def __init__(self, client: MetaGraphClient | None = None) -> None:
        self.client = client or MetaGraphClient()

    async def publish(self, context: PublishContext) -> PublishResult:
        payload = await self.client.publish(
            platform=context.platform,
            account_id=context.account_id,
            page_id=(
                context.account_metadata.get("facebook_page_id")
                or context.account_metadata.get("page_id")
            ),
            access_token=context.access_token,
            media_url=context.media_url or "",
            caption=context.caption,
        )
        external_post_id = payload.get("id")
        if not external_post_id:
            raise RuntimeError("Meta returned no external post ID")
        return PublishResult(
            external_post_id=str(external_post_id),
            response_data={"provider": "meta", "raw": payload},
        )

    async def fetch_metrics(
        self,
        *,
        platform: str,
        external_post_id: str,
        access_token: str,
    ) -> dict:
        return await self.client.fetch_metrics(
            platform=platform,
            external_post_id=external_post_id,
            access_token=access_token,
        )


class InstagramPublisherAdapter(SocialPublisherAdapter):
    """Publisher for accounts connected through Instagram Login."""

    platforms = frozenset({"instagram"})
    requires_media = True

    def __init__(self, client: InstagramGraphClient | None = None) -> None:
        self.client = client or InstagramGraphClient()

    async def publish(self, context: PublishContext) -> PublishResult:
        payload = await self.client.publish(
            account_id=context.account_id,
            access_token=context.access_token,
            media_url=context.media_url or "",
            caption=context.caption,
        )
        external_post_id = payload.get("id")
        if not external_post_id:
            raise RuntimeError("Instagram returned no external post ID")
        return PublishResult(
            external_post_id=str(external_post_id),
            response_data={"provider": "instagram", "raw": payload},
        )

    async def fetch_metrics(self, *, platform: str, external_post_id: str, access_token: str) -> dict:
        return await self.client.fetch_metrics(external_post_id=external_post_id, access_token=access_token)


class SocialPublisherRegistry:
    def __init__(self, adapters: list[SocialPublisherAdapter] | None = None) -> None:
        self._adapters: dict[str, SocialPublisherAdapter] = {}
        for adapter in adapters or [
            MetaPublisherAdapter(),
            InstagramPublisherAdapter(),
            ThreadsPublisherAdapter(),
            TikTokPublisherAdapter(),
            YouTubePublisherAdapter(),
            XPublisherAdapter(),
            LinkedInPublisherAdapter(),
        ]:
            for platform in adapter.platforms:
                self._adapters[platform] = adapter

    def get(self, platform: str) -> SocialPublisherAdapter:
        adapter = self._adapters.get(platform)
        if adapter is None:
            raise PublisherUnavailableError(
                f"The {platform} publishing adapter is not active yet."
            )
        return adapter

    def is_active(self, platform: str) -> bool:
        return platform in self._adapters


publisher_registry = SocialPublisherRegistry()
