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

    async def toggle(self) -> None:
        if self.state is State.IDLE:
            self.recorder.start()
            self.state = State.RECORDING
            self._show("recording")
        elif self.state is State.RECORDING:
            audio = self.recorder.stop()
            if len(audio) < MIN_SECONDS * SAMPLE_RATE:
                self.state = State.IDLE
                self._show("idle")
                notify("Dicta", "Recording too short")
                return
            self.state = State.TRANSCRIBING
            self._show("processing")
            try:
                text = await asyncio.to_thread(self.transcriber.transcribe, audio)
                if text:
                    copy_text(text)
                    notify("Dicta", "Copied to clipboard")
                else:
                    notify("Dicta", "No speech detected")
            except Exception as exc:
                notify("Dicta", f"Error: {exc}")
                raise
            finally:
                self.state = State.IDLE
                self._show("idle")

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
