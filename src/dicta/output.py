"""Deliver text and status messages to the user."""

import subprocess


def copy_text(text: str) -> None:
    subprocess.run(["wl-copy", "--", text], check=True)


def notify(
    title: str,
    body: str,
    *,
    icon: str = "audio-input-microphone",
    replace_id: int = 0,
    timeout_ms: int = 5000,
) -> int:
    """Show a notification and return its id.

    Pass the id back as replace_id to update it in place. A timeout of 0
    keeps the notification on screen until it is replaced or closed.
    """
    cmd = ["notify-send", "-a", "Dicta", "-p", "-i", icon, "-t", str(timeout_ms)]
    if replace_id:
        cmd += ["-r", str(replace_id)]
    result = subprocess.run(cmd + [title, body], capture_output=True, text=True)
    try:
        return int(result.stdout.strip())
    except ValueError:
        return replace_id
