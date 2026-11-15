#!/usr/bin/env python3
"""Working on UI+: whole files to edit in work/, and the patches made back from them.

    python3 tools/dev.py fork             work/: the client's files with UI+'s patches applied, to edit
    python3 tools/dev.py new NAME STOCK   start a window: packages/NAME, from the client's bundled package STOCK
    python3 tools/dev.py core FILE        start patching another file of the client's UI/Packages/Core
    python3 tools/dev.py diff             the patches (and UI+'s own files) in core/ and packages/, from work/
    python3 tools/dev.py sync             diff, then install into the client
    python3 tools/dev.py preview [off]    install (or remove) the preview: copies of the windows UI+ changes, built
                                          again from the layout files after each sync, without logging out
    --client PATH                         as for install.py

work/ is not tracked. fork overwrites it, so diff what you changed first. Run diff before every commit: the
repository holds only what diff writes.
"""
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import install as ui  # noqa: E402

WORK = REPO / "work"
PREVIEW = REPO / "dev" / "preview"
PREVIEW_FOLDER = "ui-plus-dev-preview"


def stock_package(client, source):
    stock_file = source / ui.STOCK
    if not stock_file.exists():
        return None, {}
    name = stock_file.read_text(encoding="utf-8").strip()
    return name, ui.files_of(client / "UI" / "Packages" / name)


def fork(client):
    state = ui.load_state(client)
    shutil.rmtree(WORK, ignore_errors=True)
    for name, _, _, style, new, _ in ui.plan_core(client, state, ui.repo_core()):
        path = WORK / "core" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(ui.encode(new, style))
    for source in ui.repo_packages():
        for rel, data in ui.build_package(client, source, generated=False).items():
            path = WORK / "packages" / source.name / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"work/ holds the patched files of {client}: edit them there, then run diff")


def new_package(client, name, stock):
    source, work = REPO / "packages" / name, WORK / "packages" / name
    if source.exists():
        sys.exit(f"packages/{name} exists already")
    if not (client / "UI" / "Packages" / stock).is_dir():
        sys.exit(f"the client has no bundled package {stock}")
    source.mkdir(parents=True)
    (source / ui.STOCK).write_text(stock + "\n", encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(client / "UI" / "Packages" / stock, work)
    print(f"work/packages/{name} is a copy of {stock}. Give its package.xml its own id (duramson.<short>) and the "
          f"name UI+, so it shows beside the bundled window; then diff.")


def new_core(client, name):
    path = WORK / "core" / name
    base, style, _ = ui.core_base(client, ui.load_state(client), name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(ui.encode(base, style))
    print(f"work/core/{name} is the client's file: edit it, then diff")


def diff(client):
    state = ui.load_state(client)
    written = 0
    if (WORK / "core").is_dir():
        for rel, path in ui.files_of(WORK / "core").items():
            base, _, _ = ui.core_base(client, state, rel)
            patch = ui.make_diff(base, ui.decode(path.read_bytes())[0], f"UI/Packages/Core/{rel}")
            written += put(REPO / "core" / (rel + ".diff"), patch)
    for work in sorted((WORK / "packages").iterdir()) if (WORK / "packages").is_dir() else []:
        source = REPO / "packages" / work.name
        stock_name, stock = stock_package(client, source)
        keep = {ui.STOCK}
        for rel, path in ui.files_of(work).items():
            data = path.read_bytes()
            if (work.name, rel) in ui.GENERATED:
                # Made from the player's fonts, so never written into the repository: the placeholder there is
                # edited by hand.
                keep.add(rel)
                continue
            if rel in stock:
                original = stock[rel].read_bytes()
                if data == original:
                    continue
                try:
                    old, new = ui.decode(original)[0], ui.decode(data)[0]
                except UnicodeDecodeError:
                    sys.exit(f"work/packages/{work.name}/{rel}: a changed binary file of {stock_name} can't be "
                             f"patched; give it a new name instead")
                written += put(source / (rel + ".diff"), ui.make_diff(old, new, f"UI/Packages/{stock_name}/{rel}"))
                keep.add(rel + ".diff")
            else:
                written += put(source / rel, data)
                keep.add(rel)
        for rel, path in ui.files_of(source).items():
            if rel not in keep:
                path.unlink()
                print(f"removed packages/{work.name}/{rel}")
        for rel in sorted(set(stock) - set(ui.files_of(work))):
            print(f"note: work/packages/{work.name} lacks {stock_name}'s {rel}; a patch can't delete it, so it stays")
    print(f"diff: {written} file(s) changed" if written else "diff: nothing changed")


def preview_folder():
    return ui.package_dir() / PREVIEW_FOLDER


def bump_preview():
    """Gives the installed preview a new generation number: it builds its windows again within a second."""
    folder = preview_folder()
    if not folder.is_dir():
        return False
    number = int(time.time()) % 30000 + 1
    (folder / "generation.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<root>\n'
                                           f'  <View name="generation" min_size="Point({number},1)" />\n</root>\n',
                                           encoding="utf-8")
    return True


def install_preview():
    folder = preview_folder()
    shutil.rmtree(folder, ignore_errors=True)
    shutil.copytree(PREVIEW, folder)
    bump_preview()
    print(f"Installed the preview as {folder}. The client finds a new package only when it starts: restart the "
          f"game once. After that every sync shows its layout files in the preview windows within a second; a change "
          f"to Lua code still needs a login.")


def remove_preview():
    folder = preview_folder()
    if folder.is_dir():
        shutil.rmtree(folder)
        print(f"Removed {folder}; the client lets go of it at its next start.")
    else:
        print("The preview isn't installed.")


def put(path, content):
    """Writes a patch or file; an empty patch removes it. Returns whether anything changed."""
    data = content.encode("utf-8") if isinstance(content, str) else content
    if not data:
        if path.exists():
            path.unlink()
            print(f"removed {path.relative_to(REPO)} (no changes left)")
            return 1
        return 0
    if path.exists() and path.read_bytes() == data:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"wrote {path.relative_to(REPO)}")
    return 1


def main(argv):
    args, given = [], None
    it = iter(argv)
    for arg in it:
        if arg == "--client":
            given = next(it, None)
        else:
            args.append(arg)
    client = ui.find_client(given)
    if not client:
        sys.exit("The client wasn't found: name it with --client PATH.")
    if args == ["fork"]:
        fork(client)
    elif len(args) == 3 and args[0] == "new":
        new_package(client, args[1], args[2])
    elif len(args) == 2 and args[0] == "core":
        new_core(client, args[1])
    elif args == ["diff"]:
        diff(client)
    elif args == ["sync"]:
        diff(client)
        ui.install(client)
        if bump_preview():
            print("The preview builds its windows again.")
    elif args == ["preview"]:
        install_preview()
    elif args == ["preview", "off"]:
        remove_preview()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
