"""Global shortcut through the xdg-desktop-portal GlobalShortcuts interface."""

import asyncio
from collections.abc import Awaitable, Callable

from dbus_fast import Variant
from dbus_fast.aio import MessageBus

from . import portal


class GlobalShortcut:
    def __init__(self, shortcut_id: str, description: str, trigger: str) -> None:
        self.shortcut_id = shortcut_id
        self.description = description
        self.trigger = trigger
        self._bus: MessageBus | None = None

    async def register(self, on_activated: Callable[[], Awaitable[None]]) -> str:
        bus = await portal.connect()
        self._bus = bus
        shortcuts = await portal.get_interface(
            bus, "org.freedesktop.portal.GlobalShortcuts"
        )

        # 1. Create session.
        handle_token = portal.token("dicta_create")
        results = await portal.call_with_response(
            bus,
            shortcuts.call_create_session,
            {
                "handle_token": Variant("s", handle_token),
                "session_handle_token": Variant("s", portal.token("dicta_session")),
            },
            handle_token=handle_token,
        )
        session = results["session_handle"].value

        # 2. Bind the shortcut.
        handle_token = portal.token("dicta_bind")
        results = await portal.call_with_response(
            bus,
            shortcuts.call_bind_shortcuts,
            session,
            [
                (
                    self.shortcut_id,
                    {
                        "description": Variant("s", self.description),
                        "preferred_trigger": Variant("s", self.trigger),
                    },
                )
            ],
            "",
            {"handle_token": Variant("s", handle_token)},
            handle_token=handle_token,
        )
        bound = results.get("shortcuts")
        trigger = self.trigger
        if bound is not None:
            for sid, props in bound.value:
                if sid == self.shortcut_id and "trigger_description" in props:
                    trigger = props["trigger_description"].value

        # 3. Listen for activations.
        def on_activated_signal(session_handle, shortcut_id, timestamp, options):
            if session_handle == session and shortcut_id == self.shortcut_id:
                asyncio.ensure_future(on_activated())

        shortcuts.on_activated(on_activated_signal)
        return trigger

    def close(self) -> None:
        if self._bus is not None:
            self._bus.disconnect()
            self._bus = None
