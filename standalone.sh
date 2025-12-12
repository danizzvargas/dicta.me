#!/bin/bash
# TODO: After migrating to whisper.cpp, remove old whisper: yay -R python-openai-whisper
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
whisper $AUDIO_FILE --language es --model base --output_format txt -o /tmp/ 2>/dev/null
cat "${AUDIO_FILE%.wav}.txt" | wl-copy
notify-send "Dictation" "Copied to clipboard"
rm $AUDIO_FILE "${AUDIO_FILE%.wav}.txt"
