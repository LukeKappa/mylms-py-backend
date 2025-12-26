from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 3001
    MOODLE_URL: str = "https://moodle.example.com"
    MOODLE_SERVICE: str = "moodle_mobile_app"

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
