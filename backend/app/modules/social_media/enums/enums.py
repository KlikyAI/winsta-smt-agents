"""State and platform enums for the Social Media AI Agent."""

from enum import Enum


class SocialPlatform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    X = "x"
    LINKEDIN = "linkedin"
    THREADS = "threads"


class ContentBriefStatus(str, Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    READY_FOR_REVIEW = "ready_for_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentItemStatus(str, Enum):
    DRAFT = "draft"
    QA_PENDING = "qa_pending"
    READY_FOR_APPROVAL = "ready_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

    @property
    def is_approvable(self) -> bool:
        return self is ContentItemStatus.READY_FOR_APPROVAL

    @property
    def is_schedulable(self) -> bool:
        return self is ContentItemStatus.APPROVED


class ContentApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class PublishJobStatus(str, Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    CONNECTION_REQUIRED = "connection_required"
    MEDIA_REQUIRED = "media_required"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CampaignStatus(str, Enum):
    """Internal paid-campaign approval lifecycle."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CampaignBudgetType(str, Enum):
    DAILY = "daily"
    LIFETIME = "lifetime"
