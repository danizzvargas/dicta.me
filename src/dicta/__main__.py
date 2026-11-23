"""Dicta: press a global shortcut, speak, press again, and the text is typed."""

import argparse
import asyncio
import os
import signal
import time
from enum import Enum, auto

from . import config as cfg
from .audio import SAMPLE_RATE, Recorder
from .format import FormatOptions, format_text
from .keyboard import RemoteKeyboard, parse_keys
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
    def __init__(self, transcriber: Transcriber, fmt: FormatOptions) -> None:
        self.transcriber = transcriber
        self.fmt = fmt
        self.keyboard: RemoteKeyboard | None = None
        self.tray: Tray | None = None
        self.recorder = Recorder()
        self.state = State.IDLE
        self.notification_id = 0
        self._timer: asyncio.Task | None = None

    async def toggle(self) -> None:
        if self.state is State.IDLE:
            # A finished notification stays in Plasma's history, and updating
            # it does not pop up again. Start each dictation with a new one.
            self.notification_id = 0
            self.recorder.start()
            self.state = State.RECORDING
            self._show("recording")
            self._start_timer(
                "Recording", "Press the shortcut again to stop", "me.dicta.Dicta-recording"
            )
        elif self.state is State.RECORDING:
            audio = self.recorder.stop()
            self._stop_timer()
            if len(audio) < MIN_SECONDS * SAMPLE_RATE:
                self.state = State.IDLE
                self._show("idle")
                self._message("Recording too short", "Nothing was copied")
                return
            self.state = State.TRANSCRIBING
            self._show("processing")
            self._start_timer("Transcribing", "Please wait", "me.dicta.Dicta-processing")
            try:
                text = await asyncio.to_thread(self.transcriber.transcribe, audio)
                text = format_text(text, self.fmt)
                if text:
                    copy_text(text)
                    await self._paste_or_report(text)
                else:
                    self._message("No speech detected", "Nothing was copied")
            except Exception as exc:
                self._message("Error", str(exc), "dialog-error")
                raise
            finally:
                self._stop_timer()
                self.state = State.IDLE
                self._show("idle")

    async def _paste_or_report(self, text: str) -> None:
        """Paste at the cursor when possible; the text stays in the clipboard."""
        if self.keyboard is not None:
            try:
                await asyncio.sleep(0.1)  # let the compositor see the new clipboard
                await self.keyboard.press_combo()
                self._message("Pasted", text, "me.dicta.Dicta")
                return
            except Exception as exc:
                self._message("Paste failed, copied to clipboard", f"{exc}\n{text}", "dialog-warning")
                return
        self._message("Copied to clipboard", text, "me.dicta.Dicta")

    def _start_timer(self, title: str, body: str, icon: str) -> None:
        """Show a persistent notification whose title counts elapsed seconds."""
        self._stop_timer()
        self._message(f"{title}... 0:00", body, icon, 0)
        self._timer = asyncio.ensure_future(self._tick(title, body, icon))

    def _stop_timer(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    async def _tick(self, title: str, body: str, icon: str) -> None:
        start = time.monotonic()
        while True:
            await asyncio.sleep(1)
            minutes, seconds = divmod(int(time.monotonic() - start), 60)
            self._message(f"{title}... {minutes}:{seconds:02d}", body, icon, 0)

    def _message(
        self,
        title: str,
        body: str,
        icon: str = "me.dicta.Dicta",
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
    conf = args.conf
    print(f"Loading model '{conf.model}'...", flush=True)
    transcriber = await asyncio.to_thread(
        Transcriber,
        conf.model,
        conf.language,
        conf.hotwords,
        conf.initial_prompt,
        conf.replacements,
    )
    dicta = Dicta(transcriber, conf.format)

    shortcut = GlobalShortcut("dictate", "Toggle dictation", conf.trigger)
    trigger = await shortcut.register(dicta.toggle)
    if conf.paste:
        keyboard = RemoteKeyboard(conf.paste_keys)
        try:
            await keyboard.start()
            dicta.keyboard = keyboard
        except Exception as exc:
            keyboard.close()
            print(f"Auto-paste unavailable ({exc}); copying to the clipboard only.", flush=True)
            notify("Dicta", f"Auto-paste unavailable: {exc}")
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
    if dicta.keyboard is not None:
        dicta.keyboard.close()
    shortcut.close()
    print("Bye.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="dicta", description=__doc__)
    parser.add_argument("-c", "--config", action="store_true", help="edit the config file in Neovim and exit")
    parser.add_argument("-m", "--model", help="faster-whisper model (overrides config)")
    parser.add_argument("-l", "--language", help="language code, e.g. es (overrides config)")
    parser.add_argument("-t", "--trigger", help="preferred shortcut (overrides config)")
    args = parser.parse_args()

    if args.config:
        os.execvp("nvim", ["nvim", str(cfg.ensure_config())])

    try:
        conf = cfg.load()
    except Exception as exc:
        raise SystemExit(f"Invalid config file {cfg.config_path()}: {exc}")
    for name in ("model", "language", "trigger"):
        if getattr(args, name):
            setattr(conf, name, getattr(args, name))
    try:
        parse_keys(conf.paste_keys)
    except ValueError as exc:
        raise SystemExit(f"Invalid paste_keys in {cfg.config_path()}: {exc}")
    args.conf = conf
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
