from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device


async def get_or_create_device(device_id: str, db: AsyncSession) -> Device:
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        device = Device(device_id=device_id)
        db.add(device)
        await db.flush()
    device.last_seen = datetime.now(timezone.utc)
    return device
