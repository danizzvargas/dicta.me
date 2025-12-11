#!/bin/bash
curl -s http://localhost:8080/ > /dev/null || { echo "Server not running"; exit 1; }
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
