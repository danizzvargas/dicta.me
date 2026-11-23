"""Global shortcut through the xdg-desktop-portal GlobalShortcuts interface."""

import asyncio
import os
from collections.abc import Awaitable, Callable

from dbus_fast import Variant
from dbus_fast.aio import MessageBus

PORTAL = "org.freedesktop.portal.Desktop"
PATH = "/org/freedesktop/portal/desktop"
SHORTCUTS_IFACE = "org.freedesktop.portal.GlobalShortcuts"
APP_ID = "me.dicta.Dicta"
REQUEST_IFACE = "org.freedesktop.portal.Request"


def _token(prefix: str) -> str:
    return f"{prefix}_{os.getpid()}"


async def _call_with_response(bus: MessageBus, method, *args, handle_token: str):
    """Call a portal method that answers through a Request.Response signal."""
    sender = bus.unique_name.lstrip(":").replace(".", "_")
    request_path = f"{PATH}/request/{sender}/{handle_token}"
    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()

    def on_message(msg):
        if (
            msg.path == request_path
            and msg.interface == REQUEST_IFACE
            and msg.member == "Response"
        ):
            future.set_result(msg.body)
            return True
        return False

    bus.add_message_handler(on_message)
    try:
        await method(*args)
        code, results = await asyncio.wait_for(future, timeout=60)
    finally:
        bus.remove_message_handler(on_message)
    if code != 0:
        raise RuntimeError(f"Portal request failed (code {code})")
    return results


class GlobalShortcut:
    def __init__(self, shortcut_id: str, description: str, trigger: str) -> None:
        self.shortcut_id = shortcut_id
        self.description = description
        self.trigger = trigger
        self._bus: MessageBus | None = None

    async def register(self, on_activated: Callable[[], Awaitable[None]]) -> str:
        bus = await MessageBus().connect()
        self._bus = bus
        await self._register_app_id(bus)
        introspection = await bus.introspect(PORTAL, PATH)
        proxy = bus.get_proxy_object(PORTAL, PATH, introspection)
        portal = proxy.get_interface(SHORTCUTS_IFACE)

        # 1. Create session.
        session_token = _token("dicta_session")
        handle_token = _token("dicta_create")
        results = await _call_with_response(
            bus,
            portal.call_create_session,
            {
                "handle_token": Variant("s", handle_token),
                "session_handle_token": Variant("s", session_token),
            },
            handle_token=handle_token,
        )
        session = results["session_handle"].value

        # 2. Bind the shortcut.
        handle_token = _token("dicta_bind")
        results = await _call_with_response(
            bus,
            portal.call_bind_shortcuts,
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

        portal.on_activated(on_activated_signal)
        return trigger

    @staticmethod
    async def _register_app_id(bus: MessageBus) -> None:
        """Tell the portal our app id (matches dicta.desktop); needed outside sandboxes."""
        introspection = await bus.introspect(PORTAL, PATH)
        proxy = bus.get_proxy_object(PORTAL, PATH, introspection)
        registry = proxy.get_interface("org.freedesktop.host.portal.Registry")
        await registry.call_register(APP_ID, {})

    def close(self) -> None:
        if self._bus is not None:
            self._bus.disconnect()
            self._bus = None
