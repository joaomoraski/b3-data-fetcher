from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "B3 Data Fetcher"
    API_V1_STR: str = "/api/v1"
    CACHE_TTL_MINUTES: int = Field(default=30)
    POSTGRES_USER: str = Field()
    POSTGRES_PASSWORD: str = Field()
    POSTGRES_DB: str = Field()
    APP_POSTGRESQL_URI: str = Field()

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
