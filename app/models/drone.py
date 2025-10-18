# app/models/drone.py
from pydantic import BaseModel, Field, AnyUrl
from enum import Enum
from typing import List
from app.models.medication import Medication


class DroneModel(str, Enum):
    Lightweight = "Lightweight"
    Middleweight = "Middleweight"
    Cruiserweight = "Cruiserweight"
    Heavyweight = "Heavyweight"


class DroneState(str, Enum):
    IDLE = "IDLE"
    LOADING = "LOADING"
    LOADED = "LOADED"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    RETURNING = "RETURNING"


class DroneRegistration(BaseModel):
    serial_number: str = Field(..., max_length=100)
    model: DroneModel
    weight_limit: float = Field(..., ge=0, le=500)
    battery_capacity: int = Field(..., ge=0, le=100)


class Drone(BaseModel):
    serial_number: str
    model: DroneModel
    weight_limit: float
    battery_capacity: int
    state: DroneState


class BatteryLevel(BaseModel):
    battery_capacity: int = Field(..., ge=0, le=100)
