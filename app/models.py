import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=_utcnow)

    devices: Mapped[list["Device"]] = relationship(back_populates="owner", lazy="noload")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(128))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=_utcnow)
    last_seen: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    owner: Mapped["User | None"] = relationship(back_populates="devices", lazy="noload")
    readings: Mapped[list["SensorReading"]] = relationship(back_populates="device", lazy="noload")
    sound_events: Mapped[list["SoundEvent"]] = relationship(back_populates="device", lazy="noload")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    temperature: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[float | None] = mapped_column(Float)
    smoke_level: Mapped[str | None] = mapped_column(String(16))
    air_quality: Mapped[str | None] = mapped_column(String(16))
    co_level: Mapped[str | None] = mapped_column(String(16))
    noise_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=_utcnow)

    device: Mapped["Device"] = relationship(back_populates="readings", lazy="noload")


class SoundEvent(Base):
    __tablename__ = "sound_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    sound_class: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=_utcnow)

    device: Mapped["Device"] = relationship(back_populates="sound_events", lazy="noload")
