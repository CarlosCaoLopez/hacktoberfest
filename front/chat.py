import streamlit as st
import requests
import time

# Configuración de la API
CHAT_API = "http://127.0.0.1:8000"  # Reemplaza con tu URL real

# Inicializar el historial de chat en session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Título de la aplicación
st.title("💬 MedicAir")
st.subheader("Asistente de despacho de drones para medicación")

# Mostrar historial de mensajes
for message in st.session_state.messages:
    # Usar nombre "MedicAir" para mensajes del asistente
    role = message["role"]
    with st.chat_message(role, avatar="🚁" if role == "assistant" else None):
        st.markdown(message["content"])

# Input del usuario
if prompt := st.chat_input("Escribe aquí a túa mensaxe..."):
    # Agregar mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Enviar mensaje a la API y obtener respuesta
    with st.chat_message("assistant", avatar="🚁"):
        message_placeholder = st.empty()
        
        try:
            # Enviar mensaje a la API
            import requests

            response = requests.post(
                f"{CHAT_API}/send",
                json={
                    "message": prompt,
                    "sender_identifier": "user_mqtt_default"
                },
                headers={
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            if response.status_code == 200:
                # Obtener respuesta de la API
                bot_response = response.json().get("response", "Sin respuesta")
                message_placeholder.markdown(f"**MedicAir:** {bot_response}")
                
                # Agregar respuesta al historial
                st.session_state.messages.append({"role": "assistant", "content": f"**MedicAir:** {bot_response}"})
            else:
                error_msg = f"**MedicAir:** Error: {response.status_code}"
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
        except requests.exceptions.RequestException as e:
            error_msg = f"**MedicAir:** Error de conexión: {str(e)}"
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Botón para limpiar el chat
if st.button("🗑️ Limpar chat"):
    st.session_state.messages = []
    st.rerun()