#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  build.sh  —  Installs deps and creates shortcuts for lnk2symlink.py
#  Run:    chmod +x build.sh && ./build.sh
# ─────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

echo
echo " =========================================="
echo "  Lnk2SymLnk  --  Linux / KDE build"
echo "  Made by Ium101"
echo " =========================================="
echo

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN="$SCRIPT_DIR/lnk2symlink.py"

if [[ ! -f "$MAIN" ]]; then
    echo " ERROR: lnk2symlink.py not found in $SCRIPT_DIR" >&2
    exit 1
fi

# ── Require Python 3.10+ ─────────────────────────────────────────
PYTHON=""
for candidate in python3 python3.13 python3.12 python3.11 python3.10 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c 'import sys; print(sys.version_info >= (3,10))' 2>/dev/null)
        if [[ "$ver" == "True" ]]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo " ERROR: Python 3.10+ not found in PATH." >&2
    echo "        Install via your package manager:" >&2
    echo "          Debian/Ubuntu:  sudo apt install python3" >&2
    echo "          Fedora/RHEL:    sudo dnf install python3" >&2
    echo "          Arch:           sudo pacman -S python" >&2
    exit 1
fi

PYVER=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo " Found: $PYTHON  (Python $PYVER)"

# ── Install dependencies ──────────────────────────────────────────
echo " Installing dependencies (pylnk3, PyQt6)..."
if ! "$PYTHON" -m pip install --quiet --upgrade pylnk3 PyQt6 2>/dev/null; then
    "$PYTHON" -m pip install --quiet --upgrade --break-system-packages pylnk3 PyQt6
fi
echo " OK   Dependencies installed."

# ── Make lnk2symlink.py directly executable ───────────────────────
chmod +x "$MAIN"
echo " OK   $MAIN is now executable."

# ── Directories ──────────────────────────────────────────────────
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")
mkdir -p "$APP_DIR" "$ICON_DIR" "$DESKTOP_DIR"

# ── Icon — installed directly into ~/.local/share/icons/ ─────────
echo " Installing icon..."
ICON_FILE="$ICON_DIR/lnk2symlnk.svg"
cat > "$ICON_FILE" << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="256" height="256">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"  stop-color="#6C7DF2"/>
      <stop offset="100%" stop-color="#3A47B8"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="62" height="62" rx="14" ry="14" fill="url(#bg)"/>
  <rect x="1" y="1" width="62" height="28" rx="14" ry="14" fill="#FFFFFF" opacity="0.08"/>
  <path fill="#FFFFFF" d="
    M 52.0 31.77
    L 34.79 15.02
    L 34.68 24.25
    C 33.92 24.44 31.55 24.93 30.12 25.39
    C 28.70 25.85 27.42 26.34 26.13 26.99
    C 24.84 27.63 23.62 28.35 22.37 29.26
    C 21.12 30.17 19.75 31.28 18.61 32.46
    C 17.47 33.64 16.42 34.92 15.53 36.33
    C 14.64 37.73 13.82 39.35 13.25 40.89
    C 12.68 42.43 12.32 44.21 12.11 45.56
    C 11.90 46.91 12.02 48.41 12.00 48.98
    C 13.10 48.14 16.67 45.24 18.61 43.97
    C 20.55 42.70 22.03 42.01 23.62 41.34
    C 25.21 40.68 26.58 40.32 28.18 39.98
    C 29.78 39.64 32.12 39.37 33.20 39.29
    C 34.28 39.21 34.43 39.48 34.68 39.52
    L 34.91 48.87
    Z
  "/>
</svg>
SVGEOF
# NOTE: this is a flat install into ~/.local/share/icons/ rather than the
# hicolor theme path (~/.local/share/icons/hicolor/scalable/apps/). Bare-name
# Icon= lookups (e.g. Icon=lnk2symlnk with no path) rely on icon-theme search
# rules and may NOT find a flat file here on every desktop environment, so
# both .desktop entries below use the full path to "$ICON_FILE" to guarantee
# the icon shows up regardless of theme lookup behavior.

# ── System menu .desktop ───────────────────────────────────────────
echo " Adding to system menu..."
cat > "$APP_DIR/Lnk2SymLnk.desktop" << DESKTOPEOF
[Desktop Entry]
Name=Lnk2SymLnk
Comment=Convert Windows .lnk shortcuts to Linux symlinks
Exec=$MAIN
Icon=$ICON_FILE
Terminal=false
Type=Application
Categories=Utility;
DESKTOPEOF
chmod +x "$APP_DIR/Lnk2SymLnk.desktop"

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$APP_DIR" &>/dev/null
fi

# ── Desktop shortcut ────────────────────────────────────────────────
echo " Creating desktop shortcut..."
cat > "$DESKTOP_DIR/Lnk2SymLnk.desktop" << DESKTOPEOF
[Desktop Entry]
Name=Lnk2SymLnk
Comment=Convert Windows .lnk shortcuts to Linux symlinks
Exec=$MAIN
Icon=$ICON_FILE
Terminal=false
Type=Application
Categories=Utility;
DESKTOPEOF
chmod 755 "$DESKTOP_DIR/Lnk2SymLnk.desktop"

if command -v gio &>/dev/null; then
    gio set "$DESKTOP_DIR/Lnk2SymLnk.desktop" metadata::trusted true 2>/dev/null
fi

# ── KDE menu cache ───────────────────────────────────────────────
echo " Refreshing menu cache..."
if command -v kbuildsycoca6 &>/dev/null; then
    kbuildsycoca6 &>/dev/null
elif command -v kbuildsycoca5 &>/dev/null; then
    kbuildsycoca5 &>/dev/null
fi

echo
echo " =========================================="
echo "  Build complete!"
echo " =========================================="
echo
echo "  Script:   $MAIN"
echo "  Menu:     $APP_DIR/Lnk2SymLnk.desktop"
echo "  Desktop:  $DESKTOP_DIR/Lnk2SymLnk.desktop"
echo "  Settings: $SCRIPT_DIR/lnk2symlnk_config_linux.ini  (created on first run)"
echo
echo " To run:"
echo "    ./lnk2symlink.py                      # open GUI"
echo "    ./lnk2symlink.py --no-gui [DIR]       # CLI mode"
echo "    ./lnk2symlink.py --lang pt            # Portuguese UI"
echo "    ./lnk2symlink.py --help               # all options"
echo
