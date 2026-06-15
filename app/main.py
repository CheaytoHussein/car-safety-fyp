import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import debug, health, sensors, sound
from app.services.yamnet_service import yamnet_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load YAMNet at startup so the first /sound/analyze request is not slow.
    # Model download (~17 MB) is cached locally by TF Hub after the first run.
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, yamnet_service.load)
    yield


app = FastAPI(
    title="Car Safety API",
    version="1.0.0",
    description="Receives ESP32 sensor data and analyses audio for baby crying detection.",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(sensors.router)
app.include_router(sound.router)
app.include_router(debug.router)
