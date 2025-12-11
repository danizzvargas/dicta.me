# Voice Dictation Project

Hands-free voice input - converts speech to text to avoid typing long prompts.

## Two Implementations

### 1. dictate.sh (openai-whisper)
- Uses Python-based whisper
- Loads model on every transcription
- Processing time: ~5-10s
- Install: `yay -S python-openai-whisper wl-clipboard libnotify`
- Run: `./dictate.sh`

### 2. dictate-server.sh (whisper.cpp) ⚡
- Uses whisper.cpp with persistent server
- Keeps model in memory
- Processing time: <1s
- Setup: Clone and build whisper.cpp, download model
- Start server, then run: `./dictate-server.sh`

## Useful Commands

```sh
# Download model with multi-language support (whisper.cpp)
cd whisper.cpp
sh ./models/download-ggml-model.sh base

# Start whisper server
./build/bin/whisper-server -m models/ggml-base.bin -l es

# Test audio recording
arecord -f cd -d 5 -D pipewire /tmp/test.wav
aplay /tmp/test.wav

# Test transcription
curl -F "file=@/tmp/test.wav" http://localhost:8080/inference
```

## KDE Shortcut Setup

1. System Settings → Shortcuts → Custom Shortcuts
2. Edit → New → Global Shortcut → Command/URL
3. Trigger: Set your key (e.g., `Meta+D`)
4. Action: `konsole -e /home/danizz/dev/projects/whisper/dictate-server.sh`
