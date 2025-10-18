# app/chatbot/chatbot_client.py
import asyncio
from asyncio_mqtt import Client, MqttError
from app.core.config import settings
from app.chatbot.chatbot_logic import process_chat_message

async def chatbot_mqtt():
    try:
        async with Client(settings.MQTT_BROKER, port=settings.MQTT_PORT) as client:
            await client.subscribe(settings.CHATBOT_TOPIC_IN)
            await client.subscribe(settings.MQTT_TOPIC_RESPONSE)
            await client.subscribe(settings.MQTT_TOPIC_ALERT)

            async with client.unfiltered_messages() as messages:
                async for message in messages:
                    topic = message.topic
                    if topic == settings.CHATBOT_TOPIC_IN:
                        await process_chat_message(client, message)
                    elif topic == settings.MQTT_TOPIC_RESPONSE:
                        await client.publish(settings.CHATBOT_TOPIC_OUT, f"📊 {message.payload.decode()}")
                    elif topic == settings.MQTT_TOPIC_ALERT:
                        await client.publish(settings.CHATBOT_TOPIC_OUT, f"⚠️ {message.payload.decode()}")
    except MqttError as e:
        print(f"MQTT chatbot error: {e}")
        await asyncio.sleep(5)
        asyncio.create_task(chatbot_mqtt())
