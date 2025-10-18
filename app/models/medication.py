# app/models/medication.py
from pydantic import BaseModel, Field, AnyUrl, constr


class Medication(BaseModel):
    name: constr(regex=r"^[a-zA-Z0-9_-]+$")
    weight: float = Field(..., gt=0.01)
    code: constr(regex=r"^[A-Z0-9_]+$")
    image: AnyUrl
