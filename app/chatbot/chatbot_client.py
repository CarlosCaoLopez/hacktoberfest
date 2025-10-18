""" # app/chatbot/chatbot_client.py
import os
import asyncio
from aiomqtt import Client, MqttError
from dotenv import load_dotenv
from app.chatbot.chatbot_logic import process_chat_message

# Cargar variables del .env
load_dotenv()

# Broker
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

# Topics de comandos del chatbot
CHATBOT_TOPIC_DRONES_REGISTER = os.getenv("CHATBOT_TOPIC_DRONES_REGISTER")
CHATBOT_TOPIC_DRONES_AVAILABLE = os.getenv("CHATBOT_TOPIC_DRONES_AVAILABLE")
CHATBOT_TOPIC_DRONES_LOAD = os.getenv("CHATBOT_TOPIC_DRONES_LOAD")
CHATBOT_TOPIC_DRONES_MEDICATIONS = os.getenv("CHATBOT_TOPIC_DRONES_MEDICATIONS")
CHATBOT_TOPIC_DRONES_BATTERY = os.getenv("CHATBOT_TOPIC_DRONES_BATTERY")

# Topics de respuestas de la API
MQTT_TOPIC_DRONES_REGISTER_RESPONSE = os.getenv("MQTT_TOPIC_DRONES_REGISTER_RESPONSE")
MQTT_TOPIC_DRONES_AVAILABLE_RESPONSE = os.getenv("MQTT_TOPIC_DRONES_AVAILABLE_RESPONSE")
MQTT_TOPIC_DRONES_LOAD_RESPONSE = os.getenv("MQTT_TOPIC_DRONES_LOAD_RESPONSE")
MQTT_TOPIC_DRONES_MEDICATIONS_RESPONSE = os.getenv("MQTT_TOPIC_DRONES_MEDICATIONS_RESPONSE")
MQTT_TOPIC_DRONES_BATTERY_RESPONSE = os.getenv("MQTT_TOPIC_DRONES_BATTERY_RESPONSE")

# Topics de alertas de drones
MQTT_TOPIC_DRONES_ALERT_BATTERY_LOW = os.getenv("MQTT_TOPIC_DRONES_ALERT_BATTERY_LOW")
MQTT_TOPIC_DRONES_ALERT_STATE = os.getenv("MQTT_TOPIC_DRONES_ALERT_STATE")
MQTT_TOPIC_DRONES_ALERT_ERROR = os.getenv("MQTT_TOPIC_DRONES_ALERT_ERROR")

# Topic de salida del chatbot al usuario
CHATBOT_TOPIC_OUT = os.getenv("CHATBOT_TOPIC_OUT")


async def chatbot_mqtt():
    try:
        async with Client(MQTT_BROKER, port=MQTT_PORT) as client:
            # Suscribirse a comandos del chatbot
            await client.subscribe(CHATBOT_TOPIC_DRONES_REGISTER)
            await client.subscribe(CHATBOT_TOPIC_DRONES_AVAILABLE)
            await client.subscribe(CHATBOT_TOPIC_DRONES_LOAD)
            await client.subscribe(CHATBOT_TOPIC_DRONES_MEDICATIONS)
            await client.subscribe(CHATBOT_TOPIC_DRONES_BATTERY)

            # Suscribirse a respuestas de la API
            await client.subscribe(MQTT_TOPIC_DRONES_REGISTER_RESPONSE)
            await client.subscribe(MQTT_TOPIC_DRONES_AVAILABLE_RESPONSE)
            await client.subscribe(MQTT_TOPIC_DRONES_LOAD_RESPONSE)
            await client.subscribe(MQTT_TOPIC_DRONES_MEDICATIONS_RESPONSE)
            await client.subscribe(MQTT_TOPIC_DRONES_BATTERY_RESPONSE)

            # Suscribirse a alertas
            await client.subscribe(MQTT_TOPIC_DRONES_ALERT_BATTERY_LOW)
            await client.subscribe(MQTT_TOPIC_DRONES_ALERT_STATE)
            await client.subscribe(MQTT_TOPIC_DRONES_ALERT_ERROR)

            async with client.messages() as messages:
                async for message in messages:
                    topic = message.topic
                    payload = message.payload.decode()

                    # Procesar comandos
                    if topic in [
                        CHATBOT_TOPIC_DRONES_REGISTER,
                        CHATBOT_TOPIC_DRONES_AVAILABLE,
                        CHATBOT_TOPIC_DRONES_LOAD,
                        CHATBOT_TOPIC_DRONES_MEDICATIONS,
                        CHATBOT_TOPIC_DRONES_BATTERY,
                    ]:
                        await process_chat_message(client, message)

                    # Publicar respuestas al usuario
                    elif topic in [
                        MQTT_TOPIC_DRONES_REGISTER_RESPONSE,
                        MQTT_TOPIC_DRONES_AVAILABLE_RESPONSE,
                        MQTT_TOPIC_DRONES_LOAD_RESPONSE,
                        MQTT_TOPIC_DRONES_MEDICATIONS_RESPONSE,
                        MQTT_TOPIC_DRONES_BATTERY_RESPONSE,
                    ]:
                        await client.publish(CHATBOT_TOPIC_OUT, f"📊 {payload}")

                    # Publicar alertas al usuario
                    elif topic in [
                        MQTT_TOPIC_DRONES_ALERT_BATTERY_LOW,
                        MQTT_TOPIC_DRONES_ALERT_STATE,
                        MQTT_TOPIC_DRONES_ALERT_ERROR,
                    ]:
                        await client.publish(CHATBOT_TOPIC_OUT, f"⚠️ {payload}")

    except MqttError as e:
        print(f"MQTT chatbot error: {e}")
        await asyncio.sleep(5)
        asyncio.create_task(chatbot_mqtt())
 """