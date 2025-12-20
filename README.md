# Dicta.me

Hands-free voice input - converts speech to text to avoid typing long prompts.

## Implementation

### execute.sh (whisper.cpp) ⚡
- Uses whisper.cpp with persistent server
- Keeps model in memory
- Processing time: <1s
- Auto-starts server if not running
- Toggle recording: press once to start, press again to stop
- Copies transcribed text to clipboard
- Setup: Clone and build whisper.cpp, download model
- Run: `./execute.sh`

## Useful Commands

```sh
# Download model with multi-language support (whisper.cpp)
cd whisper.cpp
sh ./models/download-ggml-model.sh base

# Start whisper server
./build/bin/whisper-server -m models/ggml-base.bin -l es -t 8

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
4. Action: `/path/to/dicta.me/execute.sh`

## Future Improvements

- [ ] Auto-paste text at cursor position instead of clipboard
  - Requires: `yay -S ydotool` and daemon setup
  - Would eliminate manual Ctrl+V step
