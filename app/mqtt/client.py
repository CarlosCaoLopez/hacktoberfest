""" # app/mqtt/client.py
import os
import asyncio
from aiomqtt import Client, MqttError
from dotenv import load_dotenv
from app.mqtt.handlers import handle_command, handle_response, handle_alert

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
CHATBOT_TOPIC_OUT = os.getenv("CHATBOT_TOPIC_OUT")

# Topics de comandos del chatbot
COMMAND_TOPICS = [
    os.getenv("CHATBOT_TOPIC_DRONES_REGISTER"),
    os.getenv("CHATBOT_TOPIC_DRONES_AVAILABLE"),
    os.getenv("CHATBOT_TOPIC_DRONES_LOAD"),
    os.getenv("CHATBOT_TOPIC_DRONES_MEDICATIONS"),
    os.getenv("CHATBOT_TOPIC_DRONES_BATTERY"),
]

# Topics de respuestas de la API
RESPONSE_TOPICS = [
    os.getenv("MQTT_TOPIC_DRONES_REGISTER_RESPONSE"),
    os.getenv("MQTT_TOPIC_DRONES_AVAILABLE_RESPONSE"),
    os.getenv("MQTT_TOPIC_DRONES_LOAD_RESPONSE"),
    os.getenv("MQTT_TOPIC_DRONES_MEDICATIONS_RESPONSE"),
    os.getenv("MQTT_TOPIC_DRONES_BATTERY_RESPONSE"),
]

# Topics de alertas de drones
ALERT_TOPICS = [
    os.getenv("MQTT_TOPIC_DRONES_ALERT_BATTERY_LOW"),
    os.getenv("MQTT_TOPIC_DRONES_ALERT_STATE"),
    os.getenv("MQTT_TOPIC_DRONES_ALERT_ERROR"),
]


async def mqtt_client():
    try:
        async with Client(MQTT_BROKER, port=MQTT_PORT) as client:
            # Suscribirse a todos los topics
            for t in COMMAND_TOPICS + RESPONSE_TOPICS + ALERT_TOPICS:
                await client.subscribe(t)

            async with client.messages() as messages:
                async for message in messages:
                    topic = message.topic
                    payload = message.payload.decode()

                    # Dispatch según tipo de topic
                    if topic in COMMAND_TOPICS:
                        await handle_command(client, topic, payload)
                    elif topic in RESPONSE_TOPICS:
                        await handle_response(client, topic, payload, CHATBOT_TOPIC_OUT)
                    elif topic in ALERT_TOPICS:
                        await handle_alert(client, topic, payload, CHATBOT_TOPIC_OUT)

    except MqttError as e:
        print(f"MQTT client error: {e}")
        await asyncio.sleep(5)
        asyncio.create_task(mqtt_client())
 """