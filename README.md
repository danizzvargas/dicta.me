# Dicta.me

Local voice dictation for KDE Plasma (Wayland). Press a global shortcut, speak, press it again, and the transcribed text is pasted at the cursor. Everything runs on your machine, on CPU.

## Usage

```sh
./dicta.sh                      # start in the foreground (Ctrl+C to quit)
./dicta.sh -c                   # edit the configuration in Neovim (--config)
./dicta.sh -l es                # force a language (--language), default: auto-detect
./dicta.sh -m base              # faster, less accurate (--model), default: small
./dicta.sh -t META+D            # preferred shortcut (--trigger), default: META+R
```

Command-line options override the configuration file.

While the program runs:

1. `Meta+R` starts recording.
2. `Meta+R` again stops, transcribes, copies the text to the clipboard and pastes it at the cursor with Ctrl+Shift+V.

While it runs, a tray icon shows the state: a microphone when ready, a red dot while recording, and a refresh icon while transcribing. Clicking the icon works like the shortcut.

A single notification follows the process: "Recording..." stays on screen until you stop, then changes to "Transcribing..." and finally to "Copied to clipboard" with the transcribed text.

Stopping the program with Ctrl+C removes the shortcut and the icon.

The first run downloads the model. The first time, KDE asks you to confirm the shortcut and to allow Dicta to control the keyboard (needed to paste). The permission is remembered. If you deny it, Dicta only copies to the clipboard.

## Configuration

`./dicta.sh -c` creates `~/.config/dicta/config.toml` from a commented template and opens it in Neovim. Restart Dicta after saving.

```toml
model = "small"
language = "es"
trigger = "META+R"
paste = true                                    # paste at the cursor after copying
paste_keys = "ctrl+shift+v"                     # keys used to paste
hotwords = ["Neovim", "Claude Code"]          # words Whisper should favor
initial_prompt = ""                             # optional context for vocabulary and style

[format]                                        # formatting of the final text
capitalize = true                               # capital letter at the start
final_period = true                             # period at the end if missing
capitalize_sentences = false                    # capital letter after every period

[replacements]                                  # fixes on the final text
"neo vim" = "Neovim"
```

- `paste = false` keeps only the clipboard. `paste_keys` accepts combinations such as `ctrl+v` (modifiers: `ctrl`, `shift`, `alt`, `super`, then one character).
- `hotwords` and `initial_prompt` bias the model before transcribing.
- `[format]` cleans up whitespace always. `final_period` closes an open `¿` with `?` and an open `¡` with `!`.
- `replacements` run after transcribing, are case-insensitive and match whole words.
- A bigger `model` (`medium`) improves names and technical terms at the cost of speed.

## Requirements

- Plasma 6 with `xdg-desktop-portal-kde` (GlobalShortcuts portal)
- [`uv`](https://docs.astral.sh/uv/), `portaudio`, `wl-clipboard`, `libnotify`

```sh
sudo pacman -S uv portaudio wl-clipboard libnotify
```

## How it works

```
Meta+R ─▶ KDE GlobalShortcuts portal ─▶ dicta ─▶ record ─▶ faster-whisper ─▶ wl-copy ─▶ RemoteDesktop portal (Ctrl+Shift+V)
```

- `src/dicta/shortcut.py`: registers the shortcut through the portal over D-Bus.
- `src/dicta/tray.py`: tray icon through the StatusNotifierItem protocol.
- `src/dicta/config.py`: loads `~/.config/dicta/config.toml` and writes its template.
- `src/dicta/format.py`: capitalization, final punctuation and whitespace rules.
- `src/dicta/audio.py`: in-memory microphone capture (16 kHz mono).
- `src/dicta/stt.py`: transcription with faster-whisper (CPU, int8) with hotwords, initial prompt and replacements. The model stays loaded.
- `src/dicta/output.py`: copies the text to the clipboard with `wl-copy` and shows one notification that updates in place.
- `src/dicta/keyboard.py`: pastes by sending keys through the RemoteDesktop portal. The permission token is stored in `~/.local/state/dicta/`.
- `src/dicta/portal.py`: helpers shared by the portal clients.
- `contrib/me.dicta.Dicta.desktop`: the portal identifies the app through this file. `dicta.sh` installs it into `~/.local/share/applications`.

## Future improvements

- Stop automatically after a pause in speech.
- Custom dictionary and voice commands ("new line", "period").
