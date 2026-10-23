"""
LLM provider selection
Picks the client configured by LLM_PROVIDER (groq | claude)
"""

from typing import Optional, Union

from app.config import settings
from app.llm.claude import ClaudeClient
from app.llm.groq_client import GroqClient

LLMClient = Union[GroqClient, ClaudeClient]

PROVIDERS = {
    "groq": GroqClient,
    "claude": ClaudeClient,
}

# API key setting for each provider (used by the readiness check)
PROVIDER_KEYS = {
    "groq": lambda: settings.groq_api_key,
    "claude": lambda: settings.anthropic_api_key,
}

# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """Get or create the configured LLM client instance"""
    global _llm_client
    if _llm_client is None:
        provider = settings.llm_provider.lower()
        if provider not in PROVIDERS:
            raise ValueError(f"Unknown LLM_PROVIDER '{settings.llm_provider}' - expected one of {list(PROVIDERS)}")
        print(f"[LLM] Creating {provider} client...")
        _llm_client = PROVIDERS[provider]()
    return _llm_client


def reset_llm_client():
    """Reset the singleton to force recreation with new settings"""
    global _llm_client
    _llm_client = None
    print("[LLM] Client reset - will be recreated on next use")


def llm_key_configured() -> bool:
    """Whether the selected provider has an API key set"""
    get_key = PROVIDER_KEYS.get(settings.llm_provider.lower())
    return bool(get_key and get_key())
