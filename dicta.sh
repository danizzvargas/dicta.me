#!/bin/bash
# Run Dicta in the foreground. Stop it with Ctrl+C.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The desktop portal identifies the app through its .desktop file, whose Exec
# must be an existing executable. Install it pointing at this script.
DESKTOP_SRC="$SCRIPT_DIR/contrib/me.dicta.Dicta.desktop"
DESKTOP_DST="${XDG_DATA_HOME:-$HOME/.local/share}/applications/me.dicta.Dicta.desktop"
DESKTOP_CONTENT="$(sed "s|@EXEC@|$SCRIPT_DIR/dicta.sh|" "$DESKTOP_SRC")"
if [ "$(cat "$DESKTOP_DST" 2>/dev/null)" != "$DESKTOP_CONTENT" ]; then
    mkdir -p "$(dirname "$DESKTOP_DST")"
    printf '%s\n' "$DESKTOP_CONTENT" > "$DESKTOP_DST"
fi

cd "$SCRIPT_DIR" && exec uv run dicta "$@"
