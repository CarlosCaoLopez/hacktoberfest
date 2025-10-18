# app/models/medication.py
from pydantic import BaseModel, Field, AnyUrl, constr
from beanie import Document



class Medication(Document):
    name: constr(pattern=r"^[a-zA-Z0-9_-]+$")
    weight: float = Field(..., ge=0.01)

    code: constr(pattern=r"^[A-Z0-9_]+$")
    image: AnyUrl

    class Settings:
        name = "medications"
