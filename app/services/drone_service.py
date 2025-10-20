# app/services/drone_service.py
from typing import List
from app.models.drone import Drone, DroneState, DroneRegistration, BatteryLevel
from app.models.medication import Medication
from app.models.error import Error
from fastapi import HTTPException

class DroneService:
    def _create_error_response(self, code: str, message: str, status_code: int):
        """Crea una respuesta de error estructurada según la especificación"""
        error = Error(code=code, message=message)
        raise HTTPException(status_code=status_code, detail=error.dict())

    async def register_drone(self, data: DroneRegistration) -> Drone:
        # Verificar si ya existe un drone con el mismo serial
        existing_drone = await Drone.find_one(Drone.serial_number == data.serial_number)
        if existing_drone:
            self._create_error_response("DUPLICATE_SERIAL", "Serial duplicado", 400)

        # Crear nuevo drone
        drone = Drone(**data.dict(), state=DroneState.IDLE)
        await drone.insert()
        return drone

    async def get_available_drones(self) -> List[Drone]:
        drones = await Drone.find(
            Drone.state == DroneState.IDLE,
            Drone.battery_capacity >= 25
        ).to_list()
        return drones

    async def load_drone(self, serial: str, meds: List[Medication]) -> Drone:
        # Buscar el drone
        drone = await Drone.find_one(Drone.serial_number == serial)
        if not drone:
            self._create_error_response("DRONE_NOT_FOUND", "Drone no encontrado", 404)

        # Validar batería
        if drone.battery_capacity < 25:
            self._create_error_response("LOW_BATTERY", "Batería < 25%", 400)

        # Validar estado - debe estar en IDLE o LOADING
        if drone.state not in [DroneState.IDLE, DroneState.LOADING]:
            self._create_error_response("INVALID_STATE", "Estado no válido para carga", 400)

        # Validar hay medicamentos
        if not meds:
            self._create_error_response("NO_MEDICATIONS", "No se han proporcionado medicamentos", 400)

        # Validar peso
        current_weight = 0
        if drone.state != DroneState.IDLE:
            # Solo validar peso actual si no está IDLE
            current_weight = sum(med["weight"] for med in drone.medications)

        new_weight = sum(m.weight for m in meds)
        total_weight = current_weight + new_weight

        if total_weight > drone.weight_limit:
            self._create_error_response("WEIGHT_EXCEEDED", "Peso excede el límite", 400)

        # Agregar medicamentos y actualizar estado
        for med in meds:
            drone.medications.append(med.dict())

        drone.state = DroneState.LOADED if total_weight == drone.weight_limit else DroneState.LOADING
        await drone.save()
        return drone

    async def get_medications(self, serial: str) -> List[Medication]:
        drone = await Drone.find_one(Drone.serial_number == serial)
        if not drone:
            self._create_error_response("DRONE_NOT_FOUND", "Drone no encontrado", 404)

        # Convertir dict a objetos Medication
        medications = [Medication(**med) for med in drone.medications]
        return medications

    async def get_battery(self, serial: str) -> BatteryLevel:
        drone = await Drone.find_one(Drone.serial_number == serial)
        if not drone:
            self._create_error_response("DRONE_NOT_FOUND", "Drone no encontrado", 404)

        return BatteryLevel(battery_capacity=drone.battery_capacity)
