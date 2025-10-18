# app/core/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_battery_monitor_logger():
    """
    Configura el logger específico para el monitor de batería de drones.
    Los logs se guardan en logs/battery_monitor.log con rotación automática.
    """
    logger = logging.getLogger('battery_monitor')
    logger.setLevel(logging.INFO)

    # Evitar duplicar handlers si ya está configurado
    if logger.handlers:
        return logger

    # Crear el directorio de logs si no existe
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configurar el handler para archivo con rotación
    log_file = os.path.join(log_dir, "battery_monitor.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )

    # Formato para los logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Agregar handler al logger
    logger.addHandler(file_handler)

    return logger

# Instancia global del logger para el monitor de batería
battery_logger = setup_battery_monitor_logger()