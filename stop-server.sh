#!/bin/bash

PID_FILE="/tmp/whisper-server.pid"

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")

    # Check if process is running
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping whisper server (PID: $PID)..."
        kill $PID
        rm "$PID_FILE"
        echo "Server stopped successfully"
    else
        echo "Process with PID $PID not found, cleaning up PID file"
        rm "$PID_FILE"
    fi
else
    # Try to find and kill whisper-server process
    WHISPER_PID=$(pgrep -f "whisper-server")

    if [ -n "$WHISPER_PID" ]; then
        echo "Found whisper-server process (PID: $WHISPER_PID), stopping..."
        kill $WHISPER_PID
        echo "Server stopped successfully"
    else
        echo "No whisper server running"
    fi
fi
