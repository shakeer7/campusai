import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Core Application
    APP_NAME: str = "CampusAI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # Database Settings
    POSTGRES_USER: str = "campusai_user"
    POSTGRES_PASSWORD: str = "campusai_secure_pass"
    POSTGRES_DB: str = "campusai_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "sqlite:///./campusai.db"  # Defaults to local SQLite for zero-friction local run/test

    # Authentication & JWT
    JWT_SECRET_KEY: str = "campusai_super_secret_jwt_key_minimum_32_characters_for_security_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AWS Bedrock Settings
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_SESSION_TOKEN: str = ""
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"
    BEDROCK_MAX_TOKENS: int = 2048
    BEDROCK_TEMPERATURE: float = 0.2
    AWS_BEDROCK_MOCK_FALLBACK: bool = True

    # S3 Document Storage
    AWS_S3_BUCKET_DOCUMENTS: str = "campusai-academic-documents-prod"
    AWS_S3_ENDPOINT_URL: str = ""

    # Speech Services
    AWS_POLLY_VOICE_EN: str = "Aditi"
    AWS_POLLY_VOICE_HI: str = "Aditi"
    AWS_POLLY_ENGINE: str = "neural"
    SPEECH_SERVICE_ENABLED: bool = True

    # MCP Server
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 8001
    MCP_API_KEY: str = "campusai_mcp_secure_token_key_2026"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


settings = Settings()
