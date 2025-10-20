# app/core/database.py
import os
import asyncio
from typing import Optional
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.models.drone import Drone
from app.models.medication import Medication

load_dotenv()

class Database:
    client: Optional[AsyncIOMotorClient] = None

database = Database()

async def connect_to_mongo():
    """Conecta a MongoDB usando Beanie"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "drones_db")

    database.client = AsyncIOMotorClient(mongodb_url)

    await init_beanie(
        database=database.client[database_name],
        document_models=[Drone, Medication]
    )

async def close_mongo_connection():
    """Cierra la conexión a MongoDB"""
    if database.client:
        database.client.close()