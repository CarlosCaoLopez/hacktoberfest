# app/routes/medications.py
from fastapi import APIRouter, status
from typing import List
from app.models.medication import Medication
from app.models.drone import Drone
from app.services.drone_service import DroneService

router = APIRouter(prefix="/api/v1/drones", tags=["Medications"])
service = DroneService()

@router.post("/{serialNumber}/load", response_model=Drone)
async def load_drone(serialNumber: str, meds: List[Medication]):
    return await service.load_drone(serialNumber, meds)

@router.get("/{serialNumber}/medications", response_model=List[Medication])
async def get_medications(serialNumber: str):
    return await service.get_medications(serialNumber)
