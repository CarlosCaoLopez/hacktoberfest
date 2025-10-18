#!/bin/bash
#
# Script de prueba de integración para la API de Drones Dispatch.
#
# Uso:
# 1. Asegúrate de que el servidor de la API esté corriendo.
# 2. Actualiza la variable 'BASE_URL' si es necesario.
# 3. Ejecuta: chmod +x test_drones_api.sh
# 4. Ejecuta: ./test_drones_api.sh
#

# --- Configuración ---

# ¡IMPORTANTE! Actualiza esto a la URL base de tu servidor (sin /api/v1)
SERVER_URL="http://localhost:8000"
BASE_URL="${SERVER_URL}/api/v1"

# Genera un número de serie único para esta ejecución de prueba
# Usamos $RANDOM para simplicidad, en un entorno CI se usaría algo más robusto (ej. build ID)
DRONE_SN="DRONE-TEST-${RANDOM}"
DRONE_SN_404="DRONE-NOT-FOUND"

# Contadores de estado
PASS_COUNT=0
FAIL_COUNT=0

# --- Colores para la Salida ---
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

# --- Función de Ayuda para Pruebas ---

#
# Ejecuta una prueba de endpoint y reporta el resultado.
#
# $1: Descripción de la prueba (string)
# $2: Método HTTP (e.g., "GET", "POST")
# $3: Endpoint (e.g., "/drones")
# $4: Código de estado HTTP esperado (e.g., 200, 201, 400)
# $5: Payload/Body (string JSON, opcional)
#
run_test() {
    local description="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local payload="$5"

    echo -e "\n---"
    echo -e "${YELLOW}TEST:${RESET} $description"
    echo -e "► ${method} ${BASE_URL}${endpoint} (Espera ${expected_status})"

    local body_file
    body_file=$(mktemp) # Archivo temporal para el cuerpo de la respuesta

    local curl_args=(
        -s -L                 # Silencioso, seguir redirecciones
        -X "$method"          # Método HTTP
        -w "%{http_code}"     # Escribir código HTTP al final
        -o "$body_file"       # Guardar cuerpo de respuesta en archivo
        --connect-timeout 5   # Timeout de conexión
    )

    if [[ -n "$payload" ]]; then
        curl_args+=(-H "Content-Type: application/json" -d "$payload")
    fi

    # Ejecutar cURL
    local http_status
    http_status=$(curl "${curl_args[@]}" "${BASE_URL}${endpoint}")
    local http_body
    http_body=$(cat "$body_file")
    rm "$body_file"

    # Verificar el resultado
    if [[ "$http_status" -eq "$expected_status" ]]; then
        echo -e "${GREEN}PASS:${RESET} Código de estado recibido ${http_status}."
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}FAIL:${RESET} Se esperaba ${expected_status} pero se recibió ${http_status}."
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    # Imprimir el cuerpo de la respuesta (formateado si es JSON)
    if [[ -n "$http_body" ]]; then
        echo "Respuesta:"
        echo "$http_body" | jq . 2>/dev/null || echo "$http_body"
    else
        echo "Respuesta: (Vacía)"
    fi
}

# --- Definición de Payloads ---

# Payload para registrar un drone (éxito)
# Drone con batería alta (90%) y límite de peso de 300g
DRONE_REG_PAYLOAD=$(jq -c . <<EOF
{
  "serial_number": "${DRONE_SN}",
  "model": "Middleweight",
  "weight_limit": 300.0,
  "battery_capacity": 90
}
EOF
)

# Payload para registrar un drone (fallo - datos inválidos)
# Modelo inválido
DRONE_REG_INVALID_PAYLOAD=$(jq -c . <<EOF
{
  "serial_number": "INVALID-DRONE-MODEL",
  "model": "NotAModel",
  "weight_limit": 100.0,
  "battery_capacity": 100
}
EOF
)

# Payload de medicación (éxito)
# Peso total: 150g (dentro del límite de 300g)
MEDS_PAYLOAD_OK=$(jq -c . <<EOF
[
  {
    "name": "Ibuprofen-X",
    "weight": 50.5,
    "code": "IBU_X_50MG",
    "image": "https://example.com/images/ibu.png"
  },
  {
    "name": "Paracetamol-Z",
    "weight": 99.5,
    "code": "PARA_Z_100MG",
    "image": "https://example.com/images/para.png"
  }
]
EOF
)

# Payload de medicación (fallo - sobrepeso)
# Peso total: 400g (excede el límite de 300g)
MEDS_PAYLOAD_OVERWEIGHT=$(jq -c . <<EOF
[
  {
    "name": "Heavy-Pills",
    "weight": 250.0,
    "code": "HEAVY_250",
    "image": "https://example.com/images/heavy.png"
  },
  {
    "name": "Dense-Syrup",
    "weight": 150.0,
    "code": "DENSE_150",
    "image": "https://example.com/images/dense.png"
  }
]
EOF
)


# --- Inicio de las Pruebas ---

echo "========================================="
echo "Iniciando Pruebas de API Drones Dispatch"
echo "Servidor: ${SERVER_URL}"
echo "========================================="

# --- Flujo de Pruebas ---

# 1. Probar registrar un drone (Fallo 422 - Modelo Inválido)
run_test "Registrar drone con modelo inválido (Espera 422)" \
    "POST" "/drones" 422 "$DRONE_REG_INVALID_PAYLOAD"

# 2. Registrar nuestro drone de prueba (Éxito 201)
run_test "Registrar un nuevo drone (Espera 201)" \
    "POST" "/drones" 201 "$DRONE_REG_PAYLOAD"

# 3. Probar registrar el MISMO drone (Fallo 400 - Duplicado)
run_test "Registrar drone duplicado (Espera 400)" \
    "POST" "/drones" 400 "$DRONE_REG_PAYLOAD"

# 4. Consultar medicamentos (debería estar vacío) (Éxito 200)
run_test "Consultar medicamentos del drone (vacío) (Espera 200)" \
    "GET" "/drones/${DRONE_SN}/medications" 200

# 5. Consultar batería del drone (Éxito 200)
run_test "Consultar batería del drone (Espera 200)" \
    "GET" "/drones/${DRONE_SN}/battery" 200

# 6. Consultar drones disponibles (nuestro drone debería estar) (Éxito 200)
run_test "Consultar drones disponibles (Espera 200)" \
    "GET" "/drones/available" 200

# 7. Cargar drone (Fallo 400 - Sobrepeso)
run_test "Cargar drone (Fallo - Sobrepeso) (Espera 400)" \
    "POST" "/drones/${DRONE_SN}/load" 400 "$MEDS_PAYLOAD_OVERWEIGHT"

# 8. Cargar drone (Éxito 200)
run_test "Cargar drone (Éxito) (Espera 200)" \
    "POST" "/drones/${DRONE_SN}/load" 200 "$MEDS_PAYLOAD_OK"

# 9. Consultar medicamentos (ahora debería tener ítems) (Éxito 200)
run_test "Consultar medicamentos del drone (cargado) (Espera 200)" \
    "GET" "/drones/${DRONE_SN}/medications" 200

# 10. Pruebas de 404 (Not Found)
run_test "Consultar batería (Fallo - No existe) (Espera 404)" \
    "GET" "/drones/${DRONE_SN_404}/battery" 404

run_test "Consultar medicamentos (Fallo - No existe) (Espera 404)" \
    "GET" "/drones/${DRONE_SN_404}/medications" 404

run_test "Cargar drone (Fallo - No existe) (Espera 404)" \
    "POST" "/drones/${DRONE_SN_404}/load" 404 "$MEDS_PAYLOAD_OK"


# --- Resumen Final ---

echo -e "\n========================================="
echo "Resumen de Pruebas"
echo "========================================="
echo -e "${GREEN}Pruebas Pasadas: ${PASS_COUNT}${RESET}"
echo -e "${RED}Pruebas Fallidas: ${FAIL_COUNT}${RESET}"

# Salir con un código de error si alguna prueba falló
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}Algunas pruebas fallaron.${RESET}"
    exit 1
else
    echo -e "${GREEN}¡Todas las pruebas pasaron!${RESET}"
    exit 0
fi