from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "VeriScholar"
    api_prefix: str = "/api/v1"
    database_url: str = "******db:5432/verischolar"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]
    max_csv_size_mb: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
