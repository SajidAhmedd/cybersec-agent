"""
Application Configuration
Loads settings from environment variables with validation
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_name: str = Field(default="CyberSecAgent")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    secret_key: str = Field(default="change-me-in-production")

    # -------------------------------------------------------------------------
    # Deployment / Security
    # -------------------------------------------------------------------------
    # Comma-separated origins allowed to call the API (the frontend's URL)
    allowed_origins: str = Field(default="http://localhost:3000")
    # Required in the X-Admin-Key header to create/update/delete experts.
    # Leave empty to disable those endpoints entirely.
    admin_api_key: str = Field(default="")
    # Per-IP limits on chat requests (protects the LLM quota)
    chat_rate_limit_per_minute: int = Field(default=10)
    chat_rate_limit_per_day: int = Field(default=100)

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # -------------------------------------------------------------------------
    # LLM provider: groq | claude
    # -------------------------------------------------------------------------
    llm_provider: str = Field(default="groq")

    # -------------------------------------------------------------------------
    # LLM - Groq
    # -------------------------------------------------------------------------
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="openai/gpt-oss-120b")
    groq_reasoning_effort: str = Field(default="low")  # low | medium | high (gpt-oss models only)

    # -------------------------------------------------------------------------
    # LLM - Anthropic Claude
    # -------------------------------------------------------------------------
    anthropic_api_key: str = Field(default="")
    claude_model: str = Field(default="claude-opus-5-5")
    claude_effort: str = Field(default="low")  # low | medium | high | xhigh | max

    # -------------------------------------------------------------------------
    # Mock Mode (for testing without API)
    # -------------------------------------------------------------------------
    use_mock_llm: bool = Field(default=False)

    # -------------------------------------------------------------------------
    # LLM - Foundation-Sec-8B
    # -------------------------------------------------------------------------
    huggingface_token: Optional[str] = Field(default=None)
    foundation_sec_model: str = Field(default="fdtn-ai/Foundation-Sec-8B")
    use_local_security_model: bool = Field(default=False)

    # -------------------------------------------------------------------------
    # PostgreSQL
    # -------------------------------------------------------------------------
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="cybersec_agent")
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    # e.g. "require" for hosted databases such as Neon
    postgres_sslmode: str = Field(default="")

    @property
    def database_url(self) -> str:
        url = f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        if self.postgres_sslmode:
            url += f"?sslmode={self.postgres_sslmode}"
        return url

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # -------------------------------------------------------------------------
    # Neo4j
    # -------------------------------------------------------------------------
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="neo4j")

    # -------------------------------------------------------------------------
    # Twilio (WhatsApp)
    # -------------------------------------------------------------------------
    twilio_account_sid: Optional[str] = Field(default=None)
    twilio_auth_token: Optional[str] = Field(default=None)
    twilio_whatsapp_number: Optional[str] = Field(default=None)

    # -------------------------------------------------------------------------
    # SendGrid (Email)
    # -------------------------------------------------------------------------
    sendgrid_api_key: Optional[str] = Field(default=None)
    sendgrid_from_email: Optional[str] = Field(default=None)

    # Send real WhatsApp/Email notifications to experts on handoff
    outreach_enabled: bool = Field(default=False)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get fresh settings instance (no cache for development)"""
    return Settings()


# Export settings instance - reload each time for development
settings = Settings()

# Debug: Print settings on load
print(f"[CONFIG] Loaded settings - USE_MOCK_LLM: {settings.use_mock_llm}")
print(f"[CONFIG] LLM_PROVIDER: {settings.llm_provider}")
