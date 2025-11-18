import secrets
import warnings
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, (list | str)):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    # Load env from project root: rue-api/.env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # --- App ---
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str = "RUE API"
    SENTRY_DSN: HttpUrl | None = None

    DB_SCHEME: str = "sqlite"  # "sqlite" or "postgresql+psycopg"
    SQLITE_DB_PATH: str = "volumes/rue.db"  # used when DB_SCHEME=sqlite

    # Postgres fields (used when DB_SCHEME startswith("postgres"))
    POSTGRES_SERVER: str | None = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        scheme = (self.DB_SCHEME or "sqlite").lower()
        if scheme.startswith("sqlite"):
            # Local file in project root
            return f"sqlite:///./{self.SQLITE_DB_PATH}"
        # default to postgres-like URL if not sqlite
        user = self.POSTGRES_USER or ""
        pwd = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
        auth = f"{user}{pwd}@" if user else ""
        host = self.POSTGRES_SERVER or "localhost"
        port = f":{self.POSTGRES_PORT}" if self.POSTGRES_PORT else ""
        db = self.POSTGRES_DB or "postgres"
        return f"{scheme}://{auth}{host}{port}/{db}"

    # --- Email / SMTP ---
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME  # type: ignore[assignment]
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # --- Bootstrap user ---
    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        # Only enforce Postgres password if actually using Postgres
        if self.DB_SCHEME.lower().startswith("postgres"):
            self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret("FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD)
        return self

    PROJECT_FILE_DIR: Path = Path("volumes/files/project")


settings = Settings()  # type: ignore
settings.PROJECT_FILE_DIR.mkdir(parents=True, exist_ok=True)
