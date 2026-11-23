# Dicta.me

Local voice dictation for KDE Plasma (Wayland). Press a global shortcut, speak, press it again, and the transcribed text is copied to the clipboard. Everything runs on your machine, on CPU.

## Usage

```sh
./dicta.sh                      # start in the foreground (Ctrl+C to quit)
./dicta.sh --language es        # force a language (default: auto-detect)
./dicta.sh --model base         # faster, less accurate (default: small)
./dicta.sh --trigger META+D     # preferred shortcut (default: META+R)
```

While the program runs:

1. `Meta+R` starts recording.
2. `Meta+R` again stops, transcribes, and copies the text to the clipboard. Paste it with Ctrl+V.

Stopping the program with Ctrl+C removes the shortcut.

The first run downloads the model. The first time the shortcut is registered, KDE may ask you to confirm it.

## Requirements

- Plasma 6 with `xdg-desktop-portal-kde` (GlobalShortcuts portal)
- [`uv`](https://docs.astral.sh/uv/), `portaudio`, `wl-clipboard`, `libnotify`

```sh
sudo pacman -S uv portaudio wl-clipboard libnotify
```

## How it works

```
Meta+R ─▶ KDE GlobalShortcuts portal ─▶ dicta ─▶ record ─▶ faster-whisper ─▶ wl-copy
```

- `src/dicta/shortcut.py`: registers the shortcut through the portal over D-Bus.
- `src/dicta/audio.py`: in-memory microphone capture (16 kHz mono).
- `src/dicta/stt.py`: transcription with faster-whisper (CPU, int8). The model stays loaded.
- `src/dicta/output.py`: copies the text to the clipboard with `wl-copy` and sends a notification.
- `contrib/me.dicta.Dicta.desktop`: the portal identifies the app through this file. `dicta.sh` installs it into `~/.local/share/applications`.

## Future improvements

- Paste automatically at the cursor. KWin does not support the virtual keyboard protocol used by `wtype`; options are the RemoteDesktop portal, `ydotool` or `dotool`.
- Stop automatically after a pause in speech.
- Configuration file (`~/.config/dicta/config.toml`).
- Custom dictionary and voice commands ("new line", "period").
