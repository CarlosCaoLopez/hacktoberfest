# app/mqtt/consumer.py
import asyncio
import json
import os
from aiohttp import ClientSession
from dotenv import load_dotenv
from aiomqtt import Client

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC_UNICO", "chatbot/topic")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")


async def process_message(session: ClientSession, client: Client, message: dict):
    """
    Procesa un mensaje MQTT:
    - Si tipo == "pregunta", llama al endpoint correspondiente usando el método indicado.
    - Publica la respuesta en el mismo topic con tipo "respuesta".
    """
    if message.get("tipo") != "pregunta":
        return

    endpoint = message.get("endpoint")
    method = message.get("method", "POST").upper()
    payload = message.get("payload", {})

    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

    try:
        if method == "POST":
            print(f"➡️ Llamando {method} {url} con payload: {payload}")
            async with session.post(url, json=payload) as resp:
                resp_json = await resp.json()
                print(f"⬅️ Respuesta recibida: {resp_json}")
        elif method == "GET":
            print(f"➡️ Llamando {method} {url} con params: {payload}")
            async with session.get(url, params=payload) as resp:
                resp_json = await resp.json()
                print(f"⬅️ Respuesta recibida: {resp_json}")
        elif method == "PUT":
            async with session.put(url, json=payload) as resp:
                resp_json = await resp.json()
        elif method == "DELETE":
            async with session.delete(url, json=payload) as resp:
                resp_json = await resp.json()
        else:
            resp_json = {"error": f"Método HTTP no soportado: {method}"}
    except Exception as e:
        resp_json = {"error": str(e)}

    # Construir mensaje de respuesta
    response_msg = {
        "tipo": "respuesta",
        "endpoint": endpoint,
        "payload": resp_json
    }

    print(f"Imprimiendo respuesta en topic {MQTT_TOPIC}: {response_msg}")

    # Publicar la respuesta en el mismo topic
    await client.publish(MQTT_TOPIC, json.dumps(response_msg))
    print(f"✅ Procesado mensaje tipo 'pregunta' para endpoint {endpoint}")


async def mqtt_listener():
    """
    Escucha el topic único y procesa mensajes de tipo 'pregunta'.
    """
    async with Client(MQTT_BROKER, port=MQTT_PORT) as client, ClientSession() as session:
        await client.subscribe(MQTT_TOPIC)

        # Iteramos directamente sobre el async iterator
        async for msg in client.messages:
            try:
                message_json = json.loads(msg.payload.decode())
                await process_message(session, client, message_json)
            except Exception as e:
                print("Error procesando mensaje MQTT:", e)



if __name__ == "__main__":
    asyncio.run(mqtt_listener())
