"""Helpers shared by the xdg-desktop-portal clients."""

import asyncio
import itertools
import os

from dbus_fast.aio import MessageBus

PORTAL = "org.freedesktop.portal.Desktop"
PATH = "/org/freedesktop/portal/desktop"
APP_ID = "me.dicta.Dicta"
REQUEST_IFACE = "org.freedesktop.portal.Request"

_counter = itertools.count()


def token(prefix: str) -> str:
    """Return a unique token for request and session handles."""
    return f"{prefix}_{os.getpid()}_{next(_counter)}"


async def connect() -> MessageBus:
    """Open a session bus connection and register the app id with the portal.

    The portal identifies the app through me.dicta.Dicta.desktop, which
    dicta.sh installs.
    """
    bus = await MessageBus().connect()
    registry = await get_interface(bus, "org.freedesktop.host.portal.Registry")
    await registry.call_register(APP_ID, {})
    return bus


async def get_interface(bus: MessageBus, name: str):
    introspection = await bus.introspect(PORTAL, PATH)
    proxy = bus.get_proxy_object(PORTAL, PATH, introspection)
    return proxy.get_interface(name)


async def call_with_response(bus: MessageBus, method, *args, handle_token: str):
    """Call a portal method that answers through a Request.Response signal."""
    sender = bus.unique_name.lstrip(":").replace(".", "_")
    request_path = f"{PATH}/request/{sender}/{handle_token}"
    future: asyncio.Future = asyncio.get_running_loop().create_future()

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
        # The user may need time to answer a permission dialog.
        code, results = await asyncio.wait_for(future, timeout=120)
    finally:
        bus.remove_message_handler(on_message)
    if code != 0:
        raise RuntimeError(f"Portal request denied or cancelled (code {code})")
    return results
