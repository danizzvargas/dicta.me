"""Dicta: press a global shortcut, speak, press again, and the text is typed."""

import argparse
import asyncio
import signal
from enum import Enum, auto

from .audio import SAMPLE_RATE, Recorder
from .output import copy_text, notify
from .shortcut import GlobalShortcut
from .stt import Transcriber
from .tray import Tray

MIN_SECONDS = 0.3


class State(Enum):
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()


class Dicta:
    def __init__(self, transcriber: Transcriber) -> None:
        self.transcriber = transcriber
        self.tray: Tray | None = None
        self.recorder = Recorder()
        self.state = State.IDLE
        self.notification_id = 0

    async def toggle(self) -> None:
        if self.state is State.IDLE:
            self.recorder.start()
            self.state = State.RECORDING
            self._show("recording")
            self._message(
                "Recording...", "Press the shortcut again to stop", "media-record", 0
            )
        elif self.state is State.RECORDING:
            audio = self.recorder.stop()
            if len(audio) < MIN_SECONDS * SAMPLE_RATE:
                self.state = State.IDLE
                self._show("idle")
                self._message("Recording too short", "Nothing was copied")
                return
            self.state = State.TRANSCRIBING
            self._show("processing")
            self._message("Transcribing...", "Please wait", "view-refresh", 0)
            try:
                text = await asyncio.to_thread(self.transcriber.transcribe, audio)
                if text:
                    copy_text(text)
                    self._message("Copied to clipboard", text, "edit-copy")
                else:
                    self._message("No speech detected", "Nothing was copied")
            except Exception as exc:
                self._message("Error", str(exc), "dialog-error")
                raise
            finally:
                self.state = State.IDLE
                self._show("idle")

    def _message(
        self,
        title: str,
        body: str,
        icon: str = "audio-input-microphone",
        timeout_ms: int = 5000,
    ) -> None:
        """Show or update the single Dicta notification."""
        self.notification_id = notify(
            title,
            body,
            icon=icon,
            replace_id=self.notification_id,
            timeout_ms=timeout_ms,
        )

    def _show(self, state: str) -> None:
        if self.tray is not None:
            self.tray.set_state(state)


async def run(args: argparse.Namespace) -> None:
    print(f"Loading model '{args.model}'...", flush=True)
    transcriber = await asyncio.to_thread(Transcriber, args.model, args.language)
    dicta = Dicta(transcriber)

    shortcut = GlobalShortcut("dictate", "Toggle dictation", args.trigger)
    trigger = await shortcut.register(dicta.toggle)
    tray = Tray(dicta.toggle)
    await tray.start(f"Shortcut: {trigger}")
    dicta.tray = tray
    print(f"Ready. Shortcut: {trigger}. Press Ctrl+C to quit.", flush=True)
    notify("Dicta", f"Ready. Shortcut: {trigger}")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    tray.close()
    shortcut.close()
    print("Bye.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="dicta", description=__doc__)
    parser.add_argument("--model", default="small", help="faster-whisper model (default: small)")
    parser.add_argument("--language", default=None, help="language code, e.g. es (default: auto)")
    parser.add_argument("--trigger", default="META+R", help="preferred shortcut (default: META+R)")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
