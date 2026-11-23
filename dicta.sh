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

# Install the tray and notification icons into the user icon theme.
ICON_DST="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DST"
ICONS_CHANGED=0
for icon in "$SCRIPT_DIR"/contrib/icons/*.svg; do
    if ! cmp -s "$icon" "$ICON_DST/$(basename "$icon")"; then
        # Remove first: Plasma refreshes its icon cache by directory mtime,
        # which overwriting a file in place does not change.
        rm -f "$ICON_DST/$(basename "$icon")"
        cp "$icon" "$ICON_DST/"
        ICONS_CHANGED=1
    fi
done
[ "$ICONS_CHANGED" = 1 ] && touch "$ICON_DST/.." "$ICON_DST/../.."

cd "$SCRIPT_DIR" && exec uv run dicta "$@"
