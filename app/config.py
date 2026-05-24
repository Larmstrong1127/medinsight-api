from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MedInsight API"
    environment: str = "development"
    debug: bool = False

    # Security — stored as comma-separated string to avoid pydantic-settings JSON parsing
    api_key_header: str = "X-API-Key"
    api_keys: str = "dev-key-change-me-in-production"

    def get_api_keys(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Encryption — Fernet key for document content at rest
    encryption_key: str = ""

    # Storage
    storage_backend: str = "local"  # "local" | "aws"
    local_storage_path: str = "./data"

    # AWS
    aws_region: str = "us-east-1"
    s3_bucket: str = "medinsight-documents-prod"
    dynamodb_table: str = "medinsight-documents"
    audit_table: str = "medinsight-audit-logs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
