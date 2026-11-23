# Dicta.me

Local voice dictation for **KDE Plasma 6 on Wayland**. Press a shortcut, speak, press it again, and the text is pasted at the cursor. Everything runs on your machine, on CPU, with [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

> Other desktops and X11 sessions are not supported or tested.

## Requirements

- KDE Plasma 6 on Wayland, with `xdg-desktop-portal-kde`
- [`uv`](https://docs.astral.sh/uv/), `portaudio`, `wl-clipboard`, `libnotify`

```sh
sudo pacman -S uv portaudio wl-clipboard libnotify   # Arch Linux
```

## Usage

```sh
./dicta.sh        # start (Ctrl+C to quit)
```

1. `Meta+R` starts recording.
2. `Meta+R` again transcribes and pastes the text (it also stays in the clipboard).

A tray icon and a notification show the progress. The first run downloads the model, and KDE asks for permission to register the shortcut and to control the keyboard (needed to paste).

## Configuration

```sh
./dicta.sh -c     # edit ~/.config/dicta/config.toml in Neovim
```

```toml
model = "small"
language = "es"                # omit to auto-detect
hotwords = ["Neovim"]          # words to favor

[replacements]
"neo vim" = "Neovim"
```

Other options (`paste`, `paste_keys`, `[format]`) are in the generated file. Restart Dicta after saving. The options `-m`, `-l` and `-t` override the model, language and shortcut.

## Future improvements

- Stop automatically after a pause in speech.
- Voice commands ("new line", "period").
