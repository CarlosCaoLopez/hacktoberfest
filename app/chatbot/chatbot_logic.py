# app/chatbot/chatbot_logic.py
import json
import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

MQTT_TOPIC_CHECK_BATTERY = os.getenv("MQTT_TOPIC_CHECK_BATTERY", "drones/check_battery")
MQTT_TOPIC_LOAD = os.getenv("MQTT_TOPIC_LOAD", "drones/load")
MQTT_TOPIC_GET_MEDICATIONS = os.getenv("MQTT_TOPIC_GET_MEDICATIONS", "drones/get_medications")
CHATBOT_TOPIC_OUT = os.getenv("CHATBOT_TOPIC_OUT", "chatbot/out")

async def process_chat_message(client, message):
    """
    Procesa mensajes recibidos del chatbot y publica los comandos
    o respuestas correspondientes vía MQTT.
    """
    text = message.payload.decode().lower()
    print(f"🗣️ Usuario dijo: {text}")

    # --- Comando: verificar batería ---
    if "batería" in text:
        parts = text.split()
        try:
            drone_id = next(p for p in parts if p.isdigit())
            topic = f"{MQTT_TOPIC_CHECK_BATTERY}/{drone_id}"
            await client.publish(topic, "")  # solo necesitamos el topic
            await client.publish(
                CHATBOT_TOPIC_OUT,
                f"⏳ Consultando batería del dron {drone_id}..."
            )
        except StopIteration:
            await client.publish(
                CHATBOT_TOPIC_OUT,
                "❌ No pude identificar el número del dron."
            )

    # --- Comando: cargar drone ---
    elif "cargar" in text or "carga" in text:
        try:
            parts = text.split()
            drone_id = next(p for p in parts if p.isdigit())
            
            # Obtenemos los items de medicación
            if "con" in text:
                items_text = text.split("con")[-1].strip()
                items_list = [
                    {"name": it.strip(),
                     "weight": 10,  # default, ajustar según tu lógica
                     "code": it.strip().upper(),
                     "image": ""}
                    for it in items_text.split(",")
                ]
            else:
                items_list = []

            payload = json.dumps(items_list)
            topic = f"{MQTT_TOPIC_LOAD}/{drone_id}"
            await client.publish(topic, payload)

            await client.publish(
                CHATBOT_TOPIC_OUT,
                f"🚀 Enviando comando de carga al dron {drone_id} con {len(items_list)} item(s)..."
            )
        except Exception as e:
            print("Error procesando comando de carga:", e)
            await client.publish(
                CHATBOT_TOPIC_OUT,
                "❌ Formato inválido para cargar el dron."
            )

    # --- Comando: consultar medicamentos cargados ---
    elif "medicamentos" in text:
        parts = text.split()
        try:
            drone_id = next(p for p in parts if p.isdigit())
            topic = f"{MQTT_TOPIC_GET_MEDICATIONS}/{drone_id}"
            await client.publish(topic, "")
            await client.publish(
                CHATBOT_TOPIC_OUT,
                f"⏳ Consultando medicamentos cargados en el dron {drone_id}..."
            )
        except StopIteration:
            await client.publish(
                CHATBOT_TOPIC_OUT,
                "❌ No pude identificar el número del dron."
            )

    # --- Comando no reconocido ---
    else:
        await client.publish(
            CHATBOT_TOPIC_OUT,
            "🤖 No entendí el comando. Prueba con:\n"
            "- 'batería del dron 100'\n"
            "- 'cargar dron 100 con medicinaA, medicinaB'\n"
            "- 'medicamentos del dron 100'"
        )
