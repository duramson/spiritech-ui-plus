# duramson UI+ for Spiritech

Spiritech, Project Rubi-Ka's new client, brings Anarchy Online to today's computers. UI+ brings back the look of
the original client's interface: window frames built to its measurements, windows laid out as it laid them out,
and its crisp pixel text. It fixes flaws in Spiritech's bundled UI on the way, and adds a few things of its own.

![Inventory: Anarchy Online, Spiritech as shipped, Spiritech with UI+](docs/images/inventory.png)

- **Every window:** frame, title tab, icon, pin and close button at the original client's sizes, distances and
  opacity, measured from pictures of its windows.
- **Nano Programs:** the school buttons, tiles and search as the original draws them, or a new School Tabs layout.
- **Notum Grotesk:** the original client's pixel text as a font, made on your computer (see below).

**[Every change in pictures](docs/changes.md)**, beside the original client and Spiritech as shipped. That page
grows with each change UI+ makes.

![Nano Programs: Spiritech as shipped, and UI+'s School Tabs layout](docs/images/nano-programs-tabs.png)

## Notum Grotesk

The original client draws its interface text in Verdana, hinted and in black and white: every letter is sharp
pixels. Spiritech draws its text smoothed, so even Verdana comes out softer and thicker there. Notum Grotesk brings
the pixels back.

Verdana belongs to Microsoft, so a font made from it can't be shipped. Instead the installer builds the font on your
computer, from the Verdana that is already there: it draws every letter the way the original client
does, at every size from 6 to 72 pixels, and packs all those pixel sets into one TrueType font. The font's own
hinting program picks the right set for the size Spiritech asks for, so the text stays pixel-sharp at any font size
and interface scale. Nothing made from Verdana is in this repository; `fonts/ao-pixels.json` holds only checksums of
the original client's letters, to tell whether a Verdana gives the same pixels (macOS's gives all 610 at 11 px).

![Text at four times its size: Anarchy Online, Spiritech as shipped, Spiritech with Notum Grotesk](docs/images/notum-grotesk.png)

**Still being worked on.** On a Retina screen, or with Windows' display scaling at 200 %, Spiritech draws text at
twice the resolution, so Notum Grotesk comes out at twice the pixel size: sharp, but much finer than the original
client's text, as in the picture above (taken on a Retina Mac). That is not the look UI+ is after yet. At a normal
resolution (100 % scaling) its pixels should be the original client's; that hasn't been tested yet, because UI+ is
made on a Mac. Pictures from such a screen are welcome.

## Installing

1. Download this repository (Code → Download ZIP) and unpack it anywhere.
2. Start the installer:
   - **Windows:** double-click `install.bat`. If Windows warns about a script from the internet, choose Run
     (More info → Run anyway).
   - **macOS:** open Terminal (⌘ Space, type `Terminal`, Enter). Type `python3` and a space, drag
     `install.py` from the unpacked folder into the Terminal window, and press Enter. If macOS offers to
     install its command line developer tools for `python3`, let it, then do it again.
   - **Linux:** the same in a terminal: `python3`, a space, the path to `install.py`.
3. Press Enter to install. The installer finds the game in the usual places; if it doesn't, it asks for the
   client folder (the one with `PRK.Client` in it), and you can drag the folder into its window.
4. Log in a character. The window frame changes by itself; the reworked windows are picked in
   Options → Interface & HUD → UI packages, where they show as `External [duramson.<window>] — UI+`.
5. Before installing, the installer asks whether to generate **Notum Grotesk**: the original client's crisp
   pixel text as a font, made from the Verdana on your computer (the first time it fetches two Python
   packages for that). Pick it in Options as the interface font. So far only `install.py` offers it, not the
   Windows installer.

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
