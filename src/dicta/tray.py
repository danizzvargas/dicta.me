"""System tray icon through the StatusNotifierItem protocol."""

import asyncio
import os
from collections.abc import Awaitable, Callable

from dbus_fast import PropertyAccess
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, dbus_property, method, signal

WATCHER = "org.kde.StatusNotifierWatcher"
WATCHER_PATH = "/StatusNotifierWatcher"
ITEM_PATH = "/StatusNotifierItem"


class _Item(ServiceInterface):
    def __init__(self, on_activate: Callable[[], Awaitable[None]]) -> None:
        super().__init__("org.kde.StatusNotifierItem")
        self._on_activate = on_activate
        self.icon = "audio-input-microphone"
        self.tooltip_title = "Dicta"
        self.tooltip_body = ""

    @dbus_property(access=PropertyAccess.READ)
    def Category(self) -> "s":
        return "ApplicationStatus"

    @dbus_property(access=PropertyAccess.READ)
    def Id(self) -> "s":
        return "dicta"

    @dbus_property(access=PropertyAccess.READ)
    def Title(self) -> "s":
        return "Dicta"

    @dbus_property(access=PropertyAccess.READ)
    def Status(self) -> "s":
        return "Active"

    @dbus_property(access=PropertyAccess.READ)
    def IconName(self) -> "s":
        return self.icon

    @dbus_property(access=PropertyAccess.READ)
    def ToolTip(self) -> "(sa(iiay)ss)":
        return [self.icon, [], self.tooltip_title, self.tooltip_body]

    @dbus_property(access=PropertyAccess.READ)
    def ItemIsMenu(self) -> "b":
        return False

    @dbus_property(access=PropertyAccess.READ)
    def Menu(self) -> "o":
        return "/NO_DBUSMENU"

    @method()
    def Activate(self, x: "i", y: "i") -> None:
        asyncio.ensure_future(self._on_activate())

    @method()
    def SecondaryActivate(self, x: "i", y: "i") -> None:
        pass

    @method()
    def ContextMenu(self, x: "i", y: "i") -> None:
        pass

    @method()
    def Scroll(self, delta: "i", orientation: "s") -> None:
        pass

    @signal()
    def NewIcon(self) -> None:
        pass

    @signal()
    def NewToolTip(self) -> None:
        pass


class Tray:
    """Tray icon showing whether Dicta is ready, recording or processing."""

    STATES = {
        "idle": ("audio-input-microphone", "Ready", "Shortcut active"),
        "recording": ("media-record", "Recording", "Press the shortcut to stop"),
        "processing": ("view-refresh", "Processing", "Transcribing..."),
    }

    def __init__(self, on_activate: Callable[[], Awaitable[None]]) -> None:
        self._item = _Item(on_activate)
        self._bus: MessageBus | None = None

    async def start(self, ready_hint: str = "") -> None:
        bus = await MessageBus().connect()
        self._bus = bus
        name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
        bus.export(ITEM_PATH, self._item)
        await bus.request_name(name)

        introspection = await bus.introspect(WATCHER, WATCHER_PATH)
        proxy = bus.get_proxy_object(WATCHER, WATCHER_PATH, introspection)
        watcher = proxy.get_interface(WATCHER)
        await watcher.call_register_status_notifier_item(name)
        self.set_state("idle", ready_hint)

    def set_state(self, state: str, hint: str = "") -> None:
        icon, title, body = self.STATES[state]
        item = self._item
        item.icon = icon
        item.tooltip_title = f"Dicta: {title}"
        item.tooltip_body = hint or body
        item.NewIcon()
        item.NewToolTip()
        item.emit_properties_changed({"IconName": icon})

    def close(self) -> None:
        if self._bus is not None:
            self._bus.disconnect()
            self._bus = None
