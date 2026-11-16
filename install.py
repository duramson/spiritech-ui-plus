#!/usr/bin/env python3
"""Installs duramson's UI+ into a Spiritech client, updates it, or takes it out again.

    python3 install.py                a menu
    python3 install.py install        install, or update to this copy's version
    python3 install.py uninstall      put the client's own files back and remove UI+'s packages
    python3 install.py status         what is installed
    --client PATH                     the client folder (the one with PRK.Client or PRK.Client.exe and UI in it), when
                                      it isn't found by itself; the environment variable UIPLUS_CLIENT works too

UI+ ships none of Project Rubi-Ka's files, only patches: its changes to their files. The installer reads the files
from your own client and patches them there.

- core/*.diff patch the client's UI/Packages/Core in place, the frame and the shared pieces every window is built
  from. bundled/<package>/*.diff patch other packages of the client in place, where a shared piece sits in each
  window's own layout (the scroll bar). Each file is kept as it was beside it, as <name>.ui-plus-backup, and
  uninstalling puts it back.
- packages/<name>/ is a window. When its stock-package.txt names one of the client's bundled packages, that package
  is copied from the client as UI+ patches it in place and patched with the *.diff files; any other file is UI+'s
  own. The window goes into the per-user package folder as ui-plus-<name>, and the client lists it under Options >
  Interface & HUD > UI packages.

Installing again, after a client update or with a newer UI+, starts from the client's own files each time, so nothing
is patched twice. What was installed is recorded in ui-plus.json in the client folder. Needs Python 3.8 or newer and
nothing else.

Before installing, it asks whether to generate Notum Grotesk too: the original client's crisp pixel text as a font,
with Notum Grotesk 200 beside it for Retina screens and 200 % display scaling, made by fonts/pixelfont.py from the
Verdana on this computer (it fetches the two Python packages it needs the first time). Uninstalling removes them again.
The same step makes the nameplates' pixel text (fonts/build/nameplate-glyphs.lua), which the nameplates package
takes in place of its empty glyphs.lua; without it the nameplates keep Spiritech's font.
"""
import difflib
import hashlib
import json
import os
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TITLE = "duramson's UI+ for Spiritech"
MADE_FOR = "0.2.2"  # the client version the patches were made against
STATE = "ui-plus.json"
BACKUP = ".ui-plus-backup"
PREFIX = "ui-plus-"
STOCK = "stock-package.txt"
SKIP = {".DS_Store", "Thumbs.db", "desktop.ini"}
NONL = "\0"  # marks a last line without a line break while diffing
FONT_TOOL = HERE / "fonts" / "pixelfont.py"
FONTS = ["Notum Grotesk", "Notum Grotesk 200"]  # what pixelfont.py install puts into the user's font folder
# Files made on this computer that replace a placeholder of UI+'s when they are there: the nameplates' pixels, which
# pixelfont.py makes from the player's Verdana together with Notum Grotesk. Never part of the repository.
GENERATED = {("nameplates", "glyphs.lua"): HERE / "fonts" / "build" / "nameplate-glyphs.lua"}


class PatchError(Exception):
    pass


def say(text=""):
    print(text, flush=True)


def version():
    path = HERE / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.exists() else "dev"


def sha(data):
    return hashlib.sha256(data).hexdigest()


# ---- text files: patched with LF line breaks, written back the way the file had them ---------------------------------

def decode(data):
    """A text file's text with LF breaks, and its style (CRLF breaks, a UTF-8 byte-order mark) to encode it back."""
    bom = data.startswith(b"\xef\xbb\xbf")
    text = data[3 if bom else 0:].decode("utf-8")
    crlf = "\r\n" in text
    return text.replace("\r\n", "\n"), (crlf, bom)


def encode(text, style):
    crlf, bom = style
    return (b"\xef\xbb\xbf" if bom else b"") + (text.replace("\n", "\r\n") if crlf else text).encode("utf-8")


# ---- unified diffs ---------------------------------------------------------------------------------------------------

def _lines(text):
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    else:
        lines[-1] += NONL
    return lines


def _text(lines):
    if lines and lines[-1].endswith(NONL):
        return "\n".join(lines)[:-1]
    return "".join(line + "\n" for line in lines)


def make_diff(old, new, name):
    """The unified diff (as `diff -u` writes it, 3 lines of context) from old to new; "" when they are the same."""
    if old == new:
        return ""
    a, b = _lines(old), _lines(new)
    out = [f"--- a/{name}", f"+++ b/{name}"]

    def span(start, end):
        count = end - start
        return f"{start + 1}" if count == 1 else f"{start + (1 if count else 0)},{count}"

    def put(mark, line):
        if line.endswith(NONL):
            out.extend((mark + line[:-1], "\\ No newline at end of file"))
        else:
            out.append(mark + line)

    for group in difflib.SequenceMatcher(None, a, b, autojunk=False).get_grouped_opcodes(3):
        out.append(f"@@ -{span(group[0][1], group[-1][2])} +{span(group[0][3], group[-1][4])} @@")
        for tag, a1, a2, b1, b2 in group:
            if tag == "equal":
                for line in a[a1:a2]:
                    put(" ", line)
                continue
            for line in a[a1:a2]:
                put("-", line)
            for line in b[b1:b2]:
                put("+", line)
    return "\n".join(out) + "\n"


HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _hunks(diff):
    """(old start, new start, [(mark, line)]) per hunk. A hunk is read by its line counts, so a context line whose
    leading space an editor removed still counts."""
    lines, hunks, i = diff.replace("\r\n", "\n").split("\n"), [], 0
    while i < len(lines):
        match = HUNK.match(lines[i])
        i += 1
        if not match:
            continue
        old_count = int(match.group(2)) if match.group(2) is not None else 1
        new_count = int(match.group(4)) if match.group(4) is not None else 1
        body = []
        while old_count > 0 or new_count > 0 or (i < len(lines) and lines[i].startswith("\\")):
            if i >= len(lines):
                raise PatchError("a change in the patch ends early")
            line = lines[i]
            i += 1
            if line.startswith("\\"):
                if body:
                    body[-1] = (body[-1][0], body[-1][1] + NONL)
                continue
            mark, text = (line[0], line[1:]) if line else (" ", "")
            if mark not in " -+":
                raise PatchError(f"the patch has a line it can't read: {line!r}")
            old_count -= mark != "+"
            new_count -= mark != "-"
            body.append((mark, text))
        if old_count < 0 or new_count < 0:
            raise PatchError("a change in the patch doesn't match its line counts")
        hunks.append((int(match.group(1)), int(match.group(3)), body))
    return hunks


def apply_diff(old, diff, reverse=False):
    """old with the diff applied (or taken out, reverse). Each change must find its lines exactly, at most shifted."""
    a = _lines(old)
    out, pos, shift = [], 0, 0
    for old_start, new_start, body in _hunks(diff):
        if reverse:
            body = [({"-": "+", "+": "-"}.get(mark, mark), text) for mark, text in body]
            old_start = new_start
        want = [text for mark, text in body if mark != "+"]
        give = [text for mark, text in body if mark != "-"]
        if not want and old_start == 0 and a:  # a patch adding a whole file has no lines to find: it would fit anywhere
            raise PatchError("the patch adds this file, but there is one already")
        expected = old_start - 1 if want else old_start
        spots = [i for i in range(pos, len(a) - len(want) + 1) if a[i:i + len(want)] == want]
        if not spots:
            raise PatchError(f"the change at line {old_start} doesn't fit")
        at = min(spots, key=lambda i: abs(i - expected - shift))
        out += a[pos:at] + give
        pos = at + len(want)
        shift = at - expected
    return _text(out + a[pos:])


# ---- where things are ------------------------------------------------------------------------------------------------

def is_client(path):
    return path is not None and (path / "UI" / "Packages" / "Core").is_dir()


def normalise(given):
    """The client folder from what the user gave: the client folder itself, the launcher folder holding it,
    PRK.Client(.exe), the macOS PRK Launcher app, or a folder with the launcher's LauncherSettings.json."""
    if not given:
        return None
    path = Path(os.path.expanduser(str(given).strip().strip("'\""))).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, path / "client", path / "Contents" / "MacOS" / "client"):
        if is_client(candidate):
            return candidate
    settings = path / "LauncherSettings.json"
    if settings.exists():
        try:
            client = json.loads(settings.read_text(encoding="utf-8-sig")).get("ClientPath")
            if client and is_client(Path(client)):
                return Path(client)
        except (OSError, ValueError):
            pass
    return None


def candidates():
    seen = [os.environ.get("UIPLUS_CLIENT")]
    folder = HERE  # wherever this copy sits: inside the game folder, or beside it
    for _ in range(4):
        seen += [folder, folder / "PRK-AO-Native"]
        folder = folder.parent
    if sys.platform == "darwin":
        seen += [Path("/Applications/PRK Launcher.app"), Path.home() / "Applications" / "PRK Launcher.app"]
    if os.name == "nt":
        for drive in (f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")):
            for sub in (r"Games\PRK-AO-Native", "PRK-AO-Native", r"Program Files\PRK-AO-Native",
                        r"Program Files (x86)\PRK-AO-Native"):
                seen.append(Path(drive) / sub)
    for base in (os.environ.get("LOCALAPPDATA"), str(Path.home())):
        if base:
            for sub in ("PRK-AO-Native", "Games/PRK-AO-Native", "Desktop/PRK-AO-Native", "Downloads/PRK-AO-Native"):
                seen.append(Path(base) / sub)
    return seen


def find_client(given=None):
    if given:
        client = normalise(given)
        if not client:
            sys.exit(f"{given} is not a Spiritech client folder (the one with PRK.Client and UI in it).")
        return client
    for path in candidates():
        client = normalise(path)
        if client:
            return client
    return None


def package_dir():
    """The per-user package folder the client reads besides its own UI/Addons."""
    if os.name == "nt":
        base = Path(os.environ["LOCALAPPDATA"])
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "ProjectRubiKa" / "ui-packages"


def client_version(client):
    path = client / "version.txt"
    return path.read_text(encoding="utf-8").strip() if path.exists() else "unknown"


def load_state(client):
    """What is installed: "files", the client's files UI+ patched in place (by their path under UI/Packages), and
    "packages", UI+'s windows in the per-user folder. Versions before 2026-11-16 patched only Core in place and
    recorded its files under "core" by name; they are read as Core's."""
    path = client / STATE
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    state.setdefault("version", None)
    files = state.setdefault("files", {})
    for name, entry in state.pop("core", {}).items():
        files.setdefault(f"Core/{name}", entry)
    state.setdefault("packages", {})
    return state


def save_state(client, state):
    path = client / STATE
    if state["files"] or state["packages"]:
        path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif path.exists():
        path.unlink()


def files_of(root):
    """{relative path: path} of the files in a folder, without system clutter and UI+'s kept copies."""
    return {p.relative_to(root).as_posix(): p for p in sorted(root.rglob("*"))
            if p.is_file() and p.name not in SKIP and not p.name.endswith(BACKUP)}


# ---- the client's files: patched in place ---------------------------------------------------------------------------

def ui_file(client, rel):
    """A file of the client's UI/Packages, by its path there ("Core/window.xml")."""
    return client / "UI" / "Packages" / rel


def made_by_ui_plus(entry, backup):
    """Whether a file is UI+'s own, one the client doesn't have: it gets no kept copy, and uninstalling deletes it.
    Earlier installers took such a Core file for the client's own when installing again and kept an empty copy of it,
    so an empty kept copy means the same."""
    return entry.get("created", False) or (backup.exists() and backup.stat().st_size == 0)


def original(client, state, rel):
    """The client's own file without UI+'s changes, its style, and whether UI+ makes the file: the kept copy while
    the installed file is still UI+'s, else the file in the client with UI+'s last changes taken out where they are
    still in it. Nothing, for a file UI+ makes."""
    target = ui_file(client, rel)
    backup = target.with_name(target.name + BACKUP)
    entry = state["files"].get(rel)
    made = entry is not None and made_by_ui_plus(entry, backup)
    if not target.exists():
        return "", (False, False), entry is None or made
    data = target.read_bytes()
    if entry and not made and backup.exists() and sha(data) == entry["sha"]:
        text, style = decode(backup.read_bytes())
        return text, style, False
    text, style = decode(data)
    if entry:  # UI+'s own file, or changed since UI+ installed it: a client update, or another mod editing UI+'s file
        try:
            base = apply_diff(text, entry["diff"], reverse=True)
            return base, style, made and not base
        except PatchError:
            pass
    return text, style, False


def plan_files(client, state, items):
    """What installing writes, worked out before anything is: per (path, diff) of items the path, the diff, the
    client's own text and its style, UI+'s text, and whether UI+ makes the file."""
    plan = []
    for rel, diff in items:
        package = rel.split("/", 1)[0]
        if not ui_file(client, package).is_dir():
            raise PatchError(f"the client has no package UI/Packages/{package}. It is not the client this version of "
                             f"UI+ was made for (client {MADE_FOR}).")
        base, style, created = original(client, state, rel)
        try:
            new = apply_diff(base, diff)
        except PatchError as error:
            try:  # UI+'s changes are in it although nothing records them (ui-plus.json was deleted)
                base = apply_diff(base, diff, reverse=True)
                new = apply_diff(base, diff)
            except PatchError:
                raise PatchError(f"UI/Packages/{rel}: {error}. The client's file is not the one this version of UI+ "
                                 f"was made for (client {MADE_FOR}).") from None
            created = created or not base  # nothing of the client's left in it: a file UI+ made
        plan.append((rel, diff, base, style, new, created))
    return plan


def write_files(client, state, plan):
    changed = 0
    for rel, diff, base, style, new, created in plan:
        target = ui_file(client, rel)
        backup = target.with_name(target.name + BACKUP)
        if not created:
            data = encode(base, style)
            if not backup.exists() or backup.read_bytes() != data:
                backup.write_bytes(data)
        elif backup.exists():  # a kept copy of a file UI+ made: the empty one an earlier installer left
            backup.unlink()
            say(f"  removed UI/Packages/{rel}{BACKUP} (UI+ made that file, the client has none to keep)")
            changed += 1
        data = encode(new, style)
        if not target.exists() or target.read_bytes() != data:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            say(f"  {'added' if created else 'patched'} UI/Packages/{rel}")
            changed += 1
        state["files"][rel] = {"sha": sha(data), "diff": diff, "created": created}
    return changed


def remove_file(client, state, rel):
    target = ui_file(client, rel)
    backup = target.with_name(target.name + BACKUP)
    entry = state["files"].pop(rel)
    made = made_by_ui_plus(entry, backup)
    if not target.exists():
        if backup.exists():
            backup.unlink()
        return
    if sha(target.read_bytes()) == entry["sha"]:
        if made:
            target.unlink()
            if backup.exists():
                backup.unlink()
            say(f"  removed UI/Packages/{rel}")
        elif backup.exists():
            target.write_bytes(backup.read_bytes())
            backup.unlink()
            say(f"  put back the client's UI/Packages/{rel}")
        return
    text, style = decode(target.read_bytes())
    try:
        base = apply_diff(text, entry["diff"], reverse=True)
        if made and not base:
            target.unlink()
            say(f"  removed UI/Packages/{rel}")
        else:
            target.write_bytes(encode(base, style))
            say(f"  took UI+'s changes out of UI/Packages/{rel} (it changed since UI+ installed it)")
    except PatchError:
        say(f"  left UI/Packages/{rel}: it changed since UI+ installed it and has none of UI+'s changes left")
    if backup.exists():
        backup.unlink()


# ---- packages: forked from the client's bundled ones -----------------------------------------------------------------

def stock_of(source):
    """The client's bundled package a window in packages/ is made from, from its stock-package.txt; None for a
    package of UI+'s own."""
    path = source / STOCK
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def bundled_package(client, state, stock, plan):
    """{relative path: bytes} of one of the client's bundled packages as UI+ patches it in place (the plan of
    plan_files), whatever is installed now; without the kept copies."""
    root = ui_file(client, stock)
    if not root.is_dir():
        raise PatchError(f"the client has no bundled package {stock}")
    files = {}
    for rel, path in files_of(root).items():
        key = f"{stock}/{rel}"
        if key in state["files"]:
            base, style, created = original(client, state, key)
            if not created:
                files[rel] = encode(base, style)
        else:
            files[rel] = path.read_bytes()
    for rel, _, _, style, new, _ in plan:
        package, name = rel.split("/", 1)
        if package == stock:
            files[name] = encode(new, style)
    return files


def build_package(client, source, plan, generated=True):
    """{relative path: bytes} of a UI+ package: the bundled package it names, as UI+ patches it in place (plan) and
    then with the window's patches, plus UI+'s own files, with the files made on this computer in place of their
    placeholders (unless generated is False)."""
    stock_name = stock_of(source)
    files = bundled_package(client, load_state(client), stock_name, plan) if stock_name else {}
    for rel, path in files_of(source).items():
        if rel == STOCK:
            continue
        if rel.endswith(".diff") and stock_name:
            target = rel[:-len(".diff")]
            if target not in files:
                raise PatchError(f"packages/{source.name}: {stock_name} has no {target}")
            text, style = decode(files[target])
            try:
                files[target] = encode(apply_diff(text, path.read_text(encoding="utf-8")), style)
            except PatchError as error:
                raise PatchError(f"UI/Packages/{stock_name}/{target}: {error}. The client's file is not the one this "
                                 f"version of UI+ was made for (client {MADE_FOR}).") from None
        else:
            files[rel] = path.read_bytes()
    for (name, rel), made in GENERATED.items():
        if generated and name == source.name and rel in files and made.is_file():
            files[rel] = made.read_bytes()
    return files


def package_id(data):
    match = re.search(rb'<Package\b[^>]*\bid="([^"]+)"', data)
    return match.group(1).decode() if match else None


def clashes(client, folder, pid):
    """Other package folders with the same id: the client refuses every package of a duplicated id."""
    found = []
    for root in (package_dir(), client / "UI" / "Addons"):
        if root.is_dir():
            for other in sorted(root.iterdir()):
                manifest = other / "package.xml"
                if other != folder and manifest.is_file() and package_id(manifest.read_bytes()) == pid:
                    found.append(other)
    return found


def check_package(client, name, files):
    pid = package_id(files.get("package.xml", b""))
    others = clashes(client, package_dir() / (PREFIX + name), pid) if pid else []
    if others:
        raise PatchError(f"packages/{name}: another folder has the package id {pid}, so the client would refuse both: "
                         + ", ".join(str(o) for o in others) + ". Remove it (an older copy of UI+?) and run this again.")


def write_package(client, state, name, files):
    root = package_dir()
    folder = root / (PREFIX + name)
    pid = package_id(files.get("package.xml", b""))
    changed = 0
    current = {rel: path.read_bytes() for rel, path in files_of(folder).items()} if folder.is_dir() else None
    if current != files:
        staging = root / (PREFIX + name + ".new")
        shutil.rmtree(staging, ignore_errors=True)
        for rel, data in files.items():
            path = staging / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        shutil.rmtree(folder, ignore_errors=True)
        staging.rename(folder)
        say(f"  installed the {name} window as {folder}")
        changed = 1
    state["packages"][name] = {"folder": folder.name, "id": pid, "sha": sha(json.dumps(
        {rel: sha(data) for rel, data in sorted(files.items())}).encode())}
    return changed


def remove_package(state, name):
    entry = state["packages"].pop(name)
    folder = package_dir() / entry["folder"]
    if folder.is_dir():
        shutil.rmtree(folder)
        say(f"  removed {folder}")


# ---- commands --------------------------------------------------------------------------------------------------------

def repo_core():
    return sorted((HERE / "core").glob("*.diff")) if (HERE / "core").is_dir() else []


def repo_items():
    """(path under UI/Packages, diff) for every file of the client that UI+ patches in place: core/ for Core,
    bundled/<package>/ for the client's other packages."""
    items = [(f"Core/{p.name[:-len('.diff')]}", p.read_text(encoding="utf-8")) for p in repo_core()]
    root = HERE / "bundled"
    if root.is_dir():
        for rel, path in files_of(root).items():
            if rel.endswith(".diff") and "/" in rel:
                items.append((rel[:-len(".diff")], path.read_text(encoding="utf-8")))
    return items


def repo_packages():
    root = HERE / "packages"
    return sorted(p for p in root.iterdir() if p.is_dir() and files_of(p)) if root.is_dir() else []


def ask_font():
    """The question before installing: generate Notum Grotesk too? Only asked when someone is there to answer."""
    if not FONT_TOOL.exists() or not sys.stdin.isatty():
        return False
    say("Notum Grotesk is the original AO interface text as a font: crisp pixels at every size and interface scale.")
    say("Notum Grotesk 200 draws each of its pixels as 2 x 2, for Retina screens and 200 % display scaling.")
    say("The UI+ nameplates take their pixel text from the same step.")
    say("All are generated from the Verdana on this computer and stay on it.")
    answer = input("Generate Notum Grotesk? [Y/n]: ").strip().lower()
    say()
    return answer in ("", "y", "yes")


def installed_fonts(state):
    """The fonts UI+ installed. Installs from before Notum Grotesk 200 recorded only "font": true."""
    return state.get("fonts") or (FONTS[:1] if state.get("font") else [])


def install_font(client, state):
    say()
    if subprocess.run([sys.executable, str(FONT_TOOL), "install"]).returncode == 0:
        state.pop("font", None)
        state["fonts"] = list(FONTS)
        save_state(client, state)
    else:
        say("Notum Grotesk was not installed. UI+ installs without it.")
    say()


def install(client):
    state = load_state(client)
    if ask_font():  # first, so the nameplates package gets the pixels made with it
        install_font(client, state)
    say(f"Installing {TITLE} {version()} into {client}")
    if client_version(client) != MADE_FOR:
        say(f"  note: this is client {client_version(client)}, UI+ was made for {MADE_FOR}. It installs what still "
            f"fits and stops at anything that doesn't.")
    try:  # everything is worked out before anything is written
        files = plan_files(client, state, repo_items())
        packages = [(source.name, build_package(client, source, files)) for source in repo_packages()]
        for name, data in packages:
            check_package(client, name, data)
    except PatchError as error:
        sys.exit(f"Nothing was changed. {error}")
    try:
        changed = write_files(client, state, files)
        for name, data in packages:
            changed += write_package(client, state, name, data)
        for rel in sorted(set(state["files"]) - {plan[0] for plan in files}):
            remove_file(client, state, rel)
        for name in sorted(set(state["packages"]) - {p.name for p in repo_packages()}):
            remove_package(state, name)
    except PatchError as error:
        save_state(client, state)
        sys.exit(str(error))
    state["version"] = version()
    save_state(client, state)
    if not changed:
        say("  nothing to change: this version is installed")
    say()
    say("Done. It loads at your next character login (log out to character select and back in).")
    say("- The window frame and the scroll bars change every window by themselves. The client's own screens (Options,")
    say("  login) take the frame after a restart of the game.")
    say("- Pick UI+'s windows in Options > Interface & HUD > UI packages, where they show as")
    say("  \"External [duramson.<window>] - UI+\": " + ", ".join(p.name for p in repo_packages()) + ".")


def uninstall(client):
    state = load_state(client)
    if not state["files"] and not state["packages"]:
        say("UI+ is not installed in this client.")
        return
    say(f"Removing {TITLE} from {client}")
    for rel in sorted(state["files"]):
        remove_file(client, state, rel)
    for name in sorted(state["packages"]):
        remove_package(state, name)
    fonts = installed_fonts(state)
    state.pop("font", None)
    state.pop("fonts", None)
    if fonts and FONT_TOOL.exists():  # removes every font of ours it finds, so an older single-font install too
        subprocess.run([sys.executable, str(FONT_TOOL), "uninstall"])
    save_state(client, state)
    say("Done. The client's own UI is back at your next character login (the Options and login screens after a")
    say("restart). If you picked UI+'s windows in Options, the client falls back to its own ones.")


def status(client):
    state = load_state(client)
    say(f"Client: {client} (version {client_version(client)}; UI+ {version()} was made for {MADE_FOR})")
    if not state["files"] and not state["packages"]:
        say("UI+ is not installed.")
        return
    say(f"UI+ {state['version']} is installed:")
    try:
        planned = {plan[0]: plan[4] for plan in plan_files(client, state, repo_items())}
    except PatchError as error:
        planned, note = {}, str(error)
    else:
        note = None
    for rel in sorted(set(state["files"]) | set(planned)):
        target = ui_file(client, rel)
        entry = state["files"].get(rel)
        if not entry:
            say(f"  {rel}: not installed yet")
        elif not target.exists() or sha(target.read_bytes()) != entry["sha"]:
            say(f"  {rel}: changed since it was installed (a client update?): install again")
        elif rel in planned and encode(planned[rel], decode(target.read_bytes())[1]) != target.read_bytes():
            say(f"  {rel}: installed, this copy of UI+ has a newer version")
        else:
            say(f"  {rel}: installed")
    for source in repo_packages():
        entry = state["packages"].get(source.name)
        say(f"  window {source.name}: " + (f"installed as {package_dir() / entry['folder']}" if entry else
                                          "not installed yet"))
    for font in installed_fonts(state):
        say(f"  font {font}: installed")
    if note:
        say(f"  note: {note}")


def menu(client):
    say(f"{TITLE} {version()}")
    say()
    while not client:
        say("The game wasn't found by itself. Drag the client folder (the one with PRK.Client in it, or the")
        say("PRK Launcher app on a Mac) into this window, then press Enter. Nothing and Enter quits.")
        given = input("> ").strip()
        if not given:
            return
        client = normalise(given)
        if not client:
            say("That's not a Spiritech client folder.")
    say(f"Game: {client} (version {client_version(client)})")
    say()
    say("  1) Install / update")
    say("  2) Uninstall (back to the client's own UI)")
    say("  3) Status")
    say("  4) Quit")
    choice = input("Pick one [1]: ").strip() or "1"
    say()
    action = {"1": install, "2": uninstall, "3": status}.get(choice)
    if action:
        try:
            action(client)
        except SystemExit as stop:
            say(stop.code if isinstance(stop.code, str) else "")


def main(argv):
    args, given = [], None
    it = iter(argv)
    for arg in it:
        if arg == "--client":
            given = next(it, None)
        elif arg.startswith("--client="):
            given = arg.split("=", 1)[1]
        elif arg in ("-h", "--help"):
            sys.exit(__doc__)
        else:
            args.append(arg)
    if sys.version_info < (3, 8):
        sys.exit("UI+ needs Python 3.8 or newer.")
    client = find_client(given)
    if not args:
        menu(client)
        return
    if len(args) != 1 or args[0] not in ("install", "uninstall", "status"):
        sys.exit(__doc__)
    if not client:
        sys.exit("The game wasn't found. Name the client folder with --client PATH.")
    {"install": install, "uninstall": uninstall, "status": status}[args[0]](client)


if __name__ == "__main__":
    main(sys.argv[1:])
