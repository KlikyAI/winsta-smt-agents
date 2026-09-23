"""AI Autonomous Trend Discovery Agent.

A Multi-Provider LangGraph/Node pipeline that synthesizes real-world, high-virality
trend candidates tailored to target country, niche, aesthetic, and time-window.
Includes robust partial JSON recovery to guarantee zero decode failures.
"""

import json
import hashlib
import re
import urllib.parse
from typing import Any, Optional
import httpx
import structlog

from app.collectors.base import TrendCandidateData
from app.core.config import get_settings
from app.modules.ai.services.service import ai_service

logger = structlog.get_logger()

COUNTRY_CONTEXT_MAP = {
    "ID": "Indonesia (Jakarta, Bandung, Surabaya tech & social media culture, Bahasa Indonesia slang & viral hooks)",
    "KW": "Kuwait (Kuwait City luxury, Gulf trends, Arabic/Khaleeji creative culture)",
    "SA": "Saudi Arabia (Riyadh, Jeddah Vision 2030, modern Arabic viral social media)",
    "US": "United States (Silicon Valley, NYC, LA viral TikTok/Reels/YouTube Shorts tech & culture)",
    "GB": "United Kingdom (London tech, creative digital culture)",
    "SG": "Singapore (Southeast Asia tech hub, fintech, modern lifestyle)",
    "AE": "United Arab Emirates (Dubai, Abu Dhabi innovation, luxury AI & social media)",
}


def safe_parse_json_array(text: str) -> list[dict]:
    """Parse JSON array with robust partial recovery if output was truncated."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t.rsplit("```", 1)[0]
    t = t.strip()

    # 1. Direct standard parse
    try:
        data = json.loads(t)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("trends", data.get("items", [data]))
    except Exception:
        pass

    # 2. Resilient partial recovery for truncated arrays
    last_brace = t.rfind("}")
    if last_brace != -1:
        truncated = t[:last_brace + 1].strip()
        first_bracket = truncated.find("[")
        if first_bracket != -1:
            truncated = truncated[first_bracket:]
        else:
            truncated = "[" + truncated
        if not truncated.endswith("]"):
            truncated = truncated + "]"
        try:
            data = json.loads(truncated)
            if isinstance(data, list):
                return data
        except Exception:
            pass

    # 3. Regex extraction of individual trend JSON objects
    obj_matches = re.findall(r'\{[^{}]*?"title"[^{}]*?\}', t, re.DOTALL)
    recovered = []
    for m in obj_matches:
        try:
            parsed_obj = json.loads(m)
            if isinstance(parsed_obj, dict) and "title" in parsed_obj:
                recovered.append(parsed_obj)
        except Exception:
            continue

    return recovered


class AutonomousTrendDiscoveryAgent:
    """Agent that synthesizes platform-native, high-engagement viral trend candidates."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def discover_platform_candidates(
        self,
        platform: str,
        category: str,
        market: str = "ID",
        language: str = "en",
        aesthetic: str = "minimalist_organic",
        time_window: str = "24h",
        limit: int = 5,
    ) -> list[TrendCandidateData]:
        """Generate platform-specific viral trend candidates using active LLM (DeepSeek/OpenAI/Claude)."""
        safe_limit = min(max(1, limit), 6)
        market_upper = (market or "ID").upper()
        country_context = COUNTRY_CONTEXT_MAP.get(market_upper, f"Country: {market_upper}")
        clean_category = (category or "general").replace("_", " ").title()

        system_prompt = (
            "You are an elite Social Media Trend Forecaster and Viral AI Intelligence Agent. "
            f"Discover {safe_limit} realistic, breaking viral trends currently exploding on "
            f"{platform.upper()} in {country_context} for the niche: '{clean_category}'.\n\n"
            "Return ONLY a JSON array of trend objects. Each trend object MUST strictly follow this JSON schema:\n"
            "[\n"
            "  {\n"
            '    "title": "Short, punchy, viral trend title",\n'
            '    "caption": "Realistic creator post caption with context and scenario details",\n'
            '    "author_name": "@creator_handle",\n'
            '    "hashtags": ["tag1", "tag2", "tag3"],\n'
                '    "media_type": "video"\n'
            "  }\n"
            "]"
        )

        user_prompt = (
            f"Discover exactly {safe_limit} viral trend topics for:\n"
            f"- Platform: {platform.upper()}\n"
            f"- Region: {country_context}\n"
            f"- Niche / Category: {clean_category}\n"
            f"- Aesthetic / Tone: {aesthetic}\n"
            f"- Timeframe: Last {time_window} viral surge\n\n"
            "Requirements:\n"
            "1. Ground the trends in authentic current discussions, creative concepts, and cultural hooks.\n"
            "2. Do not invent engagement or audience metrics.\n"
            "3. Keep captions concise and punchy (1-2 sentences).\n"
            "4. Return strictly valid JSON array."
        )

        try:
            resp = await ai_service.generate(
                capability="trend_discovery",
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                max_tokens=3000,
                temperature=0.8,
            )

            items_data = safe_parse_json_array(resp.content)
            if not items_data:
                logger.warning("ai_discovery_empty_parse", raw=resp.content[:200])

            results: list[TrendCandidateData] = []
            for item in items_data[:safe_limit]:
                title = str(item.get("title", "Emerging Trend")).strip()
                caption = str(item.get("caption", title)).strip()
                author = str(item.get("author_name", f"@{platform}_creator")).strip()
                tags = [str(t).replace("#", "").strip() for t in item.get("hashtags", []) if t]

                # Construct 100% working live platform search & tag explore URLs
                main_tag = "".join(c for c in (tags[0] if tags else clean_category).replace(" ", "") if c.isalnum())
                encoded_title = urllib.parse.quote_plus(f"{title}")
                encoded_tag = urllib.parse.quote(main_tag)

                url_templates = {
                    "tiktok": f"https://www.tiktok.com/search?q={encoded_title}",
                    "instagram": f"https://www.instagram.com/explore/tags/{encoded_tag}/",
                    "youtube": f"https://www.youtube.com/results?search_query={encoded_title}",
                    "x": f"https://x.com/search?q={encoded_title}&src=typed_query&f=live",
                    "linkedin": f"https://www.linkedin.com/feed/hashtag/?keywords={encoded_tag}",
                    "google_trends": f"https://trends.google.com/trends/explore?geo={market_upper}&q={encoded_title}",
                }
                canonical = url_templates.get(platform, f"https://trends.google.com/trends/explore?geo={market_upper}&q={encoded_title}")

                # If platform is YouTube, resolve real direct video link
                if platform == "youtube":
                    try:
                        search_html_url = f"https://www.youtube.com/results?search_query={encoded_title}"
                        async with httpx.AsyncClient(timeout=3.0) as http_c:
                            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
                            html_res = await http_c.get(search_html_url, headers=headers)
                            v_match = re.search(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html_res.text)
                            if v_match:
                                canonical = f"https://www.youtube.com/watch?v={v_match.group(1)}"
                    except Exception:
                        pass

                candidate = TrendCandidateData(
                    platform=platform,
                    external_id="ai:" + hashlib.sha256(
                        f"{platform}|{market_upper}|{title}".encode()
                    ).hexdigest()[:24],
                    title=title,
                    caption=caption,
                    canonical_url=canonical,
                    author_name=author,
                    hashtags=tags or [platform, clean_category.lower()],
                    engagement_rate=None,
                    view_count=None,
                    like_count=None,
                    comment_count=None,
                    share_count=None,
                    media_type=item.get("media_type", "video"),
                    language=language or "en",
                    raw_payload={
                        "data_quality": "llm_agent_synthesized",
                        "synthesized_by": resp.provider,
                        "model": resp.model,
                        "market": market_upper,
                        "category": category,
                    },
                )
                results.append(candidate)

            if results:
                logger.info(
                    "ai_discovery_completed",
                    platform=platform,
                    market=market_upper,
                    count=len(results),
                    provider=resp.provider,
                )
                return results

        except Exception as e:
            logger.warning("ai_discovery_agent_failed", platform=platform, error=str(e))

        return []


trend_discovery_agent = AutonomousTrendDiscoveryAgent()
