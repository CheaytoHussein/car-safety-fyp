from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/car_safety_db"

    model_config = {"env_file": ".env"}


settings = Settings()
