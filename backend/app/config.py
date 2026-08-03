from typing import List, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration using Pydantic Settings."""

    # Required Secrets (No default values provided)
    GEMINI_API_KEY: str
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str

    # Monitored Repositories & CORS Configuration
    CODESAGE_REPOSITORIES: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"

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

    @property
    def monitored_repositories(self) -> List[Tuple[str, str]]:
        """
        Parses CODESAGE_REPOSITORIES comma-separated string into a list of validated (owner, repo) tuples.
        Ignores empty entries and malformed repository identifiers cleanly.
        """
        repos: List[Tuple[str, str]] = []
        if not self.CODESAGE_REPOSITORIES:
            return repos

        for raw_item in self.CODESAGE_REPOSITORIES.split(","):
            item = raw_item.strip()
            if not item or "/" not in item:
                continue
            parts = item.split("/")
            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                repos.append((parts[0].strip(), parts[1].strip()))
        return repos

    @property
    def cors_origins_list(self) -> List[str]:
        """Parses CORS_ORIGINS comma-separated string into a list of allowed origins."""
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


def get_settings() -> Settings:
    """Returns the validated application settings instance."""
    return Settings()


# Singleton instance for application-wide import
settings = get_settings()
