"""Send key presses to the focused window through the RemoteDesktop portal."""

import asyncio
import os
from pathlib import Path

from dbus_fast import Variant
from dbus_fast.aio import MessageBus

from . import portal

KEYBOARD = 1  # device type bitmask
PERSIST_UNTIL_REVOKED = 2

MODIFIERS = {
    "ctrl": 0xFFE3,
    "control": 0xFFE3,
    "shift": 0xFFE1,
    "alt": 0xFFE9,
    "super": 0xFFEB,
    "meta": 0xFFEB,
}


def parse_keys(spec: str) -> list[int]:
    """Turn "ctrl+shift+v" into X11 keysyms: modifiers first, then the key."""
    parts = [p.strip().lower() for p in spec.split("+") if p.strip()]
    if not parts:
        raise ValueError("empty key combination")
    *mods, key = parts
    keysyms = []
    for mod in mods:
        if mod not in MODIFIERS:
            raise ValueError(f"unknown modifier '{mod}' (use ctrl, shift, alt, super)")
        keysyms.append(MODIFIERS[mod])
    if len(key) != 1:
        raise ValueError(f"the last key must be a single character, got '{key}'")
    keysyms.append(ord(key))
    return keysyms


def _token_file() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(base) / "dicta" / "remote-desktop-token"


class RemoteKeyboard:
    def __init__(self, keys: str = "ctrl+shift+v") -> None:
        self.keysyms = parse_keys(keys)
        self._bus: MessageBus | None = None
        self._remote = None
        self._session: str | None = None

    async def start(self) -> None:
        """Open a keyboard session. KDE asks for permission the first time."""
        bus = await portal.connect()
        self._bus = bus
        remote = await portal.get_interface(bus, "org.freedesktop.portal.RemoteDesktop")
        self._remote = remote

        handle_token = portal.token("dicta_rd_create")
        results = await portal.call_with_response(
            bus,
            remote.call_create_session,
            {
                "handle_token": Variant("s", handle_token),
                "session_handle_token": Variant("s", portal.token("dicta_rd_session")),
            },
            handle_token=handle_token,
        )
        session = results["session_handle"].value

        options = {
            "handle_token": Variant("s", portal.token("dicta_rd_select")),
            "types": Variant("u", KEYBOARD),
            "persist_mode": Variant("u", PERSIST_UNTIL_REVOKED),
        }
        token_file = _token_file()
        if token_file.exists():
            options["restore_token"] = Variant("s", token_file.read_text().strip())
        await portal.call_with_response(
            bus,
            remote.call_select_devices,
            session,
            options,
            handle_token=options["handle_token"].value,
        )

        handle_token = portal.token("dicta_rd_start")
        results = await portal.call_with_response(
            bus,
            remote.call_start,
            session,
            "",
            {"handle_token": Variant("s", handle_token)},
            handle_token=handle_token,
        )
        new_token = results.get("restore_token")
        if new_token is not None:
            token_file.parent.mkdir(parents=True, exist_ok=True)
            token_file.write_text(new_token.value)
        self._session = session

    async def press_combo(self) -> None:
        """Press the configured keys in order, then release them in reverse."""
        if self._remote is None or self._session is None:
            raise RuntimeError("keyboard session not started")
        for keysym in self.keysyms:
            await self._remote.call_notify_keyboard_keysym(self._session, {}, keysym, 1)
            await asyncio.sleep(0.01)
        for keysym in reversed(self.keysyms):
            await self._remote.call_notify_keyboard_keysym(self._session, {}, keysym, 0)
            await asyncio.sleep(0.01)

    def close(self) -> None:
        if self._bus is not None:
            self._bus.disconnect()
            self._bus = None
