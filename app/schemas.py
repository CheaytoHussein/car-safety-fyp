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


class SensorPayload(BaseModel):
    device_id: str = Field(..., description="Unique ESP32 identifier (e.g. MAC address)")
    temperature: float
    humidity: float
    smokeLevel: SmokeLevelEnum
    airQuality: AirQualityEnum
    coLevel: CoLevelEnum
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
    latitude: float | None
    longitude: float | None
    recorded_at: datetime
    alerts_triggered: int

    model_config = {"from_attributes": True}


class DetectionResult(BaseModel):
    detected: bool
    confidence: float


class SoundAnalysisResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    baby: DetectionResult
    dog: DetectionResult
    cat: DetectionResult
    top_labels: list[dict]
    audio_duration_s: float | None
    recorded_at: datetime
    alerts_triggered: int

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    database: str
    yamnet_loaded: bool
    version: str = "1.0.0"
