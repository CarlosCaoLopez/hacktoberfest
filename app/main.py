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
from app.services.battery_monitor import battery_monitor

app = FastAPI(
    title="Drones Dispatch API",
    description="API REST para la comunicación con un controlador de gestión de entregas de medicación mediante drones.",
    version="1.0.0"
)

# Modelo de datos para recibir mensajes del chatbot
class ChatbotMessage(BaseModel):
    message: str
    sender_identifier: str

@app.post("/send")
async def send_message(data: ChatbotMessage):
    """
    Endpoint que recibe un mensaje desde el frontend y llama a process_message().
    """
    try:
        print(f"📩 Mensaje recibido: {data.message} (sender={data.sender_identifier})")

        # Llamar a tu función asíncrona
        response = await process_message(
            message_text=data.message,
            sender_id=data.sender_identifier
        )

        # Validar la respuesta
        if not response:
            raise HTTPException(status_code=500, detail="No se recibió respuesta del sistema de drones.")

        # Puedes devolver directamente el dict o formatear la respuesta
        return {"response": response}

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Tiempo de espera agotado esperando la respuesta del dron.")

    except Exception as e:
        print(f"❌ Error en /send: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    # Inicia el listener MQTT en segundo plano
    asyncio.create_task(mqtt_listener())
    # asyncio.create_task(chatbot_mqtt())

    # Iniciar el monitor de batería
    await battery_monitor.start(interval_seconds=30)

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    # Detener el monitor de batería
    await battery_monitor.stop()

app.include_router(drones.router)
app.include_router(medications.router)
