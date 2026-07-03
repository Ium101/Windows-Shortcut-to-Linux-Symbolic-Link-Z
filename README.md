<div align="center">

# Lnk2SymLnk

**Converts Windows `.lnk` shortcut files into Linux symbolic links**  
Clean dark PyQt6 GUI · Bilingual EN/PT-BR · CLI fallback · Dry-run mode

</div>

---

## How it works

Windows stores shortcuts as binary `.lnk` files that Linux simply ignores.
Lnk2SymLnk reads each file, extracts the target path, maps the Windows drive
letter to its Linux mount point, and creates a native symlink in place of the
`.lnk` file — so your file manager, shell, and every other tool on Linux can
follow them normally.

---

## Features

| | |
|---|---|
| 🔍 Auto-scan | Scanning begins as soon as you pick a folder — no extra button |
| 📁 Recursive | Finds `.lnk` files buried in any depth of sub-folders |
| 🧪 Dry-run | Preview every symlink that *would* be created, nothing written to disk |
| 🗺️ Drive mapping | Map any number of Windows drive letters (`X:`, `Y:`, `Z:`, UNC…) to Linux paths |
| 📄 Single file | Browse and convert one `.lnk` directly instead of a whole folder |
| 📝 Activity log | Timestamped, color-coded output for every action (Log tab) |
| 🎨 Theme-aware | Follows your system light/dark preference; Catppuccin Mocha palette in dark mode |
| 🌐 Bilingual | EN-US / PT-BR toggle, remembered across sessions |
| 🖥️ Menu integration | Desktop entry, app-menu launcher, and `.lnk` MIME association after install |
| ⌨️ CLI mode | `--no-gui` flag for scripting and headless use |

---

## Requirements

- Python 3.10+
- PyQt6 (`pip install PyQt6`)
- pylnk3 (`pip install pylnk3`) — installed automatically on first run

GTK3 bindings are **not** required; the GUI is pure PyQt6.

---

## Quick start

### Run without installing

```bash
python3 lnk2symlink.py
```

Dependencies (`PyQt6`, `pylnk3`) are fetched automatically on the first run if
they are not already present.

### Build & install (system-wide)

```bash
chmod +x build.sh && ./build.sh
```

Run as your normal user — **not** with `sudo`. The script asks for your password
only for the two steps that actually need root: copying files into `/opt/` and
placing the launcher in `/usr/local/bin/`. Everything else (desktop entry, icon,
MIME registration) lands in `~/.local/share/`, scoped to your account.

If you do run `sudo ./build.sh`, it detects the real user via `$SUDO_USER` and
still writes those files to your home directory, not root's.

**After install, the build creates:**

| Path | Purpose |
|---|---|
| `/opt/wsl-symlink/` | Program files |
| `/usr/local/bin/wsl-symlink` | Launcher in `$PATH` |
| `~/.local/share/applications/Lnk2SymLnk.desktop` | App menu entry (KDE, GNOME, …) |
| `~/.local/share/icons/lnk2symlnk.svg` | Icon |
| `lnk2symlnk_config_linux.ini` | Settings (created next to the script on first run) |

The build finishes with a self-check that confirms the files landed and the
Python source is syntactically valid before declaring success.

---

## CLI usage

```
python3 lnk2symlink.py --no-gui [DIR]
  --dry-run / -n       Preview only, no symlinks created
  --mount LETTER:PATH  Map a drive letter, e.g. -m X:/mnt/disk1
  --no-recurse         Scan top-level folder only
  --lang pt            Portuguese output
  --help               All options
```

---

## Settings file

Settings are saved next to the script as `lnk2symlnk_config_linux.ini`
(or `_windows.ini` on Windows), so the program is fully portable — move
the folder and your preferences travel with it.

```ini
[main]
last_folder = /mnt/sda1/Users/Casa/Links
lang = en
recursive = true

[drive_map]
x = /mnt/Disco_Local1
y = /run/media/x/Seagate1
z = /mnt/Disco_Local
```

If a legacy `.json` config exists from an older version it is read
automatically and migrated to `.ini` on the next save.

---

## Project layout

```
lnk2symlink.py              Main script (GUI + CLI in one file)
build.sh                    Builds the launcher and installs desktop integration
Lnk2SymLnk                 Generated launcher (created by build.sh)
lnk2symlnk_config_linux.ini Settings (created on first run)
```

---

## License and Credits

GNU AGPLv3

Made by **Ium101**
