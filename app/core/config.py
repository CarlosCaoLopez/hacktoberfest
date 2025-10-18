# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Drone Control System"
    VERSION: str = "0.2.0"

    MQTT_BROKER: str = "broker.hivemq.com"
    MQTT_PORT: int = 1883

    # Topics de la API
    MQTT_TOPIC_COMMAND: str = "chatbot/drone/command"
    MQTT_TOPIC_BATTERY: str = "chatbot/drone/check_battery/+"
    MQTT_TOPIC_ALERT: str = "drone/alerta/bateria_baja"
    MQTT_TOPIC_RESPONSE: str = "chatbot/drone/battery_response"

    # Topics del Chatbot
    CHATBOT_TOPIC_IN: str = "chatbot/input"
    CHATBOT_TOPIC_OUT: str = "chatbot/output"

    class Config:
        env_file = ".env"

settings = Settings()
