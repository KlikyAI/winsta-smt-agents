"""Sub-service managing Brand Kit configuration, voice, and context."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.modules.social_media.models import BrandKit
from app.modules.social_media.schemas import BrandKitResponse, UpdateBrandKitRequest


class SocialBrandKitService:
    """Manages active brand guidelines, visual tokens, and policy dictionaries."""

    @staticmethod
    async def get_active_brand_kit(session: AsyncSession, organization_id: uuid.UUID) -> BrandKit | None:
        result = await session.execute(
            select(BrandKit)
            .where(BrandKit.organization_id == organization_id)
            .where(BrandKit.is_active.is_(True))
            .where(BrandKit.deleted_at.is_(None))
            .order_by(BrandKit.version.desc(), BrandKit.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def brand_context(brand_kit: BrandKit | None) -> dict:
        if brand_kit is None:
            return {}
        return {
            "version": brand_kit.version,
            "brand_name": brand_kit.brand_name,
            "tagline": brand_kit.tagline,
            "colors": brand_kit.colors or {},
            "fonts": brand_kit.fonts or {},
            "tone": brand_kit.tone,
            "target_audience": brand_kit.target_audience,
            "default_hashtags": brand_kit.default_hashtags or [],
            "disclaimer": brand_kit.disclaimer,
            "forbidden_terms": brand_kit.forbidden_terms or [],
            "required_terms": brand_kit.required_terms or [],
            "product_facts": brand_kit.product_facts or {},
            "languages": brand_kit.languages or ["id", "en", "ar"],
            "guidelines": brand_kit.guidelines,
        }

    @classmethod
    async def get_or_create_brand_kit(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
    ) -> BrandKitResponse:
        brand_kit = await cls.get_active_brand_kit(session, organization_id)
        if brand_kit is None:
            brand_kit = BrandKit(
                organization_id=organization_id,
                brand_name="Winsta AI Studio",
                tagline="Autonomous AI Trend Intelligence & Social Content Studio",
                colors={"primary": "#0f172a", "accent": "#8b5cf6", "secondary": "#38bdf8"},
                fonts={"primary": "Outfit, sans-serif"},
                tone="Luxury, Authoritative & Inspiring",
                target_audience="Gulf Region and global innovators",
                default_hashtags=["#WinstaAI", "#FutureOfCreative"],
                languages=["id", "en", "ar"],
                guidelines="Use verified facts, one clear CTA, and native phrasing for each language.",
                is_active=True,
            )
            session.add(brand_kit)
            await session.commit()
            await session.refresh(brand_kit)
        return BrandKitResponse.model_validate(brand_kit)

    @classmethod
    async def update_brand_kit(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
        data: UpdateBrandKitRequest,
    ) -> BrandKitResponse:
        current = await cls.get_active_brand_kit(session, organization_id)
        next_version = (current.version + 1) if current else 1
        if current:
            current.is_active = False
        brand_kit = BrandKit(
            organization_id=organization_id,
            version=next_version,
            is_active=True,
            **data.model_dump(),
        )
        session.add(brand_kit)
        await session.commit()
        await session.refresh(brand_kit)
        return BrandKitResponse.model_validate(brand_kit)

