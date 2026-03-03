from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TalentLens"
    env: str = "development"
    debug: bool = False
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    backend_port: int = 8000

    # PostgreSQL (Supabase)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/talentlens"

    # Anthropic
    anthropic_api_key: str = ""

    # Deepgram
    deepgram_api_key: str = ""

    # Fireflies
    fireflies_api_key: str = ""
    fireflies_webhook_secret: str = ""

    # Slack
    slack_bot_token: str = ""
    slack_default_channel: str = ""

    # CoderPad
    coderpad_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ("../.env", ".env")


settings = Settings()
