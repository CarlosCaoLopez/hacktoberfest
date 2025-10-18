# app/main.py
import os
from dotenv import load_dotenv

# Cargar las variables del .env al inicio
load_dotenv()

import asyncio
from fastapi import FastAPI
from app.routes import drones, medications
from app.mqtt.client import mqtt_listener
from app.chatbot.chatbot_client import chatbot_mqtt

app = FastAPI(
    title="Drones Dispatch API",
    description="API REST para la comunicación con un controlador de despacho de drones.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(mqtt_listener())
    asyncio.create_task(chatbot_mqtt())

app.include_router(drones.router)
app.include_router(medications.router)
