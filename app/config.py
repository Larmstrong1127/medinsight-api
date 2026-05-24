from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MedInsight API"
    environment: str = "development"
    debug: bool = False

    # Security
    api_key_header: str = "X-API-Key"
    api_keys: list[str] = ["dev-key-change-me-in-production"]

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
