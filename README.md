# duramson UI+ for Spiritech

Additions to Project Rubi-Ka's Spiritech client: fixes for flaws in its bundled UI, reworked windows, and new
things of its own. Most of it brings back the original Anarchy Online client's look, measured from pictures of
its windows. [The changes in pictures](docs/changes.md), beside the original client and Spiritech as shipped.

## Installing

1. Download this repository (Code → Download ZIP) and unpack it anywhere.
2. Start the installer:
   - **Windows:** double-click `install.bat`. If Windows warns about a script from the internet, choose Run
     (More info → Run anyway).
   - **macOS:** right-click `install.command` → Open (a plain double-click is refused the first time, since
     it comes from the internet). It needs `python3`; if macOS offers to install its command line developer
     tools for it, let it.
   - **Linux:** `python3 install.py`
3. Press Enter to install. The installer finds the game in the usual places; if it doesn't, it asks for the
   client folder (the one with `PRK.Client` in it), and you can drag the folder into its window.
4. Log in a character. The window frame changes by itself; the reworked windows are picked in
   Options → Interface & HUD → UI packages, where they show as `External [duramson.<window>] — UI+`.

Run the installer again for these:

- **Before the launcher updates the game, uninstall** (2 in the menu). The launcher patches the client's own
  files and expects them unchanged. Install again after the update.
- **To update UI+**, download the new version and install it; it replaces the old one.
- **To remove UI+**, uninstall. The client's own files come back from the copies the installer kept.

## How it works

UI+ ships none of Project Rubi-Ka's files. It ships patches: its changes to their files, line by line. The
installer reads the files from your own client and patches them there.

- `core/`: patches for the client's `UI/Packages/Core`, the frame every window is built from. No UI package
  can replace those, so they are patched in place. Each file is kept as it was beside it
  (`<name>.ui-plus-backup`), and uninstalling puts it back.
- `packages/`: windows. Each names the bundled package it is made from in `stock-package.txt`; the installer
  copies that package from the client, applies the window's patches and adds its own files, and puts the
  result in the per-user package folder (`ProjectRubiKa/ui-packages/ui-plus-<window>`).

Installing again starts from the client's own files each time, so nothing is patched twice. Another mod that
patches the same files keeps its changes, as long as it changes other lines than UI+. If a client update
changes the lines a patch needs, the installer stops before writing anything.

`install.py` (Python 3.8 or newer, nothing else) and `install.ps1` (Windows' own PowerShell, started by
`install.bat`) do the same and can undo each other's work. What is installed is recorded in `ui-plus.json` in
the client folder.

## Working on it

`tools/dev.py` turns the patches into whole files to edit, and edited files back into patches:

```bash
python3 tools/dev.py fork      # work/: the client's files with UI+'s patches applied
python3 tools/dev.py sync      # patches from work/, then install into the client
```

Log out to character select and back in to see a change. `python3 tools/dev.py new <name> <BundledPackage>`
starts a window from one of the client's bundled packages, and `python3 tools/dev.py core <file>` starts
patching another Core file. [CONTRIBUTING.md](CONTRIBUTING.md) has the rest: one change per commit, and a
picture for each change one can see.

## License

UI+'s own work (the patches, the installers, the tools, the documentation and its pictures) is licensed under
[CC BY-NC-SA 4.0](LICENSE): share and change it freely, name duramson UI+ as its source, keep the same license,
and don't sell it or use it commercially without permission.

Anarchy Online is a trademark of Funcom. Project Rubi-Ka and Spiritech belong to their owners, and the files
the patches apply to are theirs. This is an unofficial fan project, not made or endorsed by either.
