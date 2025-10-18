# yepcode_chatbot_with_gemini.py

import os
import json
import re
from google import genai
# Para cargar variables de entorno en desarrollo local, no necesario en YepCode
from dotenv import load_dotenv
# Los imports propios no van bien con YepCode
#from context_info import get_context_1
def get_context_1():
    return """
    Eres un asistente de chatbot especializado en la gestión y operación de una flota de drones para entrega de medicamentos.
    Tu principal tarea es responder a las preguntas de los usuarios y facilitar la interacción con los drones llamando a la API cuando se necesario,
    proporcionando información precisa.

    **Instrucciones Clave:**
    1.  **Prioriza la información proporcionada aquí.**
    2.  **Sé conciso, directo y útil.**
    3.  **Para comandos específicos de drones**, yo (el sistema principal) gestionaré la ejecución, pero tú puedes confirmar la recepción del comando de forma amigable y, si es posible, ofrecer contexto relevante.
    4.  **No permitas acciones que violen las restricciones.** Si una pregunta o comando va en contra de las reglas, debes indicar la restricción.
    5.  **Si no tienes suficiente información para responder**, indícalo educadamente.

    **Detalles y Restricciones de Nuestra Flota de Drones:**

    *   **Propósito:** Entrega de pequeños artículos (medicamentos urgentes) en lugares de difícil acceso.
    *   **Flota:** 10 drones.
    *   **Carga Útil:** Medicamentos.
    *   **Atributos clave de un Drone:**
        *   **Modelo:** (Ligero, Peso medio, Cruiser, Peso pesado).
        *   **Límite de Peso (Carga):** Máximo 500 gramos.
        *   **Capacidad de Batería:** Porcentaje.
        *   **Estado:** IDLE, LOADING, LOADED, DELIVERING, DELIVERED, RETURNING.
    *   **Restricciones Operativas Clave:**
        *   **Prohibición de Sobrecarga:** Un drone NO puede ser cargado con más de 500 gramos.
        *   **Restricción de Batería para Carga:** Un drone NO puede entrar en estado 'LOADING' si su nivel de batería es INFERIOR al 25%.

    **Instrucciones para generar la SALIDA JSON:**
    1. Siempre se devuelve un JSON con cuatro campos: "tipo", "method", "endpoint", "payload"
    2. En caso de que el usuario realice una pregunta genérica, que no implique una llamada a la API, el campo "tipo" debe ser "respuesta". Los campos
    "method" y "endpoint" serán vacíos. El campo "payload" contiene la respuesta a la pregunta del usuario.
    3. En caso de que el usuario quiera realizar una consulta a la API, el campo "tipo" debe ser "pregunta". El resto de campos deben rellenarse en función
    de las instrucciones proporcionadas por la documentación de la API. El campo "method" es la forma de envío, y puede ser "GET" o "POST". El campo
    "endpoint" es la propia llamada. El campo "payload" es un JSON que contiene lo que espera esa llamada a la API.
    4. La documentación de la API es:

openapi: 3.0.3
info:
  title: Drones Dispatch API
  description: |-
    API REST para la comunicación con un controlador de despacho de drones.
    Permite registrar drones, cargarlos con medicamentos y monitorear su estado.
  version: 1.0.0
servers:
  - url: /api/v1
    description: Servidor principal

tags:
  - name: Drones
    description: Operaciones relacionadas con la gestión y monitoreo de drones.
  - name: Medications
    description: Operaciones relacionadas con la carga de medicamentos.

paths:
  /drones:
    post:
      tags:
        - Drones
      summary: Registrar un nuevo drone
      description: |-
        Añade un nuevo drone a la flota del sistema.
        El cliente proporciona todos los campos requeridos y el estado
        inicial del drone se establecerá automáticamente en 'IDLE'.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/DroneRegistration"
      responses:
        "201":
          description: Drone registrado exitosamente. Retorna el objeto completo del drone creado (incluyendo el estado 'IDLE').
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Drone"
        "400":
          description: Datos de entrada inválidos (e.g., serial duplicado).
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
        "422":
          description: Error de validación de datos (e.g., modelo inválido, campos faltantes o con formato incorrecto).
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ValidationError"

  /drones/available:
    get:
      tags:
        - Drones
      summary: Verificar drones disponibles para carga
      description: |-
        Obtiene una lista de todos los drones que están actualmente en estado 'IDLE'
        y tienen un nivel de batería suficiente (>= 25%) para iniciar una carga.
      responses:
        "200":
          description: Una lista de drones disponibles.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Drone"
        "500":
          description: Error interno del servidor.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"

  /drones/{serialNumber}/load:
    post:
      tags:
        - Medications
      summary: Cargar un drone con medicamentos
      description: |-
        Carga uno o más ítems de medicación en un drone específico.
        El servicio debe validar:
        1. Que el peso total no exceda el límite del drone.
        2. Que la batería del drone sea >= 25%.
        3. Que el drone esté en estado 'IDLE' o 'LOADING'.
      parameters:
        - name: serialNumber
          in: path
          required: true
          description: El número de serie del drone a cargar.
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: "#/components/schemas/Medication"
              description: Lista de medicamentos a cargar.
      responses:
        "200":
          description: Medicamentos cargados exitosamente. El drone pasa a estado 'LOADING' o 'LOADED'.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Drone"
        "400":
          description: |-
            Solicitud inválida. Razones posibles:
            - El peso total excede el límite del drone.
            - El nivel de batería es < 25%.
            - El drone no está en un estado que permita la carga (e.g., 'DELIVERING').
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
        "404":
          description: Drone no encontrado.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"

  /drones/{serialNumber}/medications:
    get:
      tags:
        - Medications
      summary: Verificar medicamentos cargados en un drone
      description: Obtiene la lista de todos los ítems de medicación cargados en un drone específico.
      parameters:
        - name: serialNumber
          in: path
          required: true
          description: El número de serie del drone.
          schema:
            type: string
      responses:
        "200":
          description: Lista de medicamentos cargados.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Medication"
        "404":
          description: Drone no encontrado.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"

  /drones/{serialNumber}/battery:
    get:
      tags:
        - Drones
      summary: Verificar nivel de batería de un drone
      description: Obtiene el nivel de batería actual (en porcentaje) de un drone específico.
      parameters:
        - name: serialNumber
          in: path
          required: true
          description: El número de serie del drone.
          schema:
            type: string
      responses:
        "200":
          description: Nivel de batería del drone.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/BatteryLevel"
        "404":
          description: Drone no encontrado.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"

components:
  schemas:
    DroneRegistration:
      description: Objeto para registrar un nuevo drone. El estado 'IDLE' se asignará automáticamente en el servidor.
      type: object
      properties:
        serial_number:
          type: string
          maxLength: 100
          description: Número de serie del drone.
        model:
          $ref: "#/components/schemas/DroneModel"
        weight_limit:
          type: number
          format: double
          description: Límite de peso en gramos.
          maximum: 500
          minimum: 0
        battery_capacity:
          type: integer
          format: int32
          description: Capacidad de batería en porcentaje.
          minimum: 0
          maximum: 100
      required:
        - serial_number
        - model
        - weight_limit
        - battery_capacity

    Drone:
      description: Representa un drone en la flota.
      type: object
      properties:
        serial_number:
          type: string
          maxLength: 100
          description: Número de serie del drone.
        model:
          $ref: "#/components/schemas/DroneModel"
        weight_limit:
          type: number
          format: double
          description: Límite de peso en gramos.
          maximum: 500
          minimum: 0
        battery_capacity:
          type: integer
          format: int32
          description: Capacidad de batería en porcentaje.
          minimum: 0
          maximum: 100
        state:
          $ref: "#/components/schemas/DroneState"
      required:
        - serial_number
        - model
        - weight_limit
        - battery_capacity
        - state

    Medication:
      description: Representa un ítem de medicación.
      type: object
      properties:
        name:
          type: string
          description: Nombre del medicamento.
          pattern: "^[a-zA-Z0-9_-]+$"
        weight:
          type: number
          format: double
          description: Peso del medicamento en gramos.
          minimum: 0.01
        code:
          type: string
          description: Código del medicamento.
          pattern: "^[A-Z0-9_]+$"
        image:
          type: string
          format: uri
          description: URL a una imagen del medicamento.
      required:
        - name
        - weight
        - code
        - image

    DroneModel:
      type: string
      description: Modelo del drone.
      enum:
        - Lightweight
        - Middleweight
        - Cruiserweight
        - Heavyweight

    DroneState:
      type: string
      description: Estado actual del drone.
      enum:
        - IDLE
        - LOADING
        - LOADED
        - DELIVERING
        - DELIVERED
        - RETURNING

    BatteryLevel:
      type: object
      description: Un objeto que reporta específicamente el nivel de batería.
      properties:
        battery_capacity:
          type: integer
          format: int32
          description: Capacidad de batería en porcentaje.
          minimum: 0
          maximum: 100
      required:
        - battery_capacity

    Error:
      type: object
      properties:
        code:
          type: string
          description: Un código de error interno.
        message:
          type: string
          description: Un mensaje descriptivo del error.
      required:
        - code
        - message

    ValidationError:
      type: object
      description: Error de validación estándar de FastAPI/Pydantic
      properties:
        detail:
          type: array
          items:
            type: object
            properties:
              type:
                type: string
                description: Tipo específico de error de validación (e.g., 'enum', 'missing', 'string_type')
                example: "enum"
              loc:
                type: array
                items:
                  oneOf:
                    - type: string
                    - type: integer
                description: Ruta al campo que causó el error (e.g., ['body', 'model'])
                example: ["body", "model"]
              msg:
                type: string
                description: Mensaje descriptivo del error legible por humanos
                example: "Input should be 'Lightweight', 'Middleweight', 'Cruiserweight' or 'Heavyweight'"
              input:
                description: Valor exacto que causó el error
                example: "NotAModel"
              ctx:
                type: object
                description: Contexto adicional específico del tipo de error
                example:
                  expected: "'Lightweight', 'Middleweight', 'Cruiserweight' or 'Heavyweight'"
            required:
              - type
              - loc
              - msg
              - input
      required:
        - detail
    """
















# --- Configuración (en YepCode, esto se maneja vía Secrets/Environment Variables) ---
load_dotenv()

# Obtener la API Key de las variables de entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("La API Key de Gemini no está configurada.")

client = genai.Client(api_key=GEMINI_API_KEY)





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
        # Si no se encuentra el bloque de código, asumimos que es JSON directo
        json_content = json_string

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
        # "payload": "Hola, ¿cómo estás?"
        # "payload": "qué es un dron?"
        "payload": "¿Cuál es el peso máximo que puede llevar un dron?"
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