import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SmokeLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AirQualityEnum(str, Enum):
    GOOD = "GOOD"
    MODERATE = "MODERATE"
    POOR = "POOR"
    HAZARDOUS = "HAZARDOUS"


class CoLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SoundClassEnum(str, Enum):
    BABY_CRY = "BABY_CRY"
    CAT_MEOW = "CAT_MEOW"
    DOG_BARK = "DOG_BARK"


class SensorPayload(BaseModel):
    device_id: str = Field(..., description="Serial number hardcoded in firmware")
    temperature: float
    humidity: float
    smokeLevel: SmokeLevelEnum
    airQuality: AirQualityEnum
    coLevel: CoLevelEnum
    noise_detected: bool = False
    latitude: float
    longitude: float


class SensorReadingResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    temperature: float | None
    humidity: float | None
    smoke_level: str | None
    air_quality: str | None
    co_level: str | None
    noise_detected: bool
    latitude: float | None
    longitude: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class SoundEventPayload(BaseModel):
    device_id: str = Field(..., description="Serial number hardcoded in firmware")
    sound_class: SoundClassEnum
    confidence: float = Field(..., ge=0.0, le=1.0)


class SoundEventResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    sound_class: str
    confidence: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    database: str
    yamnet_loaded: bool
    version: str = "1.0.0"
