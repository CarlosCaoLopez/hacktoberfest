# app/services/drone_service.py
from typing import Dict, List
from app.models.drone import Drone, DroneState, DroneRegistration, BatteryLevel
from app.models.medication import Medication
from fastapi import HTTPException

class DroneService:
    def __init__(self):
        self.drones: Dict[str, Drone] = {}
        self.medications: Dict[str, List[Medication]] = {}

    def register_drone(self, data: DroneRegistration) -> Drone:
        if data.serial_number in self.drones:
            raise HTTPException(status_code=400, detail="Serial duplicado")
        drone = Drone(**data.dict(), state=DroneState.IDLE)
        self.drones[data.serial_number] = drone
        self.medications[data.serial_number] = []
        return drone

    def get_available_drones(self) -> List[Drone]:
        return [
            d for d in self.drones.values()
            if d.state == DroneState.IDLE and d.battery_capacity >= 25
        ]

    def load_drone(self, serial: str, meds: List[Medication]) -> Drone:
        if serial not in self.drones:
            raise HTTPException(status_code=404, detail="Drone no encontrado")
        drone = self.drones[serial]

        if drone.battery_capacity < 25:
            raise HTTPException(status_code=400, detail="Batería < 25%")
        if drone.state not in [DroneState.IDLE, DroneState.LOADING]:
            raise HTTPException(status_code=400, detail="Estado no válido para carga")

        total_weight = sum(m.weight for m in meds)
        if total_weight > drone.weight_limit:
            raise HTTPException(status_code=400, detail="Peso excede el límite")

        self.medications[serial].extend(meds)
        drone.state = DroneState.LOADED if total_weight > 0 else DroneState.LOADING
        self.drones[serial] = drone
        return drone

    def get_medications(self, serial: str) -> List[Medication]:
        if serial not in self.medications:
            raise HTTPException(status_code=404, detail="Drone no encontrado")
        return self.medications[serial]

    def get_battery(self, serial: str) -> BatteryLevel:
        if serial not in self.drones:
            raise HTTPException(status_code=404, detail="Drone no encontrado")
        return BatteryLevel(battery_capacity=self.drones[serial].battery_capacity)
