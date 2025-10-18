# app/services/battery_monitor.py
import asyncio
from typing import Optional
from app.models.drone import Drone, DroneState
from app.core.logger import battery_logger


class BatteryMonitor:
    """
    Monitor de batería que verifica periódicamente el estado de los drones
    y actualiza aquellos con batería baja (<25%) en estado LOADING a RETURNING.
    """

    def __init__(self):
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.interval_seconds = 30

    async def check_battery_levels(self):
        """
        Verifica los niveles de batería de todos los drones y actualiza
        el estado de aquellos con batería baja en estado LOADING.
        """
        try:
            battery_logger.info("Iniciando verificación de niveles de batería")

            # Obtener TODOS los drones para logging completo
            all_drones = await Drone.find_all().to_list()

            if not all_drones:
                battery_logger.info("No se encontraron drones en la base de datos")
                return

            # Log del estado de todos los drones
            battery_logger.info(f"=== REPORTE DE BATERÍA - {len(all_drones)} drones ===")
            for drone in all_drones:
                battery_logger.info(
                    f"Drone {drone.serial_number}: Batería {drone.battery_capacity}%, Estado: {drone.state}"
                )

            # Buscar drones con batería < 25% y estado LOADING para actualizar
            affected_drones = [
                drone for drone in all_drones
                if drone.battery_capacity < 25 and drone.state == DroneState.LOADING
            ]

            if not affected_drones:
                battery_logger.info("No se encontraron drones con batería baja en estado LOADING para actualizar")
            else:
                # Actualizar estado de drones afectados
                for drone in affected_drones:
                    old_state = drone.state
                    drone.state = DroneState.RETURNING
                    await drone.save()

                    battery_logger.warning(
                        f"ACCIÓN: Drone {drone.serial_number} cambiado de {old_state} a {drone.state} "
                        f"por batería baja ({drone.battery_capacity}%)"
                    )

                battery_logger.info(f"Verificación completada. {len(affected_drones)} drones actualizados")

        except Exception as e:
            battery_logger.error(f"Error durante la verificación de batería: {str(e)}")

    async def _async_scheduler(self):
        """
        Ejecuta el scheduler asíncrono que verifica la batería periódicamente.
        """
        battery_logger.info("Iniciando scheduler asíncrono de monitoreo de batería")

        while self.is_running:
            try:
                await self.check_battery_levels()
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                battery_logger.info("Scheduler de monitoreo de batería cancelado")
                break
            except Exception as e:
                battery_logger.error(f"Error en el scheduler asíncrono: {str(e)}")
                # Continuar con el siguiente ciclo después de un breve delay
                await asyncio.sleep(5)

        battery_logger.info("Scheduler de monitoreo de batería detenido")

    async def start(self, interval_seconds: int = 30):
        """
        Inicia el monitor de batería con el intervalo especificado.

        Args:
            interval_seconds: Intervalo en segundos entre verificaciones (default: 30)
        """
        if self.is_running:
            battery_logger.warning("El monitor de batería ya está ejecutándose")
            return

        self.interval_seconds = interval_seconds
        self.is_running = True

        # Crear la tarea asíncrona en el loop actual
        self.task = asyncio.create_task(self._async_scheduler())

        battery_logger.info(f"Monitor de batería iniciado. Verificando cada {interval_seconds} segundos")

    async def stop(self):
        """
        Detiene el monitor de batería.
        """
        if not self.is_running:
            return

        self.is_running = False

        # Cancelar la tarea si existe
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        battery_logger.info("Monitor de batería detenido")


# Instancia global del monitor de batería
battery_monitor = BatteryMonitor()