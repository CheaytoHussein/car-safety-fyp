from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SensorReading
from app.schemas import SensorPayload, SensorReadingResponse
from app.services.device_service import get_device

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("", response_model=SensorReadingResponse, status_code=201)
async def ingest_sensor_reading(payload: SensorPayload, db: AsyncSession = Depends(get_db)):
    device = await get_device(payload.device_id, db)

    reading = SensorReading(
        device_id=device.id,
        temperature=payload.temperature,
        humidity=payload.humidity,
        smoke_level=payload.smokeLevel.value,
        air_quality=payload.airQuality.value,
        co_level=payload.coLevel.value,
        noise_detected=payload.noise_detected,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(reading)
    await db.flush()

    return SensorReadingResponse(
        id=reading.id,
        device_id=reading.device_id,
        temperature=reading.temperature,
        humidity=reading.humidity,
        smoke_level=reading.smoke_level,
        air_quality=reading.air_quality,
        co_level=reading.co_level,
        noise_detected=reading.noise_detected,
        latitude=reading.latitude,
        longitude=reading.longitude,
        recorded_at=reading.recorded_at,
    )
