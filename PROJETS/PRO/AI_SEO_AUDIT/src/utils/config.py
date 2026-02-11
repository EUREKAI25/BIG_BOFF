"""Configuration utilities."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    environment: str = "development"

    # Database
    database_url: str = "postgresql://ai_seo_user:ai_seo_password@localhost:5432/ai_seo_audit"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 86400

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.3

    # Stripe
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""
    stripe_price_pro: str = ""

    # Application
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: str = "http://localhost:3000"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 86400

    # Monitoring
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
