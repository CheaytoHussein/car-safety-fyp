import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=_utcnow)
    last_seen: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    readings: Mapped[list["SensorReading"]] = relationship(back_populates="device", lazy="noload")
    sound_events: Mapped[list["SoundEvent"]] = relationship(back_populates="device", lazy="noload")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="device", lazy="noload")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    temperature: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[float | None] = mapped_column(Float)
    smoke_level: Mapped[str | None] = mapped_column(String(16))
    air_quality: Mapped[str | None] = mapped_column(String(16))
    co_level: Mapped[str | None] = mapped_column(String(16))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=_utcnow)

    device: Mapped["Device"] = relationship(back_populates="readings", lazy="noload")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="sensor_reading", lazy="noload")


class SoundEvent(Base):
    __tablename__ = "sound_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    is_baby_crying: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    baby_confidence: Mapped[float | None] = mapped_column(Float)
    is_dog_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dog_confidence: Mapped[float | None] = mapped_column(Float)
    is_cat_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cat_confidence: Mapped[float | None] = mapped_column(Float)
    top_labels: Mapped[list | None] = mapped_column(JSONB)
    audio_duration_s: Mapped[float | None] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=_utcnow)

    device: Mapped["Device"] = relationship(back_populates="sound_events", lazy="noload")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="sound_event", lazy="noload")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    sensor_reading_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sensor_readings.id", ondelete="SET NULL"), nullable=True
    )
    sound_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sound_events.id", ondelete="SET NULL"), nullable=True
    )
    alert_type: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(8))
    message: Mapped[str | None] = mapped_column(Text)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=_utcnow)

    device: Mapped["Device"] = relationship(back_populates="alerts", lazy="noload")
    sensor_reading: Mapped["SensorReading | None"] = relationship(back_populates="alerts", lazy="noload")
    sound_event: Mapped["SoundEvent | None"] = relationship(back_populates="alerts", lazy="noload")
