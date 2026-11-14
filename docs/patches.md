# Patches

UI+ ships none of Project Rubi-Ka's files. It ships patches: its changes to their files, line by line. The
installer reads the files from your own client and patches them there.

- **`core/`** holds patches for the client's `UI/Packages/Core`, the frame every window is built from. No UI
  package can replace those files, so they are patched in place. Each file is kept as it was beside it
  (`<name>.ui-plus-backup`), and uninstalling puts it back.
- **`packages/`** holds windows. Each names the bundled package it is made from in `stock-package.txt`. The
  installer copies that package from the client, applies the window's patches, adds the window's own files, and
  puts the result in the per-user package folder (`ProjectRubiKa/ui-packages/ui-plus-<window>`).

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
