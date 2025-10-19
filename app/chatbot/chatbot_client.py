# yepcode_chatbot_with_gemini.py

import os
import json
import re
from google import genai
# Para cargar variables de entorno en desarrollo local, no necesario en YepCode
from dotenv import load_dotenv

import asyncio
from aiomqtt import Client

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

async def call_mqtt(parsed_json):
    """
    Publica el JSON en el topic MQTT configurado y retorna un mensaje de confirmación.
    """
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC = os.getenv("MQTT_TOPIC_UNICO", "chatbot/topic")

    try:
        async with Client(MQTT_BROKER, port=MQTT_PORT) as client:
            await client.publish(MQTT_TOPIC, json.dumps(parsed_json))
            print(f"✅ Publicado en MQTT: {MQTT_TOPIC} -> {parsed_json}")
        return "Mensaje publicado en MQTT correctamente."
    except Exception as e:
        print(f"Error publicando en MQTT: {e}")
        raise

class MQTTTimeoutError(Exception):
    """Excepción personalizada para timeout en escucha MQTT."""
    pass


async def listen_mqtt_response(timeout=10):
    """
    Escucha el topic MQTT configurado y devuelve el primer mensaje que tenga tipo 'respuesta'.
    Lanza MQTTTimeoutError si no se recibe ningún mensaje dentro del timeout.
    """
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC = os.getenv("MQTT_TOPIC_UNICO", "chatbot/topic")

    try:
        async with Client(MQTT_BROKER, port=MQTT_PORT) as client:
            await client.subscribe(MQTT_TOPIC)
            print(f"⏳ Esperando mensaje tipo 'respuesta' en {MQTT_TOPIC}...")

            start = asyncio.get_event_loop().time()
            async for msg in client.messages:
                payload = json.loads(msg.payload.decode())
                if payload.get("tipo") == "respuesta":
                    print(f"✅ Recibido mensaje respuesta: {payload}")
                    return payload

                # Comprobar timeout manualmente
                if asyncio.get_event_loop().time() - start > timeout:
                    raise MQTTTimeoutError("No se recibió ninguna respuesta de la BD dentro del tiempo de espera.")

    except MQTTTimeoutError:
        raise  # Re-lanzar la excepción para que se propague
    except Exception as e:
        print(f"Error escuchando MQTT: {e}")
        raise
    

async def process_message(message_text, sender_id="user_mqtt"):
    """
    Procesa un mensaje de texto y devuelve una respuesta, usando Gemini para lógica compleja
    y reglas predefinidas para comandos específicos de drones.
    """

    raw_response = get_gemini_response(message_text, get_context_1())
    match = re.search(r'```json\s*(\{.*\})\s*```', raw_response, re.DOTALL)
    print(f"Respuesta cruda de Gemini: {raw_response}")
    if match:
        # Si se encuentra un bloque ```json```, usamos solo el contenido capturado
        json_content = match.group(1)
    else:
        # Si no se encuentra el bloque de código, asumimos que es JSON directo
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
        mqtt_response = await call_mqtt(parsed_json)
        print(f"Respuesta de MQTT: {mqtt_response}")
        response = await listen_mqtt_response(timeout=15)
        raw_response = get_gemini_response(
            mqtt_response_to_llm_prompt(response, parsed_json.get("method"), user_question=message_text), get_context_2()
        )
        print(f"Respuesta final de Gemini tras MQTT: {raw_response}")
        return raw_response

    except Exception as e:
        print(f"Error al llamar a MQTT: {e}")
        return "Lo siento, ha fallado la llamada a la API."


PROMPT_TEMPLATES = {

    # === Endpoint: POST /drones ===
    "/drones": {
        "POST": {
            201: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 201 Created):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot para un sistema de despacho de drones. La solicitud del usuario para registrar un nuevo drone fue **exitosa** (código 201).

Genera una respuesta amigable que:
1.  Confirme que el drone se ha registrado correctamente.
2.  Presente un resumen claro de los detalles del drone registrado, extrayéndolos del JSON de contexto:
    * **Número de serie:** `serial_number`
    * **Modelo:** `model`
    * **Límite de peso:** `weight_limit` (asegúrate de incluir "gramos").
    * **Capacidad de batería:** `battery_capacity` (asegúrate de incluir "%").
    * **Estado inicial:** `state` (tradúcelo como "En espera" o "Listo").""",

            400: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 400 Bad Request):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. La solicitud del usuario para registrar un drone falló con un error 400 (Solicitud incorrecta).

Genera una respuesta clara que:
1.  Informe al usuario que **no se pudo registrar** el drone.
2.  Explique la razón del error de forma sencilla, basándote en el campo `message` del JSON de contexto. (Por ejemplo, si el mensaje dice "Serial number already exists", tradúcelo a "El número de serie proporcionado ya existe en el sistema.").""",

            422: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 422 Unprocessable Entity):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. La solicitud del usuario para registrar un drone falló con un error 422 (Error de validación) porque los datos enviados no eran correctos.

Genera una respuesta que:
1.  Informe al usuario que el registro falló debido a datos inválidos.
2.  Revise la lista `detail` en el JSON de contexto.
3.  Para cada error en la lista, crea un punto que explique qué campo estaba mal y por qué, de forma clara y legible.
    * Usa `loc` para identificar el campo (ej. `loc: ["body", "model"]` significa "el campo 'modelo'").
    * Usa `msg` para explicar el problema (ej. "Input should be 'Lightweight'..." significa "El modelo debe ser uno de los valores permitidos...")."""
        }
    },

    # === Endpoint: GET /drones/available ===
    "/drones/available": {
        "GET": {
            200: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 200 OK):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario preguntó por los drones disponibles para cargar. La API ha devuelto una lista (que puede estar vacía).

Genera una respuesta basada en el JSON de contexto:
1.  **Si la lista NO está vacía:**
    * Informa al usuario que se encontraron los siguientes drones disponibles (listos para cargar, con batería >25%).
    * Presenta una lista formateada de los drones. Para cada drone, incluye:
        * Número de serie (`serial_number`)
        * Modelo (`model`)
        * Límite de peso (`weight_limit` en gramos)
        * Nivel de batería (`battery_capacity` en %)
2.  **Si la lista ESTÁ vacía:**
    * Informa al usuario que, por el momento, no hay ningún drone disponible para iniciar una carga (probablemente porque están todos ocupados o con batería baja).""",

            500: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 500 Internal Server Error):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario preguntó por los drones disponibles, pero la API devolvió un error 500 (Error interno).

Genera una respuesta amigable que:
1.  Pida disculpas al usuario.
2.  Le informe que hubo un problema interno al intentar obtener la lista de drones.
3.  No muestres el mensaje de error técnico (`message` o `code`), simplemente informa del fallo.
4.  Sugiérele que lo intente de nuevo en unos momentos."""
        }
    },

    # === Endpoint: POST /drones/{serialNumber}/load ===
    "/drones/{serialNumber}/load": {
        "POST": {
            200: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 200 OK):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario intentó cargar medicamentos en un drone (S/N: {{serial_number_del_request}}) y la solicitud fue **exitosa** (código 200).

Genera una respuesta que:
1.  Confirme que los medicamentos se han cargado (o están en proceso de carga) en el drone {{serial_number_del_request}}.
2.  Indique claramente el **nuevo estado** del drone, basándote en el campo `state` del JSON de respuesta. (Ej. "LOADING" -> "Cargando", "LOADED" -> "Cargado y listo").""",

            400: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 400 Bad Request):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario intentó cargar medicamentos en un drone (S/N: {{serial_number_del_request}}), pero la solicitud falló con un error 400.

Genera una respuesta que:
1.  Informe al usuario que **no se pudieron cargar** los medicamentos en el drone {{serial_number_del_request}}.
2.  Explique la **razón específica** del fallo de forma muy clara, traduciendo el campo `message` del JSON.
    * Ej. "Total weight exceeds limit" -> "El peso total de los medicamentos supera el límite del drone."
    * Ej. "Battery level is too low" -> "La batería del drone está demasiado baja (menos del 25%) para esta operación."
    * Ej. "Drone is not in a loadable state" -> "El drone no se puede cargar en este momento (por ejemplo, está en reparto).""",

            404: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 404 Not Found):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario intentó realizar una operación (cargar medicamentos) en un drone (S/N: {{serial_number_del_request}}), pero la API devolvió un error 404.

Genera una respuesta que:
1.  Informe al usuario que la operación falló.
2.  Explique que no se pudo encontrar ningún drone con el número de serie: {{serial_number_del_request}}."""
        }
    },

    # === Endpoint: GET /drones/{serialNumber}/medications ===
    "/drones/{serialNumber}/medications": {
        "GET": {
            200: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 200 OK):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario preguntó por los medicamentos cargados en un drone (S/N: {{serial_number_del_request}}). La API ha devuelto una lista (que puede estar vacía).

Genera una respuesta basada en el JSON de contexto:
1.  **Si la lista NO está vacía:**
    * Informa al usuario que estos son los medicamentos cargados en el drone {{serial_number_del_request}}.
    * Presenta una lista formateada de los medicamentos. Para cada uno, incluye:
        * Nombre (`name`)
        * Código (`code`)
        * Peso (`weight` en gramos)
2.  **Si la lista ESTÁ vacía:**
    * Informa al usuario que el drone {{serial_number_del_request}} no tiene ningún medicamento cargado en este momento.""",

            404: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 404 Not Found):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario intentó consultar los medicamentos de un drone (S/N: {{serial_number_del_request}}), pero la API devolvió un error 404.

Genera una respuesta que:
1.  Informe al usuario que no se pudo obtener la información.
2.  Explique que no se pudo encontrar ningún drone con el número de serie: {{serial_number_del_request}}."""
        }
    },

    # === Endpoint: GET /drones/{serialNumber}/battery ===
    "/drones/{serialNumber}/battery": {
        "GET": {
            200: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 200 OK):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario preguntó por la batería de un drone (S/N: {{serial_number_del_request}}). La API respondió con éxito.

Genera una respuesta directa y clara que:
1.  Informe el nivel de batería exacto del drone {{serial_number_del_request}}, usando el valor `battery_capacity` del JSON.
2.  Asegúrate de incluir el símbolo de porcentaje (%).
    * Ejemplo: "El drone (S/N: {{serial_number_del_request}}) tiene un {{battery_capacity}}% de batería."
    """,

            404: """PREGUNTA DEL USUARIO:
"{{pregunta_usuario}}"

CONTEXTO (Respuesta de la API - 404 Not Found):
{{api_response_json}}

TAREA:
Actúa como un asistente de chatbot. El usuario intentó consultar la batería de un drone (S/N: {{serial_number_del_request}}), pero la API devolvió un error 404.

Genera una respuesta que:
1.  Informe al usuario que no se pudo obtener el nivel de batería.
2.  Explique que no se pudo encontrar ningún drone con el número de serie: {{serial_number_del_request}}."""
        }
    }
}



import json

def mqtt_response_to_llm_prompt(mqtt_payload: dict, method: str, user_question: str) -> str:
    """
    Convierte un mensaje recibido vía MQTT tipo 'respuesta' en el formato esperado por `get_llm_prompt`.
    
    mqtt_payload: dict con la estructura recibida de listen_mqtt_response().
    user_question: la pregunta original del usuario que generó la petición.
    """
    if mqtt_payload.get("tipo") != "respuesta":
        raise ValueError("El payload MQTT no es de tipo 'respuesta'")
    
    print(f"Procesando payload MQTT para LLM: {mqtt_payload}")

    payload = mqtt_payload.get("payload", {})
    endpoint = mqtt_payload.get("endpoint", "/unknown")
    method = method  # Puedes ajustar según tu estructura
    status_code = 200  # O asigna 201 por defecto si quieres
    
    # Convertimos el JSON de la respuesta a string
    api_response_json_str = json.dumps(payload, ensure_ascii=False)

    # No pasamos contexto extra aquí, lo dejamos como None
    return get_llm_prompt(
        endpoint_template=endpoint,
        method=method,
        status_code=status_code,
        user_question=user_question,
        api_response_json_str=api_response_json_str,
        request_context=None
    )



# --------------------------------------------------------------------------
# FUNCIÓN "SWITCH"
# --------------------------------------------------------------------------

def get_llm_prompt(
    endpoint_template: str,
    method: str,
    status_code: int,
    user_question: str,
    api_response_json_str: str,
    request_context: dict = None
) -> str:
    """
    Selecciona y formatea el prompt de LLM adecuado basándose en la
    ruta del endpoint, el método, el código de estado y el contexto.

    Args:
        endpoint_template: La plantilla de la ruta de la API (ej. "/drones/{serialNumber}/load").
        method: El método HTTP (ej. "POST", "GET").
        status_code: El código de estado de la respuesta (ej. 200, 404).
        user_question: La pregunta original del usuario.
        api_response_json_str: La respuesta JSON de la API como un string.
        request_context: Un diccionario con datos de la solicitud que sean
                         necesarios para el prompt (ej. {"serial_number_del_request": "DRN-001"}).

    Returns:
        El prompt listo para ser enviado al LLM.
    """

    # --- Prompt de Fallback ---
    # Se usa si no se encuentra una plantilla específica para la combinación
    FALLBACK_PROMPT = """PREGUNTA DEL USUARIO:
"{user_question}"

CONTEXTO (Respuesta de la API - {status_code}):
{api_response_json_str}

TAREA:
Actúa como un asistente de chatbot. Responde amigablemente a la pregunta del usuario basándote en la respuesta de la API. Si es un error, explícalo de forma sencilla.
"""

    # --- Lógica del "Switch" ---
    # Usamos .get() con diccionarios vacíos por defecto para evitar KeyErrors
    path_prompts = PROMPT_TEMPLATES.get(endpoint_template, {})
    print(f"--- {path_prompts} ---")
    method_prompts = path_prompts.get(method, {})
    print(f"--- {method_prompts} ---")
    template = method_prompts.get(status_code)

    if template is None:
        # No se encontró un template específico, usar el fallback
        print(f"--- (ADVERTENCIA: Usando prompt de fallback para {method} {endpoint_template} {status_code}) ---")
        # Este prompt de fallback usa .format()
        return FALLBACK_PROMPT.format(
            user_question=user_question,
            status_code=status_code,
            api_response_json_str=api_response_json_str
        )

    # --- Rellenar placeholders del template encontrado ---

    # 1. Rellenar placeholders básicos
    prompt = template.replace("{{pregunta_usuario}}", user_question)
    prompt = prompt.replace("{{api_response_json}}", api_response_json_str)

    # 2. Rellenar placeholders de contexto dinámico (ej. serial_number)
    #    Estos son los placeholders que definimos en los prompts,
    #    como {{serial_number_del_request}}
    if request_context:
        for key, value in request_context.items():
            placeholder = "{{" + key + "}}"
            prompt = prompt.replace(placeholder, str(value))

    return prompt






























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