# app/mqtt/handlers.py
from app.chatbot.chatbot_logic import process_chat_message

# ----------------------
# Comandos publicados por el chatbot → Backend/REST
# ----------------------
async def handle_command(client, topic, payload):
    # Aquí llamamos a la lógica del chatbot para procesar comandos
    await process_chat_message(client, topic, payload)

# ----------------------
# Respuestas de la API → Chatbot
# ----------------------
async def handle_response(client, topic, payload, out_topic):
    await client.publish(out_topic, f"📊 {payload}")

# ----------------------
# Alertas de drones → Chatbot
# ----------------------
async def handle_alert(client, topic, payload, out_topic):
    await client.publish(out_topic, f"⚠️ {payload}")
