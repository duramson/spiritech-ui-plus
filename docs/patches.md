# Patches

UI+ ships none of Project Rubi-Ka's files. It ships patches: its changes to their files, line by line. The
installer reads the files from your own client and patches them there, in place, as if UI+ were part of the
client.

- **`core/`** holds patches for the client's `UI/Packages/Core`, the frame and the shared pieces every window is
  built from.
- **`packages/`** holds windows. Each names the client's package for it in `stock-package.txt` (the folder name in
  the client's `UI/Packages`). Its patches change that package's files, and its own files are added to it.
- Each file UI+ changes is kept as it was beside it (`<name>.ui-plus-backup`), and uninstalling puts it back.
  Files UI+ adds get no kept copy; uninstalling removes them.
- A folder in `packages/` without a `stock-package.txt` is an addon of UI+'s own, a window the client has none of.
  It goes into the per-user package folder as `ui-plus-<name>`.

So players pick nothing in Options: the client's own windows carry UI+'s changes. Until 2026-11-16 UI+'s windows
were packages of their own, picked in Options → Interface & HUD → UI packages; installing removes those and sets
the choice back to the client's own window.

Installing again starts from the client's own files each time, so nothing is patched twice. Another mod that
patches the same files keeps its changes, as long as it changes other lines than UI+. If a client update
changes the lines a patch needs, the installer stops before writing anything.

## The installers

`install.py` (Python 3.8 or newer, nothing else) and `install.ps1` (Windows' own PowerShell, started by
`install.bat`) do the same and can undo each other's work. What is installed is recorded in `ui-plus.json` in
the client folder.

```bash
python3 install.py                # a menu
python3 install.py install        # install, or update to this copy's version
python3 install.py uninstall      # put the client's own files back and remove UI+'s packages
python3 install.py status         # what is installed
```

`--client PATH` names the client folder when it isn't found by itself.
