from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    gemini_model: str = "gemini-3.7-flash"
    openai_model: str = "gpt-5.6-luna"
    anthropic_model: str = "claude-sonnet-5"

    ai_timeout_seconds: float = 60.0
    ai_max_retries: int = 2

    gemini_soft_request_limit: int = 0
    openai_soft_request_limit: int = 0
    anthropic_soft_request_limit: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()