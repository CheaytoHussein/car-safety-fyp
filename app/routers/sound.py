from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SoundEvent
from app.schemas import DetectionResult, SoundAnalysisResponse
from app.services.alert_service import evaluate_sound_alerts
from app.services.device_service import get_or_create_device
from app.services.yamnet_service import yamnet_service

router = APIRouter(prefix="/sound", tags=["sound"])

_ALLOWED_CONTENT_TYPES = {"audio/wav", "audio/wave", "audio/x-wav"}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/analyze", response_model=SoundAnalysisResponse, status_code=201)
async def analyze_sound(
    device_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only WAV files are accepted")

    audio_bytes = await file.read()
    if len(audio_bytes) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    try:
        result = await yamnet_service.analyze(audio_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Audio processing failed: {exc}")

    device = await get_or_create_device(device_id, db)

    event = SoundEvent(
        device_id=device.id,
        is_baby_crying=result.baby.detected,
        baby_confidence=result.baby.confidence,
        is_dog_detected=result.dog.detected,
        dog_confidence=result.dog.confidence,
        is_cat_detected=result.cat.detected,
        cat_confidence=result.cat.confidence,
        top_labels=result.top_labels,
        audio_duration_s=result.audio_duration_s,
    )
    db.add(event)
    await db.flush()

    alerts = await evaluate_sound_alerts(event, db)

    return SoundAnalysisResponse(
        id=event.id,
        device_id=event.device_id,
        baby=DetectionResult(detected=result.baby.detected, confidence=result.baby.confidence),
        dog=DetectionResult(detected=result.dog.detected, confidence=result.dog.confidence),
        cat=DetectionResult(detected=result.cat.detected, confidence=result.cat.confidence),
        top_labels=result.top_labels,
        audio_duration_s=event.audio_duration_s,
        recorded_at=event.recorded_at,
        alerts_triggered=len(alerts),
    )
