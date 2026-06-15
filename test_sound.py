"""
Quick CLI test for the YAMNet inference layer.
No database or running server required.

Usage:
    python test_sound.py path/to/audio.wav
"""

import asyncio
import sys
from pathlib import Path

# Make sure app package is importable from the project root
sys.path.insert(0, str(Path(__file__).parent))

from app.services.yamnet_service import yamnet_service


def _bar(score: float, width: int = 30) -> str:
    filled = round(score * width)
    return "█" * filled + "░" * (width - filled)


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python test_sound.py <path_to_wav>")
        sys.exit(1)

    wav_path = Path(sys.argv[1])
    if not wav_path.exists():
        print(f"File not found: {wav_path}")
        sys.exit(1)

    print(f"\nLoading YAMNet (first run downloads ~17 MB)...")
    audio_bytes = wav_path.read_bytes()

    print(f"Analysing  →  {wav_path.name}  ({len(audio_bytes) / 1024:.1f} KB)\n")
    result = await yamnet_service.analyze(audio_bytes)

    # ── Detection summary ──────────────────────────────────────────────────
    print("┌─ Detection results " + "─" * 40)
    subjects = [
        ("🍼 Baby crying", result.baby),
        ("🐶 Dog",         result.dog),
        ("🐱 Cat",         result.cat),
    ]
    for label, subject in subjects:
        status = "✅ DETECTED" if subject.detected else "  not detected"
        print(f"│  {label:<16}  {_bar(subject.confidence)}  {subject.confidence:.1%}  {status}")
    print(f"│")
    print(f"│  Duration: {result.audio_duration_s:.2f}s")
    print("└" + "─" * 60)

    # ── Top-10 YAMNet labels ───────────────────────────────────────────────
    print("\nTop 10 YAMNet labels:")
    for item in result.top_labels:
        print(f"  {item['label']:<40} {_bar(item['score'], 20)}  {item['score']:.4f}")


asyncio.run(main())
