# app/models/drone.py
from pydantic import BaseModel, Field, AnyUrl
from beanie import Document
from enum import Enum
from typing import List, Optional


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


class Drone(Document):
    serial_number: str = Field(..., max_length=100)
    model: DroneModel
    weight_limit: float = Field(..., ge=0, le=500)
    battery_capacity: int = Field(..., ge=0, le=100)
    state: DroneState
    medications: List[dict] = Field(default_factory=list)

    class Settings:
        name = "drones"


class BatteryLevel(BaseModel):
    battery_capacity: int = Field(..., ge=0, le=100)
