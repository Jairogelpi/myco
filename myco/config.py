import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/myco.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OpenRouter unified API (replaces single OpenAI dependency)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Legacy fallback for old env files
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    
    KERNEL_TAX_RATE: float = 0.15
    AGENT_BUDGET_DEFAULT: float = 100.0
    MAX_ACTIVE_AGENTS: int = 20
    AGENT_LIFESPAN_HOURS: int = 72
    
    class Config:
        env_file = ".env"

settings = Settings()
