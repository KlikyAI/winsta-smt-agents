"""Publishing adapters for TikTok, YouTube, X, and LinkedIn."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
import structlog

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.modules.social_media.providers.contracts import PublishContext, PublishResult, SocialPublisherAdapter
from app.modules.social_media.services.media_fetch import download_public_media

logger = structlog.get_logger()


def _truncate_utf16(value: str, max_units: int) -> str:
    """Truncate text using TikTok's UTF-16 code-unit limits.

    Python slices Unicode code points, while TikTok documents photo title and
    description limits in UTF-16 runes.  Emoji can therefore make a seemingly
    valid Python slice exceed the provider limit.
    """
    value = value or ""
    while len(value.encode("utf-16-le")) // 2 > max_units:
        value = value[:-1]
    return value


def _payload(response: httpx.Response, message: str) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        raise ExternalServiceException(message=f"{message}: invalid provider response") from exc
    error = data.get("error")
    provider_failed = isinstance(error, dict) and error.get("code") not in {None, "ok"}
    if not response.is_success or provider_failed or data.get("errors"):
        error_code = error.get("code") if isinstance(error, dict) else error
        error_message = error.get("message") if isinstance(error, dict) else None
        suffix = str(error_code or f"HTTP {response.status_code}")[:80]
        if error_message:
            suffix = f"{suffix}: {str(error_message)[:240]}"
        raise ExternalServiceException(message=f"{message}: {suffix}")
    return data


class TikTokPublisherAdapter(SocialPublisherAdapter):
    platforms = frozenset({"tiktok"})
    requires_media = True

    async def publish(self, context: PublishContext) -> PublishResult:
        headers = {"Authorization": f"Bearer {context.access_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            creator_response = await client.post(
                "https://open.tiktokapis.com/v2/post/publish/creator_info/query/", headers=headers
            )
            creator = _payload(creator_response, "TikTok creator lookup failed").get("data", {})
            # TikTok validates privacy_level against the exact values returned by
            # creator_info.  Do not invent a fallback when the account has no
            # eligible option (for example, an unaudited sandbox account).
            privacy_options = [
                str(option) for option in (creator.get("privacy_level_options") or []) if option
            ]
            if not privacy_options:
                raise ExternalServiceException(
                    message="TikTok creator profile returned no valid privacy options"
                )
            # Unaudited clients (including Sandbox apps) may only publish to
            # private accounts. Public visibility is opt-in after TikTok audit.
            audited = get_settings().tiktok_client_audited
            privacy = (
                "SELF_ONLY"
                if not audited and "SELF_ONLY" in privacy_options
                else privacy_options[0]
            )
            logger.info(
                "tiktok_creator_capabilities",
                privacy_level_options=privacy_options,
                selected_privacy_level=privacy,
                client_audited=audited,
                comment_disabled=bool(creator.get("comment_disabled", False)),
            )
            response = await client.post(
                "https://open.tiktokapis.com/v2/post/publish/content/init/",
                headers=headers,
                json={
                    "post_info": {
                        "title": _truncate_utf16(context.caption, 90),
                        "description": _truncate_utf16(context.caption, 4000),
                        "privacy_level": privacy,
                        "disable_comment": bool(creator.get("comment_disabled", False)),
                        "auto_add_music": True,
                        # TikTok marks both commercial-content declarations as
                        # required for DIRECT_POST, even when they are false.
                        "brand_content_toggle": False,
                        "brand_organic_toggle": False,
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "photo_cover_index": 0,
                        "photo_images": [context.media_url],
                    },
                    "post_mode": "DIRECT_POST",
                    "media_type": "PHOTO",
                },
            )
        data = _payload(response, "TikTok photo publish failed").get("data", {})
        publish_id = data.get("publish_id")
        if not publish_id:
            raise ExternalServiceException(message="TikTok returned no publish ID")
        return PublishResult(str(publish_id), {"provider": "tiktok", "raw": data})

    async def fetch_metrics(self, *, platform: str, external_post_id: str, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={"publish_id": external_post_id},
            )
        return _payload(response, "TikTok publish status lookup failed").get("data", {})


class XPublisherAdapter(SocialPublisherAdapter):
    platforms = frozenset({"x"})
    requires_media = False

    async def publish(self, context: PublishContext) -> PublishResult:
        media_ids: list[str] = []
        headers = {"Authorization": f"Bearer {context.access_token}"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            if context.media_url:
                try:
                    media, media_type = await download_public_media(context.media_url, 5 * 1024 * 1024)
                    if not media_type.startswith("image/"):
                        raise ExternalServiceException(message="X omnichannel posts currently accept image media only")
                    upload = await client.post(
                        "https://api.x.com/2/media/upload",
                        headers=headers,
                        data={"media_category": "tweet_image", "media_type": media_type},
                        files={"media": ("post-image", media, media_type)},
                    )
                    if upload.status_code in (200, 201):
                        upload_data = upload.json().get("data", {})
                        media_id = upload_data.get("id") or upload_data.get("media_id_string")
                        if media_id:
                            media_ids.append(str(media_id))
                    elif upload.status_code == 403:
                        logger.warning(
                            "x_media_upload_forbidden",
                            detail=upload.text[:300],
                            hint="X API Free plan does not allow media upload (requires Basic/Pro tier or media.write permission). Proceeding with text-only post.",
                        )
                    else:
                        upload_data = _payload(upload, "X media upload failed").get("data", {})
                        media_id = upload_data.get("id") or upload_data.get("media_id_string")
                        if media_id:
                            media_ids.append(str(media_id))
                except Exception as exc:
                    logger.warning("x_media_upload_skipped", error=str(exc))
            body: dict[str, Any] = {"text": context.caption[:280], "made_with_ai": True}
            if media_ids:
                body["media"] = {"media_ids": media_ids}
            response = await client.post(
                "https://api.x.com/2/tweets",
                headers={**headers, "Content-Type": "application/json"},
                json=body,
            )
        data = _payload(response, "X post creation failed").get("data", {})
        if not data.get("id"):
            raise ExternalServiceException(message="X returned no post ID")
        return PublishResult(str(data["id"]), {"provider": "x", "raw": data})

    async def fetch_metrics(self, *, platform: str, external_post_id: str, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.x.com/2/tweets/{external_post_id}",
                params={"tweet.fields": "public_metrics"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        return _payload(response, "X metrics lookup failed").get("data", {}).get("public_metrics", {})


class LinkedInPublisherAdapter(SocialPublisherAdapter):
    platforms = frozenset({"linkedin"})
    requires_media = False

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        settings = get_settings()
        return {
            "Authorization": f"Bearer {token}",
            "Linkedin-Version": settings.linkedin_api_version,
            "X-Restli-Protocol-Version": "2.0.0",
        }

    async def publish(self, context: PublishContext) -> PublishResult:
        author = context.account_metadata.get("author_urn") or f"urn:li:person:{context.account_id}"
        headers = self._headers(context.access_token)
        content: dict[str, Any] | None = None
        async with httpx.AsyncClient(timeout=60.0) as client:
            if context.media_url:
                media, media_type = await download_public_media(context.media_url, 10 * 1024 * 1024)
                if not media_type.startswith("image/"):
                    raise ExternalServiceException(message="LinkedIn omnichannel posts currently accept image media only")
                initialize = await client.post(
                    "https://api.linkedin.com/rest/images?action=initializeUpload",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"initializeUploadRequest": {"owner": author}},
                )
                value = _payload(initialize, "LinkedIn image initialization failed").get("value", {})
                if not value.get("uploadUrl") or not value.get("image"):
                    raise ExternalServiceException(message="LinkedIn returned no image upload target")
                upload = await client.put(
                    value["uploadUrl"],
                    headers={"Authorization": f"Bearer {context.access_token}", "Content-Type": media_type},
                    content=media,
                )
                if not upload.is_success:
                    raise ExternalServiceException(message=f"LinkedIn image upload failed: HTTP {upload.status_code}")
                content = {"media": {"id": value["image"], "altText": context.caption[:300]}}
            body: dict[str, Any] = {
                "author": author,
                "commentary": context.caption[:3000],
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }
            if content:
                body["content"] = content
            response = await client.post(
                "https://api.linkedin.com/rest/posts",
                headers={**headers, "Content-Type": "application/json"},
                json=body,
            )
        if not response.is_success:
            _payload(response, "LinkedIn post creation failed")
        post_id = response.headers.get("x-restli-id")
        if not post_id:
            raise ExternalServiceException(message="LinkedIn returned no post ID")
        return PublishResult(post_id, {"provider": "linkedin", "status_code": response.status_code})

    async def fetch_metrics(self, *, platform: str, external_post_id: str, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.linkedin.com/rest/posts/{quote(external_post_id, safe='')}",
                headers=self._headers(access_token),
            )
        return _payload(response, "LinkedIn post lookup failed")


class YouTubePublisherAdapter(SocialPublisherAdapter):
    platforms = frozenset({"youtube"})
    requires_media = True

    async def publish(self, context: PublishContext) -> PublishResult:
        media, media_type = await download_public_media(context.media_url or "", 128 * 1024 * 1024)
        if media_type != "video/mp4":
            raise ExternalServiceException(
                message="YouTube publishing requires an MP4 video; the public API cannot create image Community posts"
            )
        headers = {"Authorization": f"Bearer {context.access_token}"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            initialize = await client.post(
                "https://www.googleapis.com/upload/youtube/v3/videos",
                params={"uploadType": "resumable", "part": "snippet,status"},
                headers={
                    **headers,
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Upload-Content-Type": media_type,
                    "X-Upload-Content-Length": str(len(media)),
                },
                json={
                    "snippet": {"title": context.caption.splitlines()[0][:100], "description": context.caption[:5000]},
                    "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
                },
            )
            if not initialize.is_success or not initialize.headers.get("location"):
                _payload(initialize, "YouTube upload initialization failed")
                raise ExternalServiceException(message="YouTube returned no resumable upload URL")
            response = await client.put(
                initialize.headers["location"],
                headers={**headers, "Content-Type": media_type, "Content-Length": str(len(media))},
                content=media,
            )
        data = _payload(response, "YouTube video upload failed")
        if not data.get("id"):
            raise ExternalServiceException(message="YouTube returned no video ID")
        return PublishResult(str(data["id"]), {"provider": "youtube", "raw": data})

    async def fetch_metrics(self, *, platform: str, external_post_id: str, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "statistics", "id": external_post_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        items = _payload(response, "YouTube metrics lookup failed").get("items", [])
        return items[0].get("statistics", {}) if items else {}
