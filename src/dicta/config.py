"""User configuration stored in ~/.config/dicta/config.toml."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .format import FormatOptions

TEMPLATE = '''\
# Dicta configuration. Command-line options override these values.
# Restart Dicta after saving for the changes to take effect.

# Whisper model: tiny, base, small, medium, large-v3.
# Bigger models are more accurate and slower on CPU.
model = "small"

# Language code (e.g. "es", "en"). Leave commented to auto-detect.
# language = "es"

# Preferred global shortcut.
trigger = "META+R"

# Words Whisper should favor: names, brands, technical terms.
hotwords = []
# hotwords = ["Neovim", "Claude Code", "Dicta.me"]

# Context that sets vocabulary and style, as if it were said just before.
initial_prompt = ""
# initial_prompt = "Dictado técnico en español sobre programación."

# Paste the text at the cursor after copying it. KDE asks for permission the
# first time. Set to false to only copy to the clipboard.
paste = true

# Keys used to paste. Ctrl+Shift+V works in terminals and most apps.
paste_keys = "ctrl+shift+v"

# Formatting of the final text. Whitespace is always cleaned up.
[format]
capitalize = true             # capital letter at the start
final_period = true           # add a period at the end if missing
capitalize_sentences = false  # capital letter after every period too

# Fixes applied to the final text (case-insensitive, whole words).
[replacements]
# "neo vim" = "Neovim"
# "cloud code" = "Claude Code"
'''


@dataclass
class Config:
    model: str = "small"
    language: str | None = None
    trigger: str = "META+R"
    hotwords: list[str] = field(default_factory=list)
    initial_prompt: str | None = None
    replacements: dict[str, str] = field(default_factory=dict)
    format: FormatOptions = field(default_factory=FormatOptions)
    paste: bool = True
    paste_keys: str = "ctrl+shift+v"


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "dicta" / "config.toml"


def ensure_config() -> Path:
    """Create the config file from the template if it does not exist."""
    path = config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(TEMPLATE, encoding="utf-8")
    return path


def load() -> Config:
    path = config_path()
    if not path.exists():
        return Config()
    with path.open("rb") as f:
        data = tomllib.load(f)
    return Config(
        model=data.get("model", "small"),
        language=data.get("language") or None,
        trigger=data.get("trigger", "META+R"),
        hotwords=list(data.get("hotwords", [])),
        initial_prompt=data.get("initial_prompt") or None,
        replacements=dict(data.get("replacements", {})),
        format=FormatOptions(**data.get("format", {})),
        paste=bool(data.get("paste", True)),
        paste_keys=data.get("paste_keys", "ctrl+shift+v"),
    )
