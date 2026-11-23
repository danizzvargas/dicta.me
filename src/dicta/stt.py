"""Speech-to-text with faster-whisper."""

import re

import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(
        self,
        model: str = "small",
        language: str | None = None,
        hotwords: list[str] | None = None,
        initial_prompt: str | None = None,
        replacements: dict[str, str] | None = None,
    ) -> None:
        self.language = language
        self.hotwords = ", ".join(hotwords) if hotwords else None
        self.initial_prompt = initial_prompt
        self._replacements = [
            (re.compile(rf"(?<!\w){re.escape(old)}(?!\w)", re.IGNORECASE), new)
            for old, new in (replacements or {}).items()
        ]
        self._model = WhisperModel(model, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self._model.transcribe(
            audio,
            language=self.language,
            vad_filter=True,
            beam_size=5,
            hotwords=self.hotwords,
            initial_prompt=self.initial_prompt,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        for pattern, new in self._replacements:
            text = pattern.sub(lambda _m, new=new: new, text)
        return text
