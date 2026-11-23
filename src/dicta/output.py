"""Deliver text to the user."""

import subprocess


def copy_text(text: str) -> None:
    subprocess.run(["wl-copy", "--", text], check=True)


def notify(title: str, body: str) -> None:
    subprocess.run(["notify-send", "-a", "Dicta", title, body], check=False)
