# yepcode_chatbot_with_gemini.py
import os
import json
import re
from google import genai
# Para cargar variables de entorno en desarrollo local, no necesario en YepCode
from dotenv import load_dotenv

import asyncio
from aiomqtt import Client

# --- Configuración (en YepCode, esto se maneja vía Secrets/Environment Variables) ---
load_dotenv()

# Obtener la API Key de las variables de entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("La API Key de Gemini no está configurada.")

client = genai.Client(api_key=GEMINI_API_KEY)

# Obtener archivos de contexto de entrada y salida para Gemini    
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
    Envía un prompt a la API de Gemini y devuelve la respuesta. Parte prompt e información de contexto.
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
    method = method
    status_code = 200  # 
    
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



