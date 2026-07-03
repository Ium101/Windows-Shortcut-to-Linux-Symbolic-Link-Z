#!/usr/bin/env python3
"""
Windows Shortcut to Linux Symbolic Link Z — Convert Windows .lnk shortcuts to Linux symbolic links.
GUI: PyQt6 (native Dolphin file picker via kdialog / XDG portal on KDE).
CLI: pass --no-gui
Made by Ium101
"""

import os, sys, re, json, argparse, subprocess, configparser
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# ── Dependency bootstrap ───────────────────────────────────────
def _pip(*pkgs, extra=[]):
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade"] + list(pkgs) + extra,
        stderr=subprocess.DEVNULL)

def _ensure(pkg, import_name=None):
    name = import_name or pkg
    try:
        __import__(name); return True
    except ImportError:
        pass
    for extra in [[], ["--break-system-packages"]]:
        try:
            _pip(pkg, extra=extra); __import__(name); return True
        except Exception:
            pass
    return False

_HAVE_PYLNK3 = _ensure("pylnk3")
if _HAVE_PYLNK3:
    import pylnk3

# ── i18n ──────────────────────────────────────────────────────
_S = {
"en": dict(
    title="Windows Shortcut to Linux Symbolic Link Z", credit="Made by Ium101",
    lang_toggle="PT-BR",        # label shown when current lang is EN (click to switch to PT)
    theme_dark="☀  Light",     # button label shown while in dark mode (click → go light)
    theme_light="🌙  Dark",    # button label shown while in light mode (click → go dark)
    folder_label="Folder to scan:", browse="Browse Folder…", browse_file="Browse File…",
    drives_title="Drive mapping",
    drives_hint="Map each Windows drive letter to its Linux mount point:",
    mount_ph="Mount point for {l}:", browse_mount="Browse…",
    mount_unc="Mount point for network shares:",
    recursive="Scan sub-folders",
    dry="Dry run (preview only)", convert="Convert",
    tab_main="Convert", tab_log="Log",
    col_file="Shortcut", col_path="Path", col_target="Windows target",
    col_drive="Drive", col_status="Status",
    ready="Ready.", scanning="Scanning…",
    done="Done — created: {c}  skipped: {s}  errors: {e}",
    done_dry="[DRY RUN] Would create: {c}  skipped: {s}  errors: {e}",
    no_folder="Please select a folder first.",
    no_lnk="No .lnk files found.",
    no_pylnk3="pylnk3 could not be installed.\nRun: pip install pylnk3",
    log_scan="Scanning {r}…", log_found="Found {n} shortcut(s).",
    log_ok="✓  {lnk}  →  {tgt}",
    log_skip="–  {f} ({r})", log_err="✗  {f}: {r}",
    log_dry="[DRY RUN] Would create: {lnk}  →  {tgt}",
),
"pt": dict(
    title="Windows Shortcut to Linux Symbolic Link Z", credit="Feito por Ium101",
    lang_toggle="EN-US",        # label shown when current lang is PT (click to switch to EN)
    theme_dark="☀  Claro",     # button label shown while in dark mode
    theme_light="🌙  Escuro",  # button label shown while in light mode
    folder_label="Pasta para escanear:", browse="Escolher Pasta…", browse_file="Escolher Arquivo…",
    drives_title="Mapeamento de drives",
    drives_hint="Mapeie cada letra de drive Windows para seu ponto de montagem Linux:",
    mount_ph="Ponto de montagem para {l}:", browse_mount="Escolher…",
    mount_unc="Ponto de montagem para compartilhamentos de rede:",
    recursive="Escanear subpastas",
    dry="Simulação (apenas visualizar)", convert="Converter",
    tab_main="Converter", tab_log="Log",
    col_file="Atalho", col_path="Caminho", col_target="Destino Windows",
    col_drive="Drive", col_status="Status",
    ready="Pronto.", scanning="Escaneando…",
    done="Concluído — criados: {c}  pulados: {s}  erros: {e}",
    done_dry="[SIMULAÇÃO] Criaria: {c}  pulados: {s}  erros: {e}",
    no_folder="Por favor selecione uma pasta primeiro.",
    no_lnk="Nenhum arquivo .lnk encontrado.",
    no_pylnk3="pylnk3 não pôde ser instalado.\nExecute: pip install pylnk3",
    log_scan="Escaneando {r}…", log_found="{n} atalho(s) encontrado(s).",
    log_ok="✓  {lnk}  →  {tgt}",
    log_skip="–  {f} ({r})", log_err="✗  {f}: {r}",
    log_dry="[SIMULAÇÃO] Criaria: {lnk}  →  {tgt}",
),
}
_LANG = "en"
def T(k, **kw):
    s = _S[_LANG].get(k, _S["en"].get(k, k))
    return s.format(**kw) if kw else s

# ── Persistent config (remembers last folder / drive map / language) ──
# Saved next to this script itself (not ~/.config) so the program is fully
# self-contained / portable — settings travel with the folder it's run from.
# Windows and Linux get separate config files since drive mappings, mount
# points, and paths are never compatible between the two OSes.
_CONFIG_DIR    = Path(__file__).resolve().parent
_CONFIG_SUFFIX = "windows" if os.name == "nt" else "linux"
_CONFIG_FILE   = _CONFIG_DIR / f"lnk2symlnk_config_{_CONFIG_SUFFIX}.ini"

# Legacy JSON path — migrated transparently on first save.
_CONFIG_FILE_JSON = _CONFIG_DIR / f"lnk2symlnk_config_{_CONFIG_SUFFIX}.json"

_INI_MAIN   = "main"
_INI_DRIVES = "drive_map"

def load_config() -> dict:
    # ── 1. Try INI first ──────────────────────────────────────
    if _CONFIG_FILE.exists():
        try:
            cp = configparser.ConfigParser()
            cp.read(_CONFIG_FILE, encoding="utf-8")
            result: dict = {}
            if cp.has_option(_INI_MAIN, "last_folder"):
                result["last_folder"] = cp.get(_INI_MAIN, "last_folder")
            if cp.has_option(_INI_MAIN, "lang"):
                result["lang"] = cp.get(_INI_MAIN, "lang")
            if cp.has_option(_INI_MAIN, "recursive"):
                result["recursive"] = cp.getboolean(_INI_MAIN, "recursive")
            if cp.has_option(_INI_MAIN, "dark_mode"):
                result["dark_mode"] = cp.getboolean(_INI_MAIN, "dark_mode")
            if cp.has_section(_INI_DRIVES):
                result["drive_map"] = dict(cp.items(_INI_DRIVES))
            return result
        except Exception:
            pass

    # ── 2. Fall back to legacy JSON (migrate silently) ────────
    if _CONFIG_FILE_JSON.exists():
        try:
            with open(_CONFIG_FILE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data   # save_config() will write .ini on next save
        except Exception:
            pass

    return {}

def save_config(data: dict):
    try:
        cp = configparser.ConfigParser()
        cp[_INI_MAIN] = {}
        if "last_folder" in data:
            cp[_INI_MAIN]["last_folder"] = str(data["last_folder"])
        if "lang" in data:
            cp[_INI_MAIN]["lang"] = str(data["lang"])
        if "recursive" in data:
            cp[_INI_MAIN]["recursive"] = "true" if data["recursive"] else "false"
        if "dark_mode" in data:
            cp[_INI_MAIN]["dark_mode"] = "true" if data["dark_mode"] else "false"
        drive_map = data.get("drive_map", {})
        if drive_map:
            cp[_INI_DRIVES] = {k: str(v) for k, v in drive_map.items()}
        tmp = _CONFIG_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            cp.write(f)
        tmp.replace(_CONFIG_FILE)
    except Exception:
        pass  # best-effort only — never block the app over a settings write

# ── Core logic ─────────────────────────────────────────────────
@dataclass
class LnkEntry:
    lnk_path: Path
    windows_path: str = ""
    drive_letter: str = ""
    relative_path: str = ""
    error: Optional[str] = None
    symlink_target: Optional[Path] = None
    symlink_path: Optional[Path] = None
    status: str = "pending"

# Known %ROOT%-style tokens that pylnk3's LinkTargetIDList.get_path() can
# emit when a shortcut points at a special folder (Desktop, Documents, a
# KNOWN_FOLDER GUID, etc). These never carry a drive letter, so unless we
# resolve them to *something* path-like, every shortcut built from "Send to
# Desktop" or pinned via Quick Access fails with "bad format" even though
# its real target is perfectly recoverable from other shortcut fields.
_ROOT_TOKEN_RE = re.compile(r'^%[A-Z_]+%')

# Matches the classic Windows env-var token style: %USERPROFILE%, %windir%, etc.
_ENV_TOKEN_RE = re.compile(r'%([^%]+)%')

# \\?\ and \\.\ long-path / device-namespace prefixes that some shortcuts
# (especially ones made by backup tools or created on Server editions)
# include in front of an otherwise normal drive path.
_LONGPATH_PREFIX_RE = re.compile(r'^\\\\[?.]\\')


def _expand_env_tokens(raw: str) -> str:
    """Best-effort expansion of %VAR% tokens to something drive-letter-shaped.

    We can't know the real Windows username, so %USERPROFILE%, %HOMEPATH%,
    %APPDATA% etc. just get replaced with a literal placeholder under C: —
    this at least keeps the relative structure intact and lets the user spot
    + fix it via the drive-mapping UI, instead of the entry being dropped.
    """
    common = {
        "USERPROFILE": "C:\\Users\\%USERNAME%",
        "HOMEPATH":    "C:\\Users\\%USERNAME%",
        "APPDATA":     "C:\\Users\\%USERNAME%\\AppData\\Roaming",
        "LOCALAPPDATA":"C:\\Users\\%USERNAME%\\AppData\\Local",
        "PUBLIC":      "C:\\Users\\Public",
        "PROGRAMFILES":"C:\\Program Files",
        "PROGRAMFILES(X86)": "C:\\Program Files (x86)",
        "PROGRAMDATA": "C:\\ProgramData",
        "WINDIR":      "C:\\Windows",
        "SYSTEMROOT":  "C:\\Windows",
        "SYSTEMDRIVE": "C:",
    }
    def _sub(m):
        key = m.group(1).upper()
        return common.get(key, m.group(0))
    out = _ENV_TOKEN_RE.sub(_sub, raw)
    # USERNAME itself won't be known either; leave a single placeholder
    # segment rather than recursing forever.
    return out.replace("%USERNAME%", "_user_")


def _root_token_to_drive_path(raw: str) -> Optional[str]:
    """Turn a %ROOT%\\... style path (from LinkTargetIDList) into something
    drive-letter-shaped, same placeholder approach as _expand_env_tokens."""
    m = _ROOT_TOKEN_RE.match(raw)
    if not m:
        return None
    token = m.group(0)
    rest = raw[len(token):]
    mapping = {
        "%USERPROFILE%":   "C:\\Users\\_user_",
        "%MY_DOCUMENTS%":  "C:\\Users\\_user_\\Documents",
        "%MY_COMPUTER%":   "",   # "My Computer\C:\..." -> the rest already has the drive
    }
    repl = mapping.get(token)
    if repl is None:
        return None
    candidate = (repl + rest) if repl else rest.lstrip("\\/")
    return candidate


def _candidate_raw_paths(lnk) -> list:
    """Collect every plausible target-path string pylnk3 exposes, in the
    order we trust them. Earlier failures fall through to later candidates
    instead of giving up after the first non-matching one — this is the
    main reason some shortcuts used to convert fine while others (made by
    a different Windows version/app, or pointing at a special folder) were
    silently skipped as 'bad format'."""
    candidates = []

    path_attr = getattr(lnk, "path", None)
    if path_attr:
        candidates.append(path_attr)

    link_info = getattr(lnk, "link_info", None)
    if link_info is not None:
        for attr in ("local_base_path", "common_path_suffix"):
            val = getattr(link_info, attr, None)
            if val:
                candidates.append(val)

    # idlist / shell_item_id_list path reconstruction (covers KNOWN_FOLDER
    # and other "%ROOT%\..." forms) — pylnk3 names this attribute
    # differently across versions, so try a few.
    for idlist_attr in ("shell_item_id_list", "id_list", "_shell_item_id_list"):
        idlist = getattr(lnk, idlist_attr, None)
        if idlist is not None and hasattr(idlist, "get_path"):
            try:
                val = idlist.get_path()
                if val:
                    candidates.append(val)
            except Exception:
                pass

    string_data = getattr(lnk, "string_data", None)
    if string_data is not None:
        for attr in ("relative_path", "working_dir", "command_line_arguments"):
            val = getattr(string_data, attr, None)
            if val:
                candidates.append(val)

    # de-dupe while preserving order
    seen, out = set(), []
    for c in candidates:
        c = c.strip() if isinstance(c, str) else c
        if c and c not in seen:
            seen.add(c); out.append(c)
    return out


def _resolve_drive_and_relative(raw: str):
    """Try to turn one raw candidate string into (drive_letter, relative_path).
    Returns None if this candidate doesn't look like a usable path at all."""
    raw = raw.strip()
    if not raw:
        return None

    # Strip \\?\ / \\.\  device-namespace prefixes some tools add.
    raw = _LONGPATH_PREFIX_RE.sub("", raw)

    # Resolve %ROOT%-token forms coming from the shell id list.
    root_resolved = _root_token_to_drive_path(raw)
    if root_resolved is not None:
        raw = root_resolved

    # Expand %ENVVAR% tokens to a best-effort drive-shaped placeholder.
    if "%" in raw:
        raw = _expand_env_tokens(raw)

    raw = raw.strip()

    # UNC / network path: \\server\share\... — no drive letter involved.
    # Surface this distinctly so the UI can offer a "network share" mapping
    # instead of silently bucketing it under "bad format".
    if re.match(r'^\\\\[^\\]+\\[^\\]+', raw):
        return ("UNC", raw.replace("\\", "/").lstrip("/"))

    m = re.match(r'^([A-Za-z])[:\\/](.*)$', raw)
    if not m:
        return None
    drive = m.group(1).upper()
    rel = m.group(2).replace("\\", "/").strip("/")
    return (drive, rel)


def parse_lnk(path: Path) -> LnkEntry:
    e = LnkEntry(lnk_path=path)
    if not _HAVE_PYLNK3:
        e.error = "pylnk3 missing"; return e
    try:
        lnk = pylnk3.parse(str(path))
        candidates = _candidate_raw_paths(lnk)
        if not candidates:
            e.error = "no target path"; return e

        # Keep the first candidate around for display even if every
        # candidate ultimately fails to resolve, so the error message in
        # the UI still shows the user *something* useful to debug from.
        e.windows_path = candidates[0]

        resolved = None
        for raw in candidates:
            result = _resolve_drive_and_relative(raw)
            if result is not None:
                resolved = result
                e.windows_path = raw
                break

        if resolved is None:
            e.error = f"bad format: {candidates[0]!r}"; return e

        e.drive_letter, e.relative_path = resolved
    except Exception as ex:
        e.error = str(ex)
    return e

def find_lnk_files(root: Path, recursive: bool = True):
    """Find all .lnk files under root. When recursive=True (default) all sub-folders
    are included; when False only the immediate folder is scanned."""
    results = []
    try:
        pattern = root.rglob("*.lnk") if recursive else root.glob("*.lnk")
        for p in sorted(pattern):
            try:
                results.append(parse_lnk(p))
            except Exception as ex:
                entry = LnkEntry(lnk_path=p)
                entry.error = str(ex)
                results.append(entry)
    except PermissionError:
        pass
    return results

def plan(entries, drive_map):
    for e in entries:
        if e.error:
            e.status = "error"; continue
        mount = drive_map.get(e.drive_letter)
        if not mount:
            if e.drive_letter == "UNC":
                e.error = "network share: not mapped"
            else:
                e.error = f"drive {e.drive_letter}: not mapped"
            e.status = "skipped"; continue
        # relative_path is already slash-normalised and stripped of leading slash
        e.symlink_target = mount / Path(e.relative_path)
        # Place symlink next to the .lnk file (same directory), named stem only
        e.symlink_path   = e.lnk_path.parent / e.lnk_path.stem

def do_symlink(e: LnkEntry, dry: bool):
    link, tgt = e.symlink_path, e.symlink_target
    if link.exists() or link.is_symlink():
        if link.is_symlink() and link.resolve() == tgt:
            e.status = "skipped"; e.error = "already exists"
        else:
            e.status = "skipped"; e.error = f"path exists: {link.name}"
        return
    if dry:
        e.status = "created"; return
    try:
        link.symlink_to(tgt); e.status = "created"
    except OSError as ex:
        e.status = "error"; e.error = str(ex)

def list_mounts():
    try:
        out = subprocess.check_output(
            ["lsblk", "-o", "MOUNTPOINT,LABEL,SIZE", "--noheadings", "--json"],
            text=True, stderr=subprocess.DEVNULL)
        data = json.loads(out)
        results = []
        def walk(devs):
            for d in devs:
                mp = d.get("mountpoint","")
                if mp and mp != "[SWAP]":
                    lbl = d.get("label","") or ""
                    sz  = d.get("size","") or ""
                    results.append((mp, lbl, sz))
                for c in d.get("children",[]):
                    walk([c])
        walk(data.get("blockdevices",[]))
        return results
    except Exception:
        return []


# ── Dolphin / native file picker ──────────────────────────────

def _ensure_dbus_env():
    """
    Ensure DBUS_SESSION_BUS_ADDRESS is set in os.environ so that both
    out-of-process tools (kdialog, zenity) and Qt's own platform-plugin
    D-Bus connection can reach the running desktop session.

    Without this, launching via a .desktop shortcut or file manager often
    leaves DBUS_SESSION_BUS_ADDRESS unset, which silently breaks kdialog
    and the xdg-desktop-portal route inside Qt.
    """
    if os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        return
    uid = os.getuid()
    socket_path = f"/run/user/{uid}/bus"
    if Path(socket_path).exists():
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={socket_path}"
        return
    try:
        for pid_dir in Path("/proc").iterdir():
            if not pid_dir.name.isdigit():
                continue
            try:
                name = (pid_dir / "comm").read_text().strip()
            except OSError:
                continue
            if name not in ("plasmashell", "gnome-shell", "kwin_wayland",
                            "kwin_x11", "mutter", "xfwm4"):
                continue
            try:
                raw = (pid_dir / "environ").read_bytes()
                for item in raw.split(b"\x00"):
                    if item.startswith(b"DBUS_SESSION_BUS_ADDRESS="):
                        os.environ["DBUS_SESSION_BUS_ADDRESS"] = \
                            item.split(b"=", 1)[1].decode()
                        return
            except OSError:
                continue
    except OSError:
        pass


def _is_kde() -> bool:
    desk = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    return "kde" in desk or "plasma" in desk


def _set_kfilewidget_icon_view():
    """
    Write the correct KDE config keys so kdialog opens KFileWidget in
    icon/thumbnail view instead of tree or list view.

    Confirmed from KDE source (kfilewidget.cpp):
      File:    ~/.config/kdeglobals
      Group:   [KFileWidget]          ← NOT [KFileDialog Settings]
      Keys:
        View Style=Simple             Simple=icon grid, Detailed=list, Tree=tree
        Show Previews=true            enable thumbnail previews inside the dialog
        Preview Size=128              thumbnail size in pixels

    We only write keys that differ from what is already stored so we never
    permanently override a user's deliberate preference — the next time the
    user changes view mode inside the dialog, KDE overwrites these values.
    """
    try:
        cfg_path = Path.home() / ".config" / "kdeglobals"
        lines    = cfg_path.read_text(encoding="utf-8").splitlines() if cfg_path.exists() else []

        # Desired keys in [KFileWidget]
        wanted = {
            "View Style":    "Simple",
            "Show Previews": "true",
            "Preview Size":  "128",
        }

        # Parse into sections: dict of section_name -> list of (key, value) / comment lines
        sections: dict[str, list] = {}
        order:    list[str]       = []
        cur = "__preamble__"
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                cur = stripped[1:-1]
                if cur not in sections:
                    sections[cur] = []
                    order.append(cur)
            else:
                if cur not in sections:
                    sections[cur] = []
                    if cur not in order:
                        order.append(cur)
                sections[cur].append(line)

        target = "KFileWidget"
        if target not in sections:
            sections[target] = []
            order.append(target)

        # Update or insert each wanted key in the target section
        for want_key, want_val in wanted.items():
            found = False
            for i, line in enumerate(sections[target]):
                if line.strip().startswith(want_key + "="):
                    current_val = line.strip().split("=", 1)[1]
                    if current_val != want_val:
                        sections[target][i] = f"{want_key}={want_val}"
                    found = True
                    break
            if not found:
                sections[target].append(f"{want_key}={want_val}")

        # Reconstruct file
        out_lines = []
        for sec in order:
            if sec == "__preamble__":
                out_lines.extend(sections[sec])
            else:
                out_lines.append(f"[{sec}]")
                out_lines.extend(sections[sec])

        cfg_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    except OSError:
        pass   # not fatal — kdialog will still open, just may not be icon view


def _pick_folder_dolphin(parent_widget, title: str, start_dir: str) -> Optional[str]:
    """
    Open the native KDE folder picker in icon/thumbnail view — the one with
    the Places panel, navigation bar, and folder icon grid shown in the
    reference screenshot.

    How view mode works in KDE:
      kdialog reads ~/.config/kdeglobals [KFileWidget] View Style
      to decide which view to open in.  "Simple" = icon/thumbnail grid.
      We write that setting before calling kdialog so it always opens in
      icon view regardless of what the user last had it set to.

    Method cascade — first that returns non-None wins.
    None = user cancelled (stop). Exception = method unavailable (try next).

      1. kdialog --getexistingdirectory  (KDE — icon view via kdeglobals preset)
         Reliable, always opens on KDE/BigLinux, uses the real KFileWidget.
         Pre-setting View Style=Simple ensures icon/thumbnail view.

      2. QFileDialog with app stylesheet cleared  (KDE — KFileWidget in-process)
         Clearing our global QSS lets Qt delegate QFileDialog to the KDE
         platform plugin (KFileWidget).  Stylesheet is restored immediately after.

      3. zenity --file-selection --directory  (GNOME / GTK desktops)

      4. QFileDialog via xdg-desktop-portal  (any desktop with portal running)

      5. QFileDialog built-in  (universal last resort)
    """
    from PyQt6.QtWidgets import QFileDialog, QApplication

    _ensure_dbus_env()

    if not start_dir or not Path(start_dir).exists():
        start_dir = str(Path.home())

    start_uri = Path(start_dir).as_uri()

    def _decode_uri(raw: str) -> Optional[str]:
        raw = raw.strip()
        if not raw:
            return None
        if raw.startswith("file://"):
            from urllib.parse import unquote
            raw = unquote(raw[7:])
        p = Path(raw)
        if p.is_dir():
            return str(p)
        if p.exists():
            return str(p.parent)
        return None

    # ── Method 1: kdialog --getexistingdirectory with icon view preset ───────
    # Pre-set KFileWidget view mode to Simple (icon/thumbnail grid) in kdeglobals
    # so kdialog opens in icon view.  This is the exact same setting the view
    # mode buttons in the top-right of the dialog write when the user clicks them.
    _set_kfilewidget_icon_view()
    for kdialog_bin in ("kdialog", "kdialog6"):
        try:
            result = subprocess.run(
                [kdialog_bin, "--title", title,
                 "--getexistingdirectory", start_uri],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                chosen = _decode_uri(result.stdout)
                if chosen:
                    return chosen
            # rc=1 = user cancelled — don't open another dialog on top
            return None
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return None

    # ── Method 2: QFileDialog with app stylesheet cleared (KDE in-process) ──
    # Our app's global QSS blocks Qt from delegating to the KDE platform plugin.
    # Temporarily clearing it lets Qt route QFileDialog through KFileWidget.
    if _is_kde():
        _app       = QApplication.instance()
        _saved_qss = _app.styleSheet() if _app else ""
        _orig_env  = os.environ.get("QT_QPA_PLATFORMTHEME")
        try:
            os.environ["QT_QPA_PLATFORMTHEME"] = "kde"
            if _app:
                _app.setStyleSheet("")
            dlg = QFileDialog(parent_widget)
            dlg.setWindowTitle(title)
            dlg.setFileMode(QFileDialog.FileMode.Directory)
            dlg.setDirectory(start_dir)
            dlg.setOption(QFileDialog.Option.DontUseNativeDialog, False)
            accepted = dlg.exec()
            if accepted:
                dirs = dlg.selectedFiles()
                if dirs:
                    chosen = dirs[0]
                    if Path(chosen).is_dir():
                        return chosen
                    p = str(Path(chosen).parent)
                    if Path(p).is_dir():
                        return p
            else:
                return None
        except Exception:
            pass
        finally:
            if _app and _saved_qss:
                _app.setStyleSheet(_saved_qss)
            if _orig_env is None:
                os.environ.pop("QT_QPA_PLATFORMTHEME", None)
            else:
                os.environ["QT_QPA_PLATFORMTHEME"] = _orig_env

    # ── Method 3: zenity (GNOME / GTK desktops) ────────────────────────────
    try:
        result = subprocess.run(
            ["zenity", "--title", title, "--file-selection", "--directory",
             f"--filename={start_dir}/"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            chosen = result.stdout.strip()
            if chosen and Path(chosen).is_dir():
                return chosen
        if result.returncode in (0, 1):
            return None
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        pass

    # ── Method 4: QFileDialog via xdg-desktop-portal ───────────────────────
    try:
        dlg = QFileDialog(parent_widget)
        dlg.setWindowTitle(title)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        dlg.setDirectory(start_dir)
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, False)
        if dlg.exec():
            dirs = dlg.selectedFiles()
            if dirs and Path(dirs[0]).is_dir():
                return dirs[0]
        return None
    except Exception:
        pass

    # ── Method 5: QFileDialog built-in (always works, no thumbnails) ───────
    chosen = QFileDialog.getExistingDirectory(
        parent_widget, title, start_dir,
        QFileDialog.Option.ShowDirsOnly
    )
    return chosen if chosen else None

# ── GUI ────────────────────────────────────────────────────────
def run_gui():
    global _LANG
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QCheckBox, QTabWidget,
        QTreeWidget, QTreeWidgetItem, QScrollArea, QComboBox,
        QTextEdit, QStatusBar, QFrame, QSizePolicy, QFileDialog,
        QMessageBox, QGroupBox, QSplitter
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QDir
    from PyQt6.QtGui import QFont, QColor, QPalette, QTextCharFormat, QTextCursor, QIcon
    import base64

    app = QApplication(sys.argv)
    app.setApplicationName("Windows Shortcut to Linux Symbolic Link Z")

    _cfg = load_config()
    if _cfg.get("lang") in ("en", "pt"):
        _LANG = _cfg["lang"]

    # ── Detect system light/dark theme ────────────────────────
    def _detect_dark_mode() -> bool:
        """Best-effort detection of the desktop's color scheme, so the app
        (and the in-app folder picker fallback) matches the system instead
        of always forcing the same hardcoded look. Tries several signals,
        most to least reliable, and defaults to dark if everything fails."""
        # 1. Qt 6.5+ exposes the resolved scheme straight from the platform
        #    theme plugin — most reliable when it works (KDE6, some GNOME).
        try:
            from PyQt6.QtCore import Qt as _Qt
            scheme = app.styleHints().colorScheme()
            if scheme == _Qt.ColorScheme.Dark:
                return True
            if scheme == _Qt.ColorScheme.Light:
                return False
        except Exception:
            pass

        # 2. KDE Plasma: read the active color scheme out of kdeglobals.
        try:
            result = subprocess.run(
                ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
                capture_output=True, text=True, timeout=2
            )
            scheme = (result.stdout or "").strip().lower()
            if scheme:
                return "dark" in scheme or "breeze dark" in scheme
        except Exception:
            pass
        try:
            result = subprocess.run(
                ["kreadconfig6", "--group", "General", "--key", "ColorScheme"],
                capture_output=True, text=True, timeout=2
            )
            scheme = (result.stdout or "").strip().lower()
            if scheme:
                return "dark" in scheme
        except Exception:
            pass

        # 3. GNOME / GTK: gsettings color-scheme key.
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, timeout=2
            )
            out = (result.stdout or "").strip().lower()
            if out:
                return "dark" in out
        except Exception:
            pass

        # 4. Fallback: inspect the default (unmodified) application palette —
        #    if the window background is darker than the text, the
        #    underlying platform theme is already dark before we touch it.
        try:
            base_pal = app.palette()
            win_color = base_pal.color(QPalette.ColorRole.Window)
            return win_color.lightness() < 128
        except Exception:
            pass

        return True  # last resort: keep the original dark look

    # ── Honour saved theme preference, fall back to system detection ──
    _cfg_startup = load_config()
    if "dark_mode" in _cfg_startup:
        _dark_mode_state = [_cfg_startup["dark_mode"]]
    else:
        _dark_mode_state = [_detect_dark_mode()]

    # ── Set window icon from bundled SVG ──────────────────────
    _icon_svg_b64 = (
        "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NCA2"
        "NCIgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0Ij4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBp"
        "ZD0iYmciIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgogICAgICA8c3RvcCBv"
        "ZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNkM3REYyIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAw"
        "JSIgc3RvcC1jb2xvcj0iIzNBNDdCOCIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICA8L2RlZnM+"
        "CiAgPHJlY3QgeD0iMSIgeT0iMSIgd2lkdGg9IjYyIiBoZWlnaHQ9IjYyIiByeD0iMTQiIHJ5PSIx"
        "NCIgZmlsbD0idXJsKCNiZykiLz4KICA8cmVjdCB4PSIxIiB5PSIxIiB3aWR0aD0iNjIiIGhlaWdo"
        "dD0iMjgiIHJ4PSIxNCIgcnk9IjE0IiBmaWxsPSIjRkZGRkZGIiBvcGFjaXR5PSIwLjA4Ii8+CiAg"
        "PHBhdGggZmlsbD0iI0ZGRkZGRiIgZD0iCiAgICBNIDUyLjAgMzEuNzcKICAgIEwgMzQuNzkgMTUu"
        "MDIKICAgIEwgMzQuNjggMjQuMjUKICAgIEMgMzMuOTIgMjQuNDQgMzEuNTUgMjQuOTMgMzAuMTIg"
        "MjUuMzkKICAgIEMgMjguNzAgMjUuODUgMjcuNDIgMjYuMzQgMjYuMTMgMjYuOTkKICAgIEMgMjQu"
        "ODQgMjcuNjMgMjMuNjIgMjguMzUgMjIuMzcgMjkuMjYKICAgIEMgMjEuMTIgMzAuMTcgMTkuNzUg"
        "MzEuMjggMTguNjEgMzIuNDYKICAgIEMgMTcuNDcgMzMuNjQgMTYuNDIgMzQuOTIgMTUuNTMgMzYu"
        "MzMKICAgIEMgMTQuNjQgMzcuNzMgMTMuODIgMzkuMzUgMTMuMjUgNDAuODkKICAgIEMgMTIuNjgg"
        "NDIuNDMgMTIuMzIgNDQuMjEgMTIuMTEgNDUuNTYKICAgIEMgMTEuOTAgNDYuOTEgMTIuMDIgNDgu"
        "NDEgMTIuMDAgNDguOTgKICAgIEMgMTMuMTAgNDguMTQgMTYuNjcgNDUuMjQgMTguNjEgNDMuOTcK"
        "ICAgIEMgMjAuNTUgNDIuNzAgMjIuMDMgNDIuMDEgMjMuNjIgNDEuMzQKICAgIEMgMjUuMjEgNDAu"
        "NjggMjYuNTggNDAuMzIgMjguMTggMzkuOTgKICAgIEMgMjkuNzggMzkuNjQgMzIuMTIgMzkuMzcg"
        "MzMuMjAgMzkuMjkKICAgIEMgMzQuMjggMzkuMjEgMzQuNDMgMzkuNDggMzQuNjggMzkuNTIKICAg"
        "IEwgMzQuOTEgNDguODcKICAgIFoKICAiLz4KPC9zdmc+"
    )
    # Icon fully embedded as base64 — no external SVG file needed.
    # Works identically as a plain .py script or PyInstaller executable.
    from PyQt6.QtCore import QByteArray
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtGui import QPixmap, QPainter
    try:
        svg_bytes = base64.b64decode(_icon_svg_b64)
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        app.setWindowIcon(QIcon(pixmap))
    except Exception:
        pass

    # ── Theme helpers — call _apply_theme(dark) to repaint everything ──
    # Colour tokens are returned so callers (Worker, MainWindow) always read
    # the current palette without caching the QColor objects themselves.
    def _theme_colors(dark: bool):
        if dark:
            BG    = QColor("#1e1e2e")
            BG2   = QColor("#2a2a3e")
            BG3   = QColor("#313145")
            ACCENT= QColor("#89b4fa")
            FG    = QColor("#cdd6f4")
            FG2   = QColor("#6c7086")
            LOG_BG= QColor("#161622")
        else:
            BG    = QColor("#f5f5f5")
            BG2   = QColor("#ffffff")
            BG3   = QColor("#e6e6e6")
            ACCENT= QColor("#2563eb")
            FG    = QColor("#1e1e1e")
            FG2   = QColor("#6b6b6b")
            LOG_BG= QColor("#ffffff")
        GREEN      = QColor("#a6e3a1") if dark else QColor("#1f9d55")
        RED        = QColor("#f38ba8") if dark else QColor("#d1383d")
        YEL        = QColor("#f9e2af") if dark else QColor("#b8860b")
        PURPLE     = QColor("#cba6f7") if dark else QColor("#7c3aed")
        ACCENT_TEXT= BG               if dark else QColor("#ffffff")
        return BG, BG2, BG3, ACCENT, FG, FG2, LOG_BG, GREEN, RED, YEL, PURPLE, ACCENT_TEXT

    def _apply_theme(dark: bool):
        BG, BG2, BG3, ACCENT, FG, FG2, LOG_BG, GREEN, RED, YEL, PURPLE, ACCENT_TEXT = \
            _theme_colors(dark)

        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window,          BG)
        pal.setColor(QPalette.ColorRole.WindowText,      FG)
        pal.setColor(QPalette.ColorRole.Base,            BG2)
        pal.setColor(QPalette.ColorRole.AlternateBase,   BG3)
        pal.setColor(QPalette.ColorRole.Text,            FG)
        pal.setColor(QPalette.ColorRole.Button,          BG3)
        pal.setColor(QPalette.ColorRole.ButtonText,      FG)
        pal.setColor(QPalette.ColorRole.Highlight,       ACCENT)
        pal.setColor(QPalette.ColorRole.HighlightedText, ACCENT_TEXT)
        pal.setColor(QPalette.ColorRole.PlaceholderText, FG2)
        pal.setColor(QPalette.ColorRole.ToolTipBase,     BG3)
        pal.setColor(QPalette.ColorRole.ToolTipText,     FG)
        app.setPalette(pal)

        SS = f"""
    QMainWindow, QWidget {{ background: {BG.name()}; color: {FG.name()}; font-size: 10pt; }}
    QTabWidget::pane {{ border: 1px solid {BG3.name()}; background: {BG2.name()}; border-radius: 6px; }}
    QTabBar::tab {{
        background: {BG.name()}; color: {FG2.name()}; padding: 7px 18px;
        border-top-left-radius: 6px; border-top-right-radius: 6px;
        margin-right: 2px; font-size: 10pt;
    }}
    QTabBar::tab:selected {{ background: {BG2.name()}; color: {ACCENT.name()}; font-weight: bold; }}
    QTabBar::tab:hover {{ background: {BG3.name()}; color: {FG.name()}; }}
    QLineEdit {{
        background: {BG2.name()}; color: {FG.name()}; border: 1px solid {BG3.name()};
        border-radius: 5px; padding: 5px 8px; font-size: 10pt;
    }}
    QLineEdit:focus {{ border: 1px solid {ACCENT.name()}; }}
    QPushButton {{
        background: {BG3.name()}; color: {FG.name()}; border: none;
        border-radius: 5px; padding: 6px 14px; font-size: 10pt;
    }}
    QPushButton:hover {{ background: {ACCENT.lighter(130).name() if dark else BG3.darker(110).name()}; }}
    QPushButton:pressed {{ background: {ACCENT.name()}; color: {ACCENT_TEXT.name()}; }}
    QPushButton#accent {{
        background: {ACCENT.name()}; color: {ACCENT_TEXT.name()}; font-weight: bold;
    }}
    QPushButton#accent:hover {{ background: {ACCENT.lighter(115).name()}; }}
    QPushButton#lang_btn, QPushButton#theme_btn {{
        background: {BG2.name()}; color: {ACCENT.name()}; border: 1px solid {ACCENT.name()};
        border-radius: 5px; padding: 4px 10px; font-size: 9pt; font-weight: bold;
        min-width: 56px;
    }}
    QPushButton#lang_btn:hover, QPushButton#theme_btn:hover {{ background: {BG3.name()}; }}
    QCheckBox {{ color: {FG.name()}; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 16px; height: 16px; border-radius: 3px;
        border: 1px solid {FG2.name()}; background: {BG2.name()};
    }}
    QCheckBox::indicator:checked {{ background: {ACCENT.name()}; border-color: {ACCENT.name()}; }}
    QTreeWidget {{
        background: {BG2.name()}; color: {FG.name()}; border: 1px solid {BG3.name()};
        border-radius: 6px; alternate-background-color: {BG3.lighter(110).name() if not dark else QColor('#252535').name()};
        outline: none; font-size: 9pt;
    }}
    QTreeWidget::item {{ padding: 4px 2px; }}
    QTreeWidget::item:selected {{ background: {BG3.name()}; color: {ACCENT.name()}; }}
    QHeaderView::section {{
        background: {BG3.name()}; color: {ACCENT.name()}; border: none;
        padding: 6px 8px; font-weight: bold; font-size: 9pt;
    }}
    QComboBox {{
        background: {BG2.name()}; color: {FG.name()}; border: 1px solid {BG3.name()};
        border-radius: 5px; padding: 5px 8px; font-size: 10pt;
    }}
    QComboBox:focus {{ border: 1px solid {ACCENT.name()}; }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox::down-arrow {{ width: 10px; height: 10px; }}
    QComboBox QAbstractItemView {{
        background: {BG2.name()}; color: {FG.name()};
        selection-background-color: {BG3.name()}; border: 1px solid {BG3.name()};
    }}
    QTextEdit {{
        background: {LOG_BG.name()}; color: {FG.name()}; border: 1px solid {BG3.name()};
        border-radius: 6px; font-family: monospace; font-size: 9pt;
        padding: 6px;
    }}
    QScrollBar:vertical {{
        background: {BG.name()}; width: 8px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BG3.name()}; border-radius: 4px; min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {ACCENT.name()}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: {BG.name()}; height: 8px; margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {BG3.name()}; border-radius: 4px; min-width: 20px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {ACCENT.name()}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QGroupBox {{
        color: {ACCENT.name()}; font-weight: bold; border: 1px solid {BG3.name()};
        border-radius: 6px; margin-top: 8px; padding-top: 6px;
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
    QStatusBar {{ background: {LOG_BG.name()}; color: {FG2.name()}; font-size: 9pt; border-top: 1px solid {BG3.name()}; }}
    QLabel#credit {{ color: {FG2.name()}; font-size: 9pt; }}
    QLabel#heading {{ color: {ACCENT.name()}; font-size: 14pt; font-weight: bold; }}
    QFrame#sep {{ background: {BG3.name()}; }}
        """
        app.setStyleSheet(SS)

    # Apply initial theme
    _apply_theme(_dark_mode_state[0])

    # ── Convenience accessor — always returns colours for the current theme ──
    # Use _C() anywhere inside MainWindow instead of caching QColor objects,
    # so that switching themes mid-session is automatically reflected.
    def _C():
        return _theme_colors(_dark_mode_state[0])


    # ── Worker thread for scan/convert ────────────────────────
    class Worker(QThread):
        row_ready   = pyqtSignal(object)   # LnkEntry after processing
        log_line    = pyqtSignal(str, str)  # (text, tag)
        finished_ok = pyqtSignal(int, int, int)  # created, skipped, errors

        def __init__(self, entries, drive_map, dry):
            super().__init__()
            self.entries   = entries
            self.drive_map = drive_map
            self.dry       = dry

        def run(self):
            plan(self.entries, self.drive_map)
            c = s = e = 0
            for entry in self.entries:
                if entry.status == "pending":
                    do_symlink(entry, self.dry)
                if entry.status == "created":
                    c += 1
                    if self.dry:
                        self.log_line.emit(
                            T("log_dry", lnk=entry.symlink_path, tgt=entry.symlink_target), "dry")
                    else:
                        self.log_line.emit(
                            T("log_ok", lnk=entry.symlink_path, tgt=entry.symlink_target), "ok")
                elif entry.status == "skipped":
                    s += 1
                    self.log_line.emit(T("log_skip", f=entry.lnk_path.name, r=entry.error), "skip")
                else:
                    e += 1
                    self.log_line.emit(T("log_err",  f=entry.lnk_path.name, r=entry.error), "err")
                self.row_ready.emit(entry)
            self.finished_ok.emit(c, s, e)

    # ── Main window ───────────────────────────────────────────
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.entries    = []
            self.drive_rows = {}   # letter → combo
            self.worker     = None
            self._root_path = None
            self._config    = load_config()
            self._saved_drive_map = self._config.get("drive_map", {})  # letter -> mount str
            self._build_ui()
            self._restore_last_folder()

        def _restore_last_folder(self):
            last = self._config.get("last_folder", "")
            if last and Path(last).is_dir():
                self.entry_folder.setText(last)

        def _build_ui(self):
            self.setWindowTitle(T("title"))
            self.setMinimumSize(860, 640)
            self.resize(960, 700)

            central = QWidget()
            self.setCentralWidget(central)
            root = QVBoxLayout(central)
            root.setSpacing(0)
            root.setContentsMargins(0, 0, 0, 0)

            # Header
            hdr = QWidget()
            self._hdr_widget = hdr
            hdr.setStyleSheet(f"background: {_C()[6].name()};")
            hl  = QHBoxLayout(hdr)
            hl.setContentsMargins(20, 12, 20, 12)
            lbl_title = QLabel("Windows Shortcut to Linux Symbolic Link Z")
            lbl_title.setObjectName("heading")
            hl.addWidget(lbl_title)
            hl.addStretch()

            # Single language toggle button — shows the language you'll switch TO
            self.btn_lang = QPushButton(T("lang_toggle"))
            self.btn_lang.setObjectName("lang_btn")
            self.btn_lang.setFixedHeight(28)
            self.btn_lang.clicked.connect(self._toggle_lang)
            hl.addWidget(self.btn_lang)

            # Dark / light theme toggle button
            _theme_key = "theme_dark" if _dark_mode_state[0] else "theme_light"
            self.btn_theme = QPushButton(T(_theme_key))
            self.btn_theme.setObjectName("theme_btn")
            self.btn_theme.setFixedHeight(28)
            self.btn_theme.clicked.connect(self._toggle_theme)
            hl.addWidget(self.btn_theme)

            lbl_credit = QLabel(T("credit"))
            lbl_credit.setObjectName("credit")
            lbl_credit.setContentsMargins(12, 0, 0, 0)
            hl.addWidget(lbl_credit)
            self.lbl_credit = lbl_credit
            root.addWidget(hdr)

            sep = QFrame()
            sep.setObjectName("sep")
            sep.setFixedHeight(1)
            root.addWidget(sep)

            # Tabs
            self.tabs = QTabWidget()
            self.tabs.setDocumentMode(True)
            root.addWidget(self.tabs)

            self._build_main_tab()
            self._build_log_tab()

            # Status bar
            self.status = QStatusBar()
            self.setStatusBar(self.status)
            self.status.showMessage(T("ready"))

        def _build_main_tab(self):
            tab = QWidget()
            vl  = QVBoxLayout(tab)
            vl.setContentsMargins(16, 14, 16, 14)
            vl.setSpacing(10)
            self.tabs.addTab(tab, T("tab_main"))
            self.tab_main_widget = tab

            # Folder / file selection row
            fl = QHBoxLayout()
            self.lbl_folder = QLabel(T("folder_label"))
            fl.addWidget(self.lbl_folder)
            self.entry_folder = QLineEdit()
            self.entry_folder.setPlaceholderText("/home/user/myfolder")
            fl.addWidget(self.entry_folder, 1)
            self.btn_browse = QPushButton(T("browse"))
            self.btn_browse.clicked.connect(self._browse_folder)
            fl.addWidget(self.btn_browse)
            self.btn_browse_file = QPushButton(T("browse_file"))
            self.btn_browse_file.clicked.connect(self._browse_file)
            fl.addWidget(self.btn_browse_file)
            vl.addLayout(fl)

            # Recursive scan toggle
            self.chk_recursive = QCheckBox(T("recursive"))
            self.chk_recursive.setChecked(self._config.get("recursive", True))
            vl.addWidget(self.chk_recursive)

            # Tree — 5 columns: Shortcut / Path / Windows Target / Drive / Status
            self.tree = QTreeWidget()
            self.tree.setAlternatingRowColors(True)
            self.tree.setRootIsDecorated(False)
            self.tree.setSortingEnabled(True)
            self.tree.setColumnCount(5)
            self._refresh_tree_headers()
            self.tree.setColumnWidth(0, 190)   # Shortcut filename
            self.tree.setColumnWidth(1, 160)   # Path (relative to scan root)
            self.tree.setColumnWidth(2, 190)   # Windows Target
            self.tree.setColumnWidth(3,  50)   # Drive
            self.tree.setColumnWidth(4,  90)   # Status
            self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
            vl.addWidget(self.tree, 1)

            # Drive mapping group
            self.grp_drives = QGroupBox(T("drives_title"))
            grp_vl = QVBoxLayout(self.grp_drives)
            grp_vl.setSpacing(4)
            self.lbl_drives_hint = QLabel(T("drives_hint"))
            self.lbl_drives_hint.setStyleSheet(f"color: {_C()[5].name()}; font-size: 9pt;")
            grp_vl.addWidget(self.lbl_drives_hint)
            self.drives_widget = QWidget()
            self.drives_layout = QVBoxLayout(self.drives_widget)
            self.drives_layout.setSpacing(4)
            self.drives_layout.setContentsMargins(0, 0, 0, 0)
            grp_vl.addWidget(self.drives_widget)
            vl.addWidget(self.grp_drives)

            # Bottom bar
            bl = QHBoxLayout()
            self.chk_dry = QCheckBox(T("dry"))
            bl.addWidget(self.chk_dry)
            bl.addStretch()
            self.btn_convert = QPushButton(T("convert"))
            self.btn_convert.setObjectName("accent")
            self.btn_convert.setMinimumWidth(110)
            self.btn_convert.clicked.connect(self._do_convert)
            bl.addWidget(self.btn_convert)
            vl.addLayout(bl)

        def _build_log_tab(self):
            tab = QWidget()
            vl  = QVBoxLayout(tab)
            vl.setContentsMargins(16, 14, 16, 14)
            self.tabs.addTab(tab, T("tab_log"))
            self.tab_log_widget = tab

            self.log_box = QTextEdit()
            self.log_box.setReadOnly(True)
            vl.addWidget(self.log_box)

        # ── Language ──────────────────────────────────────────
        def _toggle_lang(self):
            """Single button toggles between EN and PT."""
            global _LANG
            _LANG = "pt" if _LANG == "en" else "en"
            self._retranslate()
            self._config["lang"] = _LANG
            save_config(self._config)

        # ── Theme ─────────────────────────────────────────────
        def _toggle_theme(self):
            """Toggle dark/light mode and repaint everything live."""
            _dark_mode_state[0] = not _dark_mode_state[0]
            dark = _dark_mode_state[0]
            _apply_theme(dark)
            # Refresh the header background which is set inline
            self._hdr_widget.setStyleSheet(f"background: {_C()[6].name()};")
            # Refresh the drives hint label colour
            self.lbl_drives_hint.setStyleSheet(f"color: {_C()[5].name()}; font-size: 9pt;")
            # Update button label (shows what you'll switch TO)
            self.btn_theme.setText(T("theme_dark" if dark else "theme_light"))
            # Persist preference
            self._config["dark_mode"] = dark
            save_config(self._config)

        def _retranslate(self):
            self.setWindowTitle(T("title"))
            self.lbl_credit.setText(T("credit"))
            self.lbl_folder.setText(T("folder_label"))
            self.btn_browse.setText(T("browse"))
            self.btn_browse_file.setText(T("browse_file"))
            self.btn_convert.setText(T("convert"))
            self.chk_dry.setText(T("dry"))
            self.chk_recursive.setText(T("recursive"))
            self.grp_drives.setTitle(T("drives_title"))
            self.lbl_drives_hint.setText(T("drives_hint"))
            self.tabs.setTabText(0, T("tab_main"))
            self.tabs.setTabText(1, T("tab_log"))
            self._refresh_tree_headers()
            self.status.showMessage(T("ready"))
            # Button labels show the option you'll switch TO
            self.btn_lang.setText(T("lang_toggle"))
            dark = _dark_mode_state[0]
            self.btn_theme.setText(T("theme_dark" if dark else "theme_light"))
            # Retranslate drive row labels
            letters = sorted(self.drive_rows.keys())
            self._rebuild_drive_rows(letters)

        def _refresh_tree_headers(self):
            self.tree.setHeaderLabels([
                T("col_file"), T("col_path"), T("col_target"),
                T("col_drive"), T("col_status")])

        # ── Folder browse — native Dolphin thumbnail picker ──────
        def _browse_folder(self):
            title = T("folder_label")
            start = self.entry_folder.text().strip() or str(Path.home())
            chosen = _pick_folder_dolphin(self, title, start)
            if chosen:
                self.entry_folder.setText(chosen)
                self._do_scan()   # auto-scan the selected folder immediately

        def _browse_file(self):
            """Let the user pick a single .lnk file using the native file picker."""
            from PyQt6.QtWidgets import QFileDialog
            _ensure_dbus_env()
            start = self.entry_folder.text().strip() or str(Path.home())
            # Use kdialog --getopenfilename for a full KFileWidget with thumbnails/icon view
            start_uri = Path(start).as_uri() if Path(start).exists() else Path.home().as_uri()
            chosen = None
            for kdialog_bin in ("kdialog", "kdialog6"):
                try:
                    _set_kfilewidget_icon_view()
                    result = subprocess.run(
                        [kdialog_bin, "--title", T("browse_file"),
                         "--getopenfilename", start_uri, "*.lnk"],
                        capture_output=True, text=True, timeout=300
                    )
                    if result.returncode == 0:
                        raw = result.stdout.strip()
                        if raw.startswith("file://"):
                            from urllib.parse import unquote
                            raw = unquote(raw[7:])
                        if raw and Path(raw).is_file():
                            chosen = raw
                    break
                except FileNotFoundError:
                    continue
                except subprocess.TimeoutExpired:
                    return
            if chosen is None:
                # Fallback: Qt native file dialog
                path, _ = QFileDialog.getOpenFileName(
                    self, T("browse_file"), start, "Windows Shortcuts (*.lnk);;All files (*)")
                if path:
                    chosen = path
            if chosen:
                self.entry_folder.setText(chosen)
                self._do_scan()

        def _browse_mount_combo(self, combo):
            start = combo.lineEdit().text().strip() if combo.lineEdit().text() else "/mnt"
            chosen = _pick_folder_dolphin(self, T("browse_mount"), start)
            if chosen:
                combo.lineEdit().setText(chosen)

        # ── Drive rows ────────────────────────────────────────
        def _rebuild_drive_rows(self, letters):
            # Clear existing
            while self.drives_layout.count():
                item = self.drives_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.drive_rows.clear()

            mounts = list_mounts()
            mount_choices = [mp for mp, lbl, sz in mounts]

            for letter in sorted(letters):
                row = QWidget()
                rl  = QHBoxLayout(row)
                rl.setContentsMargins(0, 0, 0, 0)
                rl.setSpacing(8)

                lbl_text = T("mount_unc") if letter == "UNC" else T("mount_ph", l=letter)
                lbl = QLabel(lbl_text)
                lbl.setFixedWidth(210)
                rl.addWidget(lbl)

                # Combo with known mounts
                combo = QComboBox()
                combo.setEditable(True)
                combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
                combo.setMinimumWidth(240)
                for mp, mlbl, sz in mounts:
                    display = f"{mp}  {('— '+mlbl) if mlbl else ''}  {sz}"
                    combo.addItem(display, userData=mp)
                remembered = self._saved_drive_map.get(letter, "")
                if remembered:
                    combo.lineEdit().setText(remembered)
                elif mount_choices:
                    combo.setCurrentIndex(0)
                    combo.lineEdit().setText(mount_choices[0])
                else:
                    combo.lineEdit().setText("")
                    combo.lineEdit().setPlaceholderText("/mnt/drive")
                rl.addWidget(combo, 1)

                btn = QPushButton(T("browse_mount"))
                btn.clicked.connect(lambda _, c=combo: self._browse_mount_combo(c))
                rl.addWidget(btn)

                self.drives_layout.addWidget(row)
                self.drive_rows[letter] = combo

        # ── Scan ──────────────────────────────────────────────
        def _save_current_config(self):
            drive_map = {}
            for letter, combo in self.drive_rows.items():
                val = combo.lineEdit().text().strip()
                if val:
                    drive_map[letter] = val
            self._config["last_folder"] = self.entry_folder.text().strip()
            self._config["drive_map"]   = drive_map
            self._config["lang"]        = _LANG
            self._config["recursive"]   = self.chk_recursive.isChecked()
            save_config(self._config)

        def _do_scan(self):
            path_str = self.entry_folder.text().strip()
            if not path_str:
                QMessageBox.warning(self, T("title"), T("no_folder")); return
            if not _HAVE_PYLNK3:
                QMessageBox.critical(self, T("title"), T("no_pylnk3")); return

            p = Path(path_str)
            self.status.showMessage(T("scanning"))
            self.log_box.clear()
            self.tree.clear()

            _BG, _BG2, _BG3, _ACCENT, _FG, _FG2, *_ = _C()
            if p.is_file() and p.suffix.lower() == ".lnk":
                # Single file mode
                self._root_path = p.parent
                self._log(T("log_scan", r=p), _ACCENT.name())
                self.entries = [parse_lnk(p)]
            else:
                # Folder mode
                self._root_path = p
                self._log(T("log_scan", r=p), _ACCENT.name())
                recursive = self.chk_recursive.isChecked()
                self.entries = find_lnk_files(self._root_path, recursive=recursive)
            self._log(T("log_found", n=len(self.entries)), _FG2.name())

            for e in self.entries:
                self._add_tree_row(e)

            letters = sorted({e.drive_letter for e in self.entries if not e.error and e.drive_letter})
            self._rebuild_drive_rows(letters)

            if not self.entries:
                self.status.showMessage(T("no_lnk"))
                QMessageBox.information(self, T("title"), T("no_lnk"))
            else:
                self.status.showMessage(T("ready"))

            self.tabs.setCurrentIndex(0)
            self._save_current_config()   # remember this folder for next launch

        def _add_tree_row(self, e: LnkEntry):
            # Show sub-path relative to the scanned root so sub-folder .lnk files are visible
            try:
                rel = str(e.lnk_path.parent.relative_to(self._root_path)) if self._root_path else ""
                if rel == ".":
                    rel = ""
            except ValueError:
                rel = str(e.lnk_path.parent)

            stat = e.error or "—"
            item = QTreeWidgetItem([
                e.lnk_path.name,
                rel,
                e.windows_path,
                e.drive_letter or "?",
                stat
            ])
            if e.error:
                _RED = _C()[8]
                for c in range(5): item.setForeground(c, _RED)
            self.tree.addTopLevelItem(item)
            return item

        # ── Convert ───────────────────────────────────────────
        def _do_convert(self):
            if not self.entries:
                QMessageBox.warning(self, T("title"), T("no_folder")); return

            drive_map = {}
            for letter, combo in self.drive_rows.items():
                val = combo.lineEdit().text().strip()
                if val:
                    drive_map[letter] = Path(val)

            self._save_current_config()   # remember drive mappings for next launch

            dry = self.chk_dry.isChecked()
            self.tree.clear()
            self.log_box.clear()
            self.btn_convert.setEnabled(False)
            self.btn_browse.setEnabled(False)
            self.btn_browse_file.setEnabled(False)

            self.worker = Worker(self.entries, drive_map, dry)
            self.worker.row_ready.connect(self._on_row_ready)
            self.worker.log_line.connect(self._on_log_line)
            self.worker.finished_ok.connect(lambda c,s,e: self._on_done(c,s,e,dry))
            self.worker.start()
            self.tabs.setCurrentIndex(1)

        def _on_row_ready(self, e: LnkEntry):
            try:
                rel = str(e.lnk_path.parent.relative_to(self._root_path)) if self._root_path else ""
                if rel == ".":
                    rel = ""
            except ValueError:
                rel = str(e.lnk_path.parent)

            stat = e.status
            item = QTreeWidgetItem([
                e.lnk_path.name,
                rel,
                e.windows_path,
                e.drive_letter or "?",
                stat
            ])
            _BG, _BG2, _BG3, _ACCENT, _FG, _FG2, _LOG_BG, _GREEN, _RED, _YEL, _PURPLE, _ = _C()
            colors = {"created": _GREEN.name(), "skipped": _YEL.name(), "error": _RED.name()}
            col = QColor(colors.get(stat, _FG.name()))
            for c in range(5): item.setForeground(c, col)
            self.tree.addTopLevelItem(item)

        def _on_log_line(self, text, tag):
            _BG, _BG2, _BG3, _ACCENT, _FG, _FG2, _LOG_BG, _GREEN, _RED, _YEL, _PURPLE, _ = _C()
            colors = {"ok": _GREEN.name(), "skip": _YEL.name(), "err": _RED.name(), "dry": _PURPLE.name()}
            col = colors.get(tag, _FG.name())
            self._log(text, col)

        def _on_done(self, c, s, e, dry):
            self.btn_convert.setEnabled(True)
            self.btn_browse.setEnabled(True)
            self.btn_browse_file.setEnabled(True)
            key = "done_dry" if dry else "done"
            self.status.showMessage(T(key, c=c, s=s, e=e))
            self.tabs.setCurrentIndex(0)

        def _log(self, text, color=None):
            if color is None:
                color = FG.name()
            cursor = self.log_box.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            cursor.setCharFormat(fmt)
            cursor.insertText(text + "\n")
            self.log_box.setTextCursor(cursor)
            self.log_box.ensureCursorVisible()

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


# ── CLI fallback ───────────────────────────────────────────────
def run_cli():
    global _LANG
    parser = argparse.ArgumentParser(description="Windows Shortcut to Linux Symbolic Link Z")
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--dry-run", "-n", action="store_true")
    parser.add_argument("--mount", "-m", action="append", metavar="LETTER:PATH")
    parser.add_argument("--lang", choices=["en","pt"], default="en")
    parser.add_argument("--no-recurse", dest="recursive", action="store_false", default=True,
                        help="Scan only the top-level folder, skip sub-folders")
    args = parser.parse_args()
    _LANG = args.lang

    print(f"=== {T('title')} — {T('credit')} ===\n")
    root_path = Path(args.directory).expanduser().resolve()
    print(T("log_scan", r=root_path))
    entries = find_lnk_files(root_path, recursive=args.recursive)
    print(T("log_found", n=len(entries)))
    if not entries: return

    drive_map = {}
    if args.mount:
        for spec in args.mount:
            parts = spec.split(":",1)
            if len(parts)==2 and re.match(r'^[A-Za-z]$', parts[0]):
                drive_map[parts[0].upper()] = Path(parts[1])

    plan(entries, drive_map)
    c=s=e=0
    for ent in entries:
        if ent.status == "pending": do_symlink(ent, args.dry_run)
        if   ent.status == "created": c+=1; print(T("log_ok",  lnk=ent.symlink_path, tgt=ent.symlink_target))
        elif ent.status == "skipped": s+=1; print(T("log_skip", f=ent.lnk_path.name,  r=ent.error))
        else:                         e+=1; print(T("log_err",  f=ent.lnk_path.name,  r=ent.error))
    print(f"\nCreated: {c}  Skipped: {s}  Errors: {e}")


# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    if "--no-gui" in sys.argv:
        sys.argv.remove("--no-gui")
        run_cli()
    else:
        try:
            _ensure("PyQt6", "PyQt6.QtWidgets")
            run_gui()
        except Exception as ex:
            print(f"GUI unavailable ({ex}), falling back to CLI.")
            run_cli()
