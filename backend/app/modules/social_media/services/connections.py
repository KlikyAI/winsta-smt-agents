"""Provider configuration metadata for secure social account connections."""

from dataclasses import dataclass
from urllib.parse import urlparse

from cryptography.fernet import Fernet

from app.core.config import Settings
from app.core.exceptions import BadRequestException


@dataclass(frozen=True)
class ConnectionProviderSpec:
    platform: str
    display_name: str
    description: str
    setup_url: str
    required_settings: tuple[tuple[str, str], ...]
    requested_scopes: tuple[str, ...]


class OAuthConnectionError(BadRequestException):
    """A callback failure with a browser-safe reason code."""

    def __init__(self, *, reason: str, platform: str | None = None, message: str) -> None:
        super().__init__(message=message)
        self.reason = reason
        self.platform = platform


PROVIDER_SPECS: tuple[ConnectionProviderSpec, ...] = (
    ConnectionProviderSpec(
        "instagram",
        "Instagram",
        "Connect an Instagram professional account through Instagram Login.",
        "https://developers.facebook.com/apps/",
        (("INSTAGRAM_APP_ID", "instagram_app_id"), ("INSTAGRAM_APP_SECRET", "instagram_app_secret")),
        ("instagram_business_basic", "instagram_business_content_publish"),
    ),
    ConnectionProviderSpec(
        "threads",
        "Threads",
        "Connect a Threads account through the official Threads API.",
        "https://developers.facebook.com/apps/",
        (("THREADS_APP_ID", "threads_app_id"), ("THREADS_APP_SECRET", "threads_app_secret")),
        ("threads_basic", "threads_content_publish"),
    ),
    ConnectionProviderSpec(
        "facebook",
        "Facebook",
        "Connect a Facebook Page managed by an authorized user.",
        "https://developers.facebook.com/apps/",
        (("META_APP_ID", "meta_app_id"), ("META_APP_SECRET", "meta_app_secret"), ("META_LOGIN_CONFIG_ID", "meta_login_config_id")),
        ("pages_show_list", "pages_manage_posts", "pages_read_engagement"),
    ),
    ConnectionProviderSpec(
        "tiktok",
        "TikTok",
        "Connect an approved TikTok Login Kit and Content Posting application.",
        "https://developers.tiktok.com/apps/",
        (("TIKTOK_CLIENT_KEY", "tiktok_client_key"), ("TIKTOK_CLIENT_SECRET", "tiktok_client_secret")),
        ("user.info.basic", "video.publish"),
    ),
    ConnectionProviderSpec(
        "youtube",
        "YouTube",
        "Authorize a YouTube channel using Google OAuth for server-side applications.",
        "https://console.cloud.google.com/apis/credentials",
        (("GOOGLE_CLIENT_ID", "google_client_id"), ("GOOGLE_CLIENT_SECRET", "google_client_secret")),
        (
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
        ),
    ),
    ConnectionProviderSpec(
        "x",
        "X",
        "Connect an X account through OAuth 2.0 Authorization Code with PKCE.",
        "https://developer.x.com/en/portal/dashboard",
        (("X_CLIENT_ID", "x_client_id"), ("X_CLIENT_SECRET", "x_client_secret")),
        ("tweet.read", "tweet.write", "users.read", "media.write", "offline.access"),
    ),
    ConnectionProviderSpec(
        "linkedin",
        "LinkedIn",
        "Authorize a LinkedIn member or organization with approved publishing access.",
        "https://www.linkedin.com/developers/apps/",
        (("LINKEDIN_CLIENT_ID", "linkedin_client_id"), ("LINKEDIN_CLIENT_SECRET", "linkedin_client_secret")),
        ("openid", "profile", "w_member_social"),
    ),
)


PROVIDER_MANUAL_CHECKS: dict[str, tuple[str, ...]] = {
    "instagram": (
        "Add the exact callback under Instagram > API setup with Instagram Login > Business login settings.",
        "Enable instagram_business_basic and instagram_business_content_publish, or add the connecting account as an Instagram Tester.",
        "Use an Instagram Professional account; direct Instagram Login does not require a linked Facebook Page.",
    ),
    "threads": (
        "Create a Meta app with the Access Threads API use case and register the exact HTTPS callback.",
        "Enable threads_basic and threads_content_publish, or add the connecting account as a Threads Tester.",
        "Use the Threads App ID and App Secret; they are separate from Facebook and Instagram credentials.",
    ),
    "facebook": (
        "Add bookmind.my.id to Meta App Domains and register the exact callback under Facebook Login for Business.",
        "Link META_LOGIN_CONFIG_ID to the active Facebook Login for Business configuration.",
        "Grant Advanced Access, or add the connecting Facebook account as an app role/tester with a manageable Page.",
    ),
    "tiktok": (
        "Register the exact HTTPS callback in Login Kit for Web.",
        "Add the Content Posting API product and obtain approval for user.info.basic and video.publish.",
        "Use an approved sandbox/test account until the TikTok application audit is complete.",
    ),
    "youtube": (
        "Register the exact callback on a Google OAuth Web application and enable the YouTube Data API v3.",
        "Add the connecting Google account as an OAuth consent-screen test user while the app is in Testing.",
        "Complete Google verification before public use of youtube.upload and youtube.readonly scopes.",
    ),
    "x": (
        "Enable OAuth 2.0 in X User authentication settings and register the exact callback URL.",
        "Configure the app as a confidential Web App/Automated App with Read and Write permission.",
        "Ensure the account can grant tweet.write and offline.access under the selected X API plan.",
    ),
    "linkedin": (
        "Register the exact HTTPS redirect URL on the LinkedIn Auth tab.",
        "Add the Sign In with LinkedIn using OpenID Connect and Share on LinkedIn products.",
        "Confirm w_member_social is granted; organization posting additionally requires approved Community Management access.",
    ),
}


def get_provider_spec(platform: str) -> ConnectionProviderSpec | None:
    return next((spec for spec in PROVIDER_SPECS if spec.platform == platform), None)


def requested_scopes(settings: Settings, spec: ConnectionProviderSpec) -> tuple[str, ...]:
    """Return provider scopes, allowing restricted Sandbox scopes to be configured."""
    if spec.platform == "tiktok" and getattr(settings, "tiktok_oauth_scopes", None):
        return tuple(
            scope.strip()
            for scope in settings.tiktok_oauth_scopes.split(",")
            if scope.strip()
        )
    return spec.requested_scopes


def missing_provider_settings(settings: Settings, spec: ConnectionProviderSpec) -> list[str]:
    missing: list[str] = []
    for environment_name, attribute in spec.required_settings:
        if spec.platform == "tiktok":
            environment = getattr(settings, "tiktok_environment", "production").strip().lower()
            if environment == "sandbox":
                client_key = getattr(settings, "tiktok_sandbox_client_key", None)
                client_secret = getattr(settings, "tiktok_sandbox_client_secret", None)
            else:
                client_key = getattr(settings, "tiktok_client_key", None)
                client_secret = getattr(settings, "tiktok_client_secret", None)
            value = client_key if attribute == "tiktok_client_key" else client_secret
            environment_name = (
                "TIKTOK_SANDBOX_CLIENT_KEY" if attribute == "tiktok_client_key" and environment == "sandbox"
                else "TIKTOK_SANDBOX_CLIENT_SECRET" if attribute == "tiktok_client_secret" and environment == "sandbox"
                else environment_name
            )
        else:
            value = getattr(settings, attribute, None)
        if spec.platform == "facebook" and attribute == "meta_app_id":
            value = getattr(settings, "meta_app_id", None) or getattr(settings, "meta_client_id", None)
        if spec.platform == "facebook" and attribute == "meta_app_secret":
            value = getattr(settings, "meta_app_secret", None) or getattr(settings, "meta_client_secret", None)
        if not value:
            missing.append(environment_name)
    if not settings.social_token_encryption_key:
        missing.append("SOCIAL_TOKEN_ENCRYPTION_KEY")
    return missing


def callback_url(settings: Settings, platform: str) -> str:
    base_url = settings.social_oauth_callback_base_url.rstrip("/")
    # One callback endpoint keeps the OAuth contract identical for providers
    # that share the Meta login flow (Facebook Pages and Instagram accounts).
    return f"{base_url}/api/v1/social/connections/oauth/callback"


def oauth_diagnostics(settings: Settings) -> dict:
    """Return OAuth readiness without returning credential values."""
    provider_results = []
    for spec in PROVIDER_SPECS:
        missing = missing_provider_settings(settings, spec)
        provider_results.append({
            "platform": spec.platform,
            "display_name": spec.display_name,
            "server_configured": not missing,
            "missing_settings": missing,
            "manual_checks": list(PROVIDER_MANUAL_CHECKS[spec.platform]),
        })

    callback = callback_url(settings, "diagnostics")
    callback_parts = urlparse(callback)
    frontend_url = settings.social_frontend_base_url.rstrip("/")
    frontend_parts = urlparse(frontend_url)
    production = getattr(settings, "is_production", False)
    callback_valid = bool(callback_parts.scheme and callback_parts.netloc)
    frontend_valid = bool(frontend_parts.scheme and frontend_parts.netloc)
    issues: list[str] = []
    if not callback_valid:
        issues.append("SOCIAL_OAUTH_CALLBACK_BASE_URL must be an absolute URL.")
    elif production and callback_parts.scheme != "https":
        issues.append("The production OAuth callback must use HTTPS.")
    if not frontend_valid:
        issues.append("SOCIAL_FRONTEND_BASE_URL must be an absolute URL.")
    elif production and frontend_parts.scheme != "https":
        issues.append("The production frontend return URL must use HTTPS.")

    encryption_ready = False
    if settings.social_token_encryption_key:
        try:
            Fernet(settings.social_token_encryption_key.encode())
            encryption_ready = True
        except (TypeError, ValueError):
            issues.append("SOCIAL_TOKEN_ENCRYPTION_KEY is not a valid Fernet key.")
    else:
        issues.append("SOCIAL_TOKEN_ENCRYPTION_KEY is missing.")

    automatic_ready = not issues and all(item["server_configured"] for item in provider_results)
    return {
        "automatic_checks_passed": automatic_ready,
        "callback_url": callback,
        "frontend_return_url": f"{frontend_url}/social/accounts",
        "callback_https": callback_parts.scheme == "https",
        "token_encryption_ready": encryption_ready,
        "issues": issues,
        "providers": provider_results,
    }
