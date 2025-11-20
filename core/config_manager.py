"""Configuration management for AYITI AI system."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # DeepSeek API Configuration
    deepseek_api_key: str
    deepseek_api_base: str = "https://api.deepseek.com/v1"

    # Vector Database Configuration
    vector_db_path: str = "./data/vector_db"
    vector_db_type: str = "chromadb"

    # Knowledge Base Configuration
    knowledge_base_path: str = "./knowledge_base"

    # LLM Configuration
    max_tokens: int = 4000
    temperature: float = 0.7
    model_name: str = "deepseek-chat"

    # Cost Management
    cost_limit_daily: float = 50.00
    cost_alert_threshold: float = 40.00

    # Language Support
    supported_languages: List[str] = ["ht", "fr", "en", "es"]
    default_language: str = "ht"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug_mode: bool = False

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
