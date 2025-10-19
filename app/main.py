# app/main.py
import os
from dotenv import load_dotenv

# Cargar las variables del .env al inicio
load_dotenv()

import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.routes import drones, medications
from app.mqtt.consumer import mqtt_listener
from app.chatbot.chatbot_client import process_message
from app.core.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Drones Dispatch API",
    description="API REST para la comunicación con un controlador de despacho de drones.",
    version="1.0.0"
)

# Modelo de datos para recibir mensajes del chatbot
class ChatbotMessage(BaseModel):
    message: str
    sender_identifier: str

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    # Inicia el listener MQTT en segundo plano
    asyncio.create_task(mqtt_listener())

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Endpoint para enviar mensajes al chatbot
@app.post("/send")
async def send_to_chatbot(data: ChatbotMessage):
    try:
        print(f"Mensaje de entrada: '{data.message}'")
        # Procesar el mensaje
        response = await process_message(data.message, data.sender_identifier)
        print(f"Respuesta del Chatbot: '{response}'")
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Routers existentes
app.include_router(drones.router)
app.include_router(medications.router)
