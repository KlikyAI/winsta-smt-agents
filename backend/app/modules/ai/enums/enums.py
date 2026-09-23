"""AI module enums."""

from enum import Enum


class AICapability(str, Enum):
    """Logical AI capabilities — used to route requests."""
    TREND_ANALYSIS = "trend_analysis"
    CONCEPT_EXTRACTION = "concept_extraction"
    PROMPT_GENERATION = "prompt_generation"
    PROMPT_VALIDATION = "prompt_validation"
    CLASSIFICATION = "classification"
    SOCIAL_COPYWRITING = "social_copywriting"


class AIProviderType(str, Enum):
    """Supported AI provider backends."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    MISTRAL = "mistral"
    LITELLM = "litellm"
    CUSTOM = "custom"


class AIExecutionStatus(str, Enum):
    """Status of an AI execution attempt."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
