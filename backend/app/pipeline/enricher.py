"""Pipeline — deterministic enrichment and prompt validation services."""


class EnricherService:
    """Enrich trend candidates without inventing platform evidence."""

    CATEGORY_KEYWORDS = {
        "ai_visual": {"ai", "artificial intelligence", "visual", "image", "video", "creative"},
        "beauty_skincare": {"beauty", "skin", "skincare", "makeup", "serum"},
        "fashion": {"fashion", "outfit", "style", "runway", "wear"},
        "technology": {"technology", "tech", "software", "app", "device"},
        "food": {"food", "recipe", "restaurant", "cooking", "drink"},
        "fitness": {"fitness", "workout", "gym", "training", "health"},
    }
    POSITIVE_TERMS = {"breakout", "growth", "innovative", "popular", "rising", "viral"}
    NEGATIVE_TERMS = {"backlash", "decline", "harmful", "scam", "unsafe", "controversy"}
    INDONESIAN_TERMS = {"dan", "dengan", "untuk", "yang", "viral", "tren", "kreator"}

    def enrich(self, candidate_data: dict) -> dict:
        """Enrich a candidate with additional metadata."""
        enriched = dict(candidate_data)
        text = f"{enriched.get('title') or ''} {enriched.get('caption') or ''}".lower()
        words = set(text.replace("/", " ").replace("-", " ").split())

        if not enriched.get("language"):
            enriched["language"] = "id" if words & self.INDONESIAN_TERMS else "en"

        positive_hits = sum(term in text for term in self.POSITIVE_TERMS)
        negative_hits = sum(term in text for term in self.NEGATIVE_TERMS)
        sentiment = "positive" if positive_hits > negative_hits else (
            "negative" if negative_hits > positive_hits else "neutral"
        )
        category_scores = {
            category: sum(keyword in text for keyword in keywords)
            for category, keywords in self.CATEGORY_KEYWORDS.items()
        }
        best_category, best_score = max(category_scores.items(), key=lambda item: item[1])

        payload = dict(enriched.get("raw_payload") or {})
        payload["enrichment"] = {
            "detected_language": enriched["language"],
            "sentiment": sentiment,
            "suggested_category": best_category if best_score else "other",
            "category_confidence": round(min(1.0, best_score / 3.0), 2),
        }
        enriched["raw_payload"] = payload
        return enriched


class ValidatorService:
    """Validates prompt packages and AI outputs.

    Ensures generated content meets quality standards before storage.
    """

    def validate_prompt_package(self, package_data: dict) -> tuple[bool, list[str]]:
        """Validate a prompt package. Returns (is_valid, error_list)."""
        errors: list[str] = []

        if not package_data.get("image_prompt"):
            errors.append("Missing image_prompt")
        if not package_data.get("trend_title"):
            errors.append("Missing trend_title")

        # Check prompt lengths
        image_prompt = package_data.get("image_prompt", "")
        if len(image_prompt) < 10:
            errors.append("image_prompt too short (min 10 chars)")
        if len(image_prompt) > 5000:
            errors.append("image_prompt too long (max 5000 chars)")

        # Check for blocked content
        blocked_terms = ["explicit", "nsfw", "violence"]
        for field_name in ["image_prompt", "negative_prompt", "text_to_video_prompt"]:
            content = package_data.get(field_name, "").lower()
            for term in blocked_terms:
                if term in content:
                    errors.append(f"Blocked term '{term}' found in {field_name}")

        return len(errors) == 0, errors
