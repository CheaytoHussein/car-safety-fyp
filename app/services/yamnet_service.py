import asyncio
import csv
import io
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import librosa
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

YAMNET_URL = "https://tfhub.dev/google/yamnet/1"

# AudioSet class-name fragments that map to each subject.
# We take the max score across all matching classes as the subject's confidence.
_TARGET_PATTERNS: dict[str, list[str]] = {
    "baby": ["baby cry", "infant cry"],
    "dog":  ["bark", "dog", "whimper", "yip", "howl"],
    "cat":  ["meow", "cat", "purr"],
}

# Thresholds applied to the 90th-percentile frame score (not the mean).
# Because we take the top-10% of frames, these values are higher than
# they would be for a mean-based approach.
_THRESHOLDS: dict[str, float] = {
    "baby": 0.50,
    "dog":  0.50,
    "cat":  0.40,
}

_executor = ThreadPoolExecutor(max_workers=2)


@dataclass
class SubjectResult:
    detected: bool
    confidence: float


@dataclass
class SoundAnalysisResult:
    baby: SubjectResult
    dog: SubjectResult
    cat: SubjectResult
    top_labels: list[dict]
    audio_duration_s: float


class YAMNetService:
    def __init__(self):
        self._model = None
        self._class_names: list[str] = []
        # Maps subject key → list of class indices that match its patterns
        self._subject_indices: dict[str, list[int]] = {}

    def load(self) -> None:
        if self._model is not None:
            return
        self._model = hub.load(YAMNET_URL)
        class_map_path = self._model.class_map_path().numpy()
        with tf.io.gfile.GFile(class_map_path) as f:
            reader = csv.reader(f)
            next(reader)  # skip header: index,mid,display_name
            self._class_names = [row[2] for row in reader]

        for subject, patterns in _TARGET_PATTERNS.items():
            self._subject_indices[subject] = [
                i for i, name in enumerate(self._class_names)
                if any(p in name.lower() for p in patterns)
            ]

    def _run_inference(self, audio_bytes: bytes) -> SoundAnalysisResult:
        self.load()

        # librosa resamples to 16 kHz mono — what YAMNet requires
        waveform, _ = librosa.load(io.BytesIO(audio_bytes), sr=16000, mono=True)
        duration = len(waveform) / 16000.0

        scores, _, _ = self._model(waveform)
        frame_scores = scores.numpy()   # shape: (num_frames, 521)

        # 90th-percentile across frames — captures peak activity without
        # being thrown off by background frames when a sound is intermittent.
        # e.g. a cat that meows in 3 of 10 frames still scores well here.
        peak_scores = np.percentile(frame_scores, 90, axis=0)

        # Top-10 labels (use peak scores so display matches detection logic)
        top_indices = np.argsort(peak_scores)[-10:][::-1]
        top_labels = [
            {"label": self._class_names[i], "score": round(float(peak_scores[i]), 4)}
            for i in top_indices
        ]

        def _subject_result(subject: str) -> SubjectResult:
            indices = self._subject_indices.get(subject, [])
            confidence = float(np.max(peak_scores[indices])) if indices else 0.0
            confidence = round(confidence, 4)
            return SubjectResult(
                detected=confidence >= _THRESHOLDS[subject],
                confidence=confidence,
            )

        return SoundAnalysisResult(
            baby=_subject_result("baby"),
            dog=_subject_result("dog"),
            cat=_subject_result("cat"),
            top_labels=top_labels,
            audio_duration_s=round(duration, 2),
        )

    async def analyze(self, audio_bytes: bytes) -> SoundAnalysisResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._run_inference, audio_bytes)


yamnet_service = YAMNetService()
