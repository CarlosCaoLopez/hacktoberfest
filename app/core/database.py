# app/core/database.py
import asyncio
from typing import Optional
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.drone import Drone
from app.models.medication import Medication


class Database:
    client: Optional[AsyncIOMotorClient] = None


database = Database()


async def connect_to_mongo():
    """Conecta a MongoDB usando Beanie"""
    database.client = AsyncIOMotorClient(settings.mongodb_url)

    await init_beanie(
        database=database.client[settings.database_name],
        document_models=[Drone, Medication]
    )


async def close_mongo_connection():
    """Cierra la conexión a MongoDB"""
    if database.client:
        database.client.close()