from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, SensorReading, SoundEvent


async def evaluate_sensor_alerts(reading: SensorReading, db: AsyncSession) -> list[Alert]:
    alerts: list[Alert] = []

    if reading.co_level == "HIGH":
        alerts.append(Alert(
            device_id=reading.device_id,
            sensor_reading_id=reading.id,
            alert_type="HIGH_CO",
            severity="CRITICAL",
            message="Dangerous CO level detected",
        ))

    if reading.smoke_level == "HIGH":
        alerts.append(Alert(
            device_id=reading.device_id,
            sensor_reading_id=reading.id,
            alert_type="HIGH_SMOKE",
            severity="HIGH",
            message="High smoke concentration detected",
        ))

    if reading.air_quality in ("POOR", "HAZARDOUS"):
        alerts.append(Alert(
            device_id=reading.device_id,
            sensor_reading_id=reading.id,
            alert_type="POOR_AIR_QUALITY",
            severity="CRITICAL" if reading.air_quality == "HAZARDOUS" else "HIGH",
            message=f"Air quality is {reading.air_quality}",
        ))

    for alert in alerts:
        db.add(alert)

    return alerts


async def evaluate_sound_alerts(event: SoundEvent, db: AsyncSession) -> list[Alert]:
    alerts: list[Alert] = []

    if event.is_baby_crying:
        alerts.append(Alert(
            device_id=event.device_id,
            sound_event_id=event.id,
            alert_type="BABY_CRYING",
            severity="HIGH",
            message=f"Baby crying detected ({event.baby_confidence:.1%} confidence)",
        ))

    if event.is_dog_detected:
        alerts.append(Alert(
            device_id=event.device_id,
            sound_event_id=event.id,
            alert_type="DOG_IN_CAR",
            severity="HIGH",
            message=f"Dog detected in car ({event.dog_confidence:.1%} confidence)",
        ))

    if event.is_cat_detected:
        alerts.append(Alert(
            device_id=event.device_id,
            sound_event_id=event.id,
            alert_type="CAT_IN_CAR",
            severity="HIGH",
            message=f"Cat detected in car ({event.cat_confidence:.1%} confidence)",
        ))

    for alert in alerts:
        db.add(alert)

    return alerts
