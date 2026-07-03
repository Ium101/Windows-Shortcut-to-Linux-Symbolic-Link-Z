# Lnk2SymLnk v1.0.0

> Batch-convert Windows `.lnk` shortcut files into real Linux symbolic links, through a dark PyQt6 interface built for KDE and GNOME.

![Convert tab](docs/screenshot_convert.png)

---

## What's new in v1.0.0

This is the initial public release.

### Core conversion engine
- Parses `.lnk` files via `pylnk3`, with a multi-candidate path resolver that handles shortcuts built by different Windows versions, backup tools, and shell integrations (including `%ROOT%`, `%USERPROFILE%`, device-namespace prefixes, and UNC paths)
- Maps any number of Windows drive letters to their Linux mount points
- Places each symlink next to its `.lnk` source file, named after the shortcut stem

### GUI
- Folder scan triggers automatically after folder selection — no extra click needed
- Single-file mode: browse and convert one `.lnk` directly
- Drive mapping rows appear only for the letters actually found in the scanned set
- Dry-run checkbox lets you preview the full conversion plan before writing anything
- Results tree shows shortcut name, sub-folder path, Windows target, drive letter, and status — color-coded green/yellow/red
- Timestamped activity log in a dedicated Log tab with monospace, colored output
- Theme follows the system light/dark preference automatically (Catppuccin Mocha palette in dark mode)
- EN-US / PT-BR language toggle, remembered between sessions

![Log tab](docs/screenshot_log.png)

### CLI
- `--no-gui` flag for headless or scripted use
- `--mount LETTER:PATH` for drive mapping on the command line
- `--dry-run`, `--no-recurse`, `--lang` flags

### Settings
- Config stored as `lnk2symlnk_config_linux.ini` (INI format) next to the script for full portability
- Remembers last folder, drive mappings, language, and recursive toggle

### Build & install (`build.sh`)
- Generates a self-contained `Lnk2SymLnk` launcher that auto-installs `pylnk3` and `PyQt6` on first run
- Installs a `.desktop` entry, scalable SVG icon, and `.lnk` MIME association into `~/.local/share/`
- Correctly handles both `./build.sh` (normal user) and `sudo ./build.sh` (`$SUDO_USER` detection)
- Ends with a file-existence and syntax self-check before reporting success
- Refreshes the KDE menu cache (`kbuildsycoca6` / `kbuildsycoca5`) automatically

---

## Installing

**Dependencies** are fetched automatically on first run. To install them ahead of time:

| Distro | Command |
|---|---|
| Ubuntu / Debian / KDE Neon | `sudo apt install python3-pyqt6 python3-pip` |
| Fedora / RHEL | `sudo dnf install python3-pyqt6 python3-pip` |
| Arch / Manjaro | `sudo pacman -S python-pyqt6 python-pip` |

Then run the build script (as your normal user):

```bash
chmod +x build.sh && ./build.sh
```

Or just run the script directly without installing:

```bash
python3 lnk2symlink.py
```

---

## Requirements

- Python 3.10+
- PyQt6 and pylnk3 (installed automatically on first run)

---

## Files in this release

| File | Description |
|---|---|
| `lnk2symlink.py` | Main program (GUI + CLI) |
| `build.sh` | Launcher builder and system installer |
| `README.md` | Full documentation |

---

Made by **Ium101**
