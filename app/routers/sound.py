from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SoundEvent
from app.schemas import SoundEventPayload, SoundEventResponse
from app.services.device_service import get_device

router = APIRouter(prefix="/sound", tags=["sound"])


@router.post("", response_model=SoundEventResponse, status_code=201)
async def ingest_sound_event(payload: SoundEventPayload, db: AsyncSession = Depends(get_db)):
    device = await get_device(payload.device_id, db)

    event = SoundEvent(
        device_id=device.id,
        sound_class=payload.sound_class.value,
        confidence=payload.confidence,
    )
    db.add(event)
    await db.flush()

    return SoundEventResponse(
        id=event.id,
        device_id=event.device_id,
        sound_class=event.sound_class,
        confidence=event.confidence,
        recorded_at=event.recorded_at,
    )
