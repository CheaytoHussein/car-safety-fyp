from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SensorReading
from app.schemas import SensorPayload, SensorReadingResponse
from app.services.alert_service import evaluate_sensor_alerts
from app.services.device_service import get_or_create_device

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("", response_model=SensorReadingResponse, status_code=201)
async def update_sensors(payload: SensorPayload, db: AsyncSession = Depends(get_db)):
    device = await get_or_create_device(payload.device_id, db)

    reading = SensorReading(
        device_id=device.id,
        temperature=payload.temperature,
        humidity=payload.humidity,
        smoke_level=payload.smokeLevel.value,
        air_quality=payload.airQuality.value,
        co_level=payload.coLevel.value,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(reading)
    await db.flush()

    alerts = await evaluate_sensor_alerts(reading, db)

    return SensorReadingResponse(
        id=reading.id,
        device_id=reading.device_id,
        temperature=reading.temperature,
        humidity=reading.humidity,
        smoke_level=reading.smoke_level,
        air_quality=reading.air_quality,
        co_level=reading.co_level,
        latitude=reading.latitude,
        longitude=reading.longitude,
        recorded_at=reading.recorded_at,
        alerts_triggered=len(alerts),
    )
