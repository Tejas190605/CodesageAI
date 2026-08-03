from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration using Pydantic Settings."""

    # Required Secrets (No default values provided)
    GEMINI_API_KEY: str
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str

    # Configurable Operational Parameters with Defaults
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GITHUB_API_TIMEOUT: int = 30
    MAX_PATCH_CHARS_PER_FILE: int = 12000
    MAX_TOTAL_DIFF_CHARS: int = 60000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def get_settings() -> Settings:
    """Returns the validated application settings instance."""
    return Settings()


# Singleton instance for application-wide import
settings = get_settings()
