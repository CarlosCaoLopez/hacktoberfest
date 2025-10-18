# app/routes/drones.py
from fastapi import APIRouter, status
from typing import List
from app.models.drone import Drone, DroneRegistration, BatteryLevel
from app.services.drone_service import DroneService

router = APIRouter(prefix="/api/v1/drones", tags=["Drones"])
service = DroneService()

@router.post("/", response_model=Drone, status_code=status.HTTP_201_CREATED)
async def register_drone(drone: DroneRegistration):
    return await service.register_drone(drone)

@router.get("/available", response_model=List[Drone])
async def available_drones():
    return await service.get_available_drones()

@router.get("/{serialNumber}/battery", response_model=BatteryLevel)
async def get_battery(serialNumber: str):
    return await service.get_battery(serialNumber)
