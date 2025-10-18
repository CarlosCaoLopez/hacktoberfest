# yepcode_chatbot_with_gemini.py

import os
import json
import re
from google import genai
# Para cargar variables de entorno en desarrollo local, no necesario en YepCode
from dotenv import load_dotenv
# Los imports propios no van bien con YepCode
#from context_info import get_context_1


# --- Configuración (en YepCode, esto se maneja vía Secrets/Environment Variables) ---
load_dotenv()

# Obtener la API Key de las variables de entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("La API Key de Gemini no está configurada.")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_context_1():
    script_dir = os.path.dirname(__file__) # Esto será el directorio de 'module_que_contiene_get_context_1.py'
    file_path = os.path.join(script_dir, 'context_1.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no se encontró.")
        return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None

def get_context_2():
    script_dir = os.path.dirname(__file__) # Esto será el directorio de 'module_que_contiene_get_context_1.py'
    file_path = os.path.join(script_dir, 'context_2.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no se encontró.")
        return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None


def get_gemini_response(prompt_text, context):
    """
    Envía un prompt a la API de Gemini y devuelve la respuesta.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text,
            config=genai.types.GenerateContentConfig(
                temperature = 0.5,
                max_output_tokens = 500,
                system_instruction = context,
            )
        )
        return response.text
    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return "Lo siento, tengo problemas para contactar con la IA en este momento."

def call_mqtt(parsed_json):
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC = os.getenv("MQTT_TOPIC_UNICO", "chatbot/topic")

def process_message(message_text, sender_id="user_mqtt"):
    """
    Procesa un mensaje de texto y devuelve una respuesta, usando Gemini para lógica compleja
    y reglas predefinidas para comandos específicos de drones.
    """

    raw_response = get_gemini_response(message_text, get_context_1())
    match = re.search(r'```json\s*(\{.*\})\s*```', raw_response, re.DOTALL)
    if match:
        # Si se encuentra un bloque ```json```, usamos solo el contenido capturado
        json_content = match.group(1)
    else:
        # Si no se encuentra el bloque de código, se devuelve directamente la respuesta
        return raw_response

    try:
        parsed_json = json.loads(json_content)
    except json.JSONDecodeError as e:
        print(f"Error al parsear JSON de Gemini: {e}")
        print(f"Texto que intentó parsear: {raw_response}")
        return "Lo siento, la IA no pudo generar una respuesta estructurada correctamente. Por favor, reformula tu pregunta."

    if parsed_json["tipo"] == "respuesta":
        return parsed_json["payload"]

    print(f"La IA necesita consultar la API. Publicando en MQTT...")
    try:
        mqtt_response = call_mqtt(parsed_json)
        raw_response = get_gemini_response(message_text, get_context_2())

    except Exception as e:
        print(f"Error al llamar a MQTT: {e}")
        return "Lo siento, ha fallado la llamada a la API."







    try:
        # Reemplaza 'mqtt_chatbot_responses' con el nombre de tu conector MQTT en YepCode
        yepcode.connectors.get('mqtt_chatbot_responses').publish(
            topic=output_topic,
            payload=json.dumps({"text": response_text, "original_request_topic": message_topic, "sender_id": sender_id})
        )
        print(f"Respuesta publicada en {output_topic} para {sender_id}: {response_text[:50]}...")
    except Exception as e:
        print(f"Error al publicar respuesta MQTT: {e}")

    return response










# --- Simulación de la ejecución en YepCode ---
# En YepCode, el 'context' es un diccionario que contiene la entrada del trigger.
# Por ejemplo, si un trigger MQTT envía el payload como JSON:
# { "topic": "chatbot/inbox", "payload": "Hola, ¿cómo estás?" }

simulated_context = {
    "event": {
        "topic": "chatbot/inbox",
        # Prueba diferentes mensajes aquí:
        #"payload": "Hola, ¿cómo estás?"
        "payload": "¿Cuál es la altura de los drones?"
        #"payload": "¿Cuál es el peso máximo que puede llevar un dron?"
        # "payload": "drone 1 despegar"
        # "payload": "Dime algo interesante sobre volar"
    }
}

# Extraer el mensaje del contexto (adaptar según cómo YepCode inyecte el payload del MQTT)
message_from_mqtt = simulated_context["event"]["payload"]
sender_identifier = simulated_context["event"].get("sender", "user_mqtt_default")

# Procesar el mensaje
print(f"Mensaje de entrada: '{message_from_mqtt}'")
chatbot_response = process_message(message_from_mqtt, sender_identifier)
print(f"Respuesta del Chatbot: '{chatbot_response}'")

# Si YepCode espera un retorno estructurado, podrías devolver un JSON
# return json.dumps({"response": chatbot_response, "target_topic": "chatbot/outbox"})




























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