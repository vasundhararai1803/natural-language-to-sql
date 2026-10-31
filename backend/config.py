"""
Application Configuration Service for QueryLens AI.
Uses Pydantic BaseSettings-like model with environment variable support and fallbacks.
"""
import os
from typing import List
from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Lightweight environment-backed BaseSettings fallback using pydantic BaseModel
    class BaseSettings(BaseModel):
        def __init__(self, **values):
            super().__init__(**values)
            # Override from os.environ if present
            for field_name in self.__class__.model_fields:
                env_val = os.environ.get(field_name.upper())
                if env_val is not None:
                    field_type = self.model_fields[field_name].annotation
                    if field_type == int:
                        setattr(self, field_name, int(env_val))
                    elif field_type == float:
                        setattr(self, field_name, float(env_val))
                    elif field_type == bool:
                        setattr(self, field_name, env_val.lower() in ("true", "1", "yes"))
                    elif field_type == List[str] or getattr(field_type, "__origin__", None) == list:
                        setattr(self, field_name, [x.strip() for x in env_val.split(",") if x.strip()])
                    else:
                        setattr(self, field_name, env_val)


class Settings(BaseSettings):
    app_name: str = "QueryLens AI"
    environment: str = "production"
    debug: bool = False
    
    # Database
    database_url: str = Field(default="sqlite:///data/querylens.db")
    query_timeout_seconds: float = Field(default=5.0)
    default_row_limit: int = Field(default=500)
    max_row_limit: int = Field(default=2000)
    
    # LLM & AI
    openai_api_key: str = Field(default="")
    openai_base_url: str = Field(default="https://api.groq.com/openai/v1")
    openai_model: str = Field(default="llama-3.3-70b-versatile")
    
    # Security & CORS
    allowed_origins: List[str] = Field(default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"])
    api_rate_limit_per_minute: int = Field(default=60)
    api_secret_key: str = Field(default="")


settings = Settings()
