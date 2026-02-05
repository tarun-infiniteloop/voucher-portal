from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str = "CHANGE_ME_DEV_SECRET"
    JWT_ALGO: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60 * 24  # 1 day

settings = Settings()
