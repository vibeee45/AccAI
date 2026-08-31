from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change_me"
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
