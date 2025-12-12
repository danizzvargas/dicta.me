#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_DIR="$SCRIPT_DIR/whisper.cpp"
PID_FILE="/tmp/whisper-server.pid"

# Check if server is running, start if not
if ! curl -s http://localhost:8080/ > /dev/null; then
    echo "Starting whisper server..."
    cd "$WHISPER_DIR"
    LD_LIBRARY_PATH=build/src:$LD_LIBRARY_PATH nohup ./build/bin/whisper-server -m models/ggml-base.bin -l es -t 8 > /tmp/whisper-server.log 2>&1 &
    echo $! > "$PID_FILE"

    # Wait for server
    for i in {1..10}; do
        sleep 1
        curl -s http://localhost:8080/ > /dev/null && { echo "Server started"; break; }
    done
fi

AUDIO_FILE="/tmp/dictation_$(date +%s).wav"

notify-send "Dictation" "Recording... (Press Enter to stop)"

# Record in background without time limit
arecord -f cd -D pipewire -q $AUDIO_FILE &
ARECORD_PID=$!

# Wait for Enter key
read -r

# Stop recording
kill $ARECORD_PID
wait $ARECORD_PID 2>/dev/null

notify-send "Dictation" "Processing..."

# Send to whisper.cpp server and extract text
TRANSCRIPTION=$(curl -s -F "file=@$AUDIO_FILE" http://localhost:8080/inference | grep -o '"text":"[^"]*"' | cut -d'"' -f4)

echo "Transcription: $TRANSCRIPTION"
echo "$TRANSCRIPTION" | wl-copy
notify-send "Dictation" "Copied to clipboard"
rm $AUDIO_FILE
