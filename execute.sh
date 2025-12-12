#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_DIR="$SCRIPT_DIR/whisper.cpp"
PID_FILE="/tmp/whisper-server.pid"

# Check if server is running, start if not
if ! curl -s http://localhost:8080/ > /dev/null; then
    echo "Starting whisper server..."
    cd "$WHISPER_DIR"
    LD_LIBRARY_PATH=build/src:$LD_LIBRARY_PATH nohup ./build/bin/whisper-server -m models/ggml-base.bin -l auto -t 8 > /tmp/whisper-server.log 2>&1 &
    echo $! > "$PID_FILE"

    # Wait for server
    for i in {1..10}; do
        sleep 1
        curl -s http://localhost:8080/ > /dev/null && { echo "Server started"; break; }
    done
fi

RECORDING_STATE="/tmp/dictation-recording.state"
AUDIO_FILE="/tmp/dictation.wav"

# Check if already recording
if [ -f "$RECORDING_STATE" ]; then
    # Stop recording
    ARECORD_PID=$(cat "$RECORDING_STATE")
    kill $ARECORD_PID 2>/dev/null
    wait $ARECORD_PID 2>/dev/null
    rm "$RECORDING_STATE"

    notify-send "Dictation" "Processing..."

    # Send to whisper.cpp server and extract text
    RESPONSE=$(curl -s -F "file=@$AUDIO_FILE" http://localhost:8080/inference)
    TRANSCRIPTION=$(echo "$RESPONSE" | jq -r '.text' 2>/dev/null)

    if [ -n "$TRANSCRIPTION" ]; then
        echo "$TRANSCRIPTION" | wl-copy
        notify-send "Dictation" "Copied to clipboard"
    else
        notify-send "Dictation" "Error: No transcription"
    fi

    rm $AUDIO_FILE
else
    # Start recording
    notify-send "Dictation" "Recording... (Press shortcut again to stop)"
    arecord -f cd -D pipewire $AUDIO_FILE 2>/tmp/arecord-error.log &
    RECORDING_PID=$!
    echo $RECORDING_PID > "$RECORDING_STATE"

    # Check if process started
    sleep 0.5
    if ! ps -p $RECORDING_PID > /dev/null; then
        notify-send "Dictation" "Recording failed!"
        cat /tmp/arecord-error.log
    fi
fi
