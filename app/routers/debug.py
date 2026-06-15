import json

from fastapi import APIRouter, Request

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/ingest")
async def debug_ingest(request: Request):
    body = await request.body()
    try:
        data = await request.json()
        print("\n── Incoming payload ──────────────────────")
        print(json.dumps(data, indent=2))
        print("──────────────────────────────────────────\n")
    except Exception:
        print("Raw body:", body.decode(errors="replace"))
    return {"status": "received"}
