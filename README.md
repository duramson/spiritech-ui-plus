# duramson's UI+ for Spiritech

The look of the original Anarchy Online interface for Spiritech, Project Rubi-Ka's new client: its window frames,
its layouts and its crisp pixel text. With a few fixes and additions of its own.

![Nano Programs: Anarchy Online, Spiritech as shipped, Spiritech with UI+](docs/images/nano-programs-bundled.png)

## Install

1. **[Download UI+](https://github.com/duramson/spiritech-ui-plus/archive/refs/heads/main.zip)** and unpack it.
2. **Windows:** double-click `install.bat`.\
   **macOS, Linux:** run `python3 install.py` in a terminal.
3. Press Enter to install, then log in a character.
4. In Options → Interface & HUD → UI packages, set **Inventory containers** and **Nano programs** to **UI+**, and
   log in again.

> [!IMPORTANT]
> Before the launcher updates the game, start the installer again and choose Uninstall. Install again after the
> update.

<details>
<summary>Help with installing</summary>

- **Windows warns about a script from the internet:** choose More info → Run anyway.
- **macOS:** open Terminal (⌘ Space, type `Terminal`, Enter). Type `python3` and a space, drag `install.py` from
  the unpacked folder into the Terminal window, and press Enter. If macOS offers to install its command line
  developer tools, let it, then do it again.
- **The installer doesn't find the game:** it asks for the client folder, the one with `PRK.Client` in it. You can
  drag the folder into its window.
- **Updating UI+:** download it again and install. It replaces the old one.
- **Removing UI+:** start the installer and choose Uninstall. The client's own files come back.

</details>

## Progress

### Windows

Every window that Options → Interface & HUD → UI packages can replace. 2 of 40 have had their first pass.

![100 %](docs/images/progress/100.svg) Nano programs · 100 %\
![100 %](docs/images/progress/100.svg) NCU · 100 %\
![30 %](docs/images/progress/30.svg) Inventory containers · 30 %\
![0 %](docs/images/progress/0.svg) Wear · next

<details>
<summary>36 more, not started</summary>

Info / Inspect · Planet Map · Local Map · Compass · Sneak indicator · Logout progress ·
Telegraph announcements · Overhead nameplates · Floating combat text · Actions · Agg/Def · Chat content ·
Chat configuration · Chat windows · Control Center · Faction · Friends · NPC dialogue · Shortcut bars ·
Global Market Interface · Missions · Mission terminal · Perks · Pets · Raid · Raid bars · Skills · Stats ·
Player status bars · Target panels · Target NCU · Team · Team invitations · Combat timer stack ·
Trade and shops · Tradeskills

</details>

### Elements

Pieces the windows share: how close each is to the original, and how many windows have it.

![100 %](docs/images/progress/100.svg) Window frame · 100 % · every window\
![80 %](docs/images/progress/80.svg) Scroll bar · 80 % · 3 of 18 windows

### Features

New with UI+.

- [Notum Grotesk](docs/notum-grotesk.md), the original client's pixel text as a font
- School Tabs, a second layout for the Nano programs window
- Tooltips that wait until the pointer rests

### Bug fixes

Bugs in Spiritech, fixed here until the client fixes them itself.

- Inventory: resizing left the last row short of slots
- Inventory: the search's tooltip covered the slot count

---

[Changelog](CHANGELOG.md) · [Every change in pictures](docs/changes.md) ·
[Issues](https://github.com/duramson/spiritech-ui-plus/issues) · [Contributing](CONTRIBUTING.md)

## License

UI+'s own work is licensed under [CC BY-NC-SA 4.0](LICENSE): share and change it, name duramson's UI+ as its source,
keep the same license, and don't use it commercially without permission.

Project Rubi-Ka may use, change and ship any part of UI+ in the Spiritech client under their own terms, as long as
they credit duramson's UI+.

An unofficial fan project, not made or endorsed by Funcom or Project Rubi-Ka. Anarchy Online is a trademark of
Funcom; Spiritech and the files the patches apply to belong to their owners.
