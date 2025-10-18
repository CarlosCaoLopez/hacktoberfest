# app/chatbot/chatbot_logic.py
from app.core.config import settings

async def process_chat_message(client, message):
    text = message.payload.decode().lower()
    print(f"🗣️ Usuario dijo: {text}")

    # Interpretar comandos del usuario
    if "batería" in text:
        # Ejemplo: "batería del dron 100"
        parts = text.split()
        try:
            drone_id = next(p for p in parts if p.isdigit())
            topic = f"chatbot/drone/check_battery/{drone_id}"
            await client.publish(topic, "")
            await client.publish(settings.CHATBOT_TOPIC_OUT, f"⏳ Consultando batería del dron {drone_id}...")
        except StopIteration:
            await client.publish(settings.CHATBOT_TOPIC_OUT, "❌ No pude identificar el número del dron.")

    elif "cargar" in text or "carga" in text:
        # Ejemplo: "cargar dron 100 con medicina A"
        try:
            parts = text.split()
            drone_id = next(p for p in parts if p.isdigit())
            item = text.split("con")[-1].strip()
            payload = f"{drone_id},{item}"
            await client.publish(settings.MQTT_TOPIC_COMMAND, payload)
            await client.publish(settings.CHATBOT_TOPIC_OUT, f"🚀 Enviando comando de carga al dron {drone_id}...")
        except Exception:
            await client.publish(settings.CHATBOT_TOPIC_OUT, "❌ Formato inválido para cargar el dron.")

    else:
        await client.publish(settings.CHATBOT_TOPIC_OUT, "🤖 No entendí el comando. Prueba con 'batería del dron 100'.")
