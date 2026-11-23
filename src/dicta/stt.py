"""Speech-to-text with faster-whisper."""

import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model: str = "small", language: str | None = None) -> None:
        self.language = language
        self._model = WhisperModel(model, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self._model.transcribe(
            audio,
            language=self.language,
            vad_filter=True,
            beam_size=5,
        )
        return " ".join(s.text.strip() for s in segments).strip()
