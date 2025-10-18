# app/core/config.py
from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    # Configuración MongoDB
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://root:hacktoberfest@localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "drone_dispatch")

    class Config:
        env_file = ".env"


settings = Settings()

