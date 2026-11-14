# duramson UI+ for Spiritech

Additions to Project Rubi-Ka's Spiritech client: fixes for flaws in its bundled UI, reworked windows, and new
things of its own. [The changes in pictures](docs/changes.md), beside the original client and Spiritech as shipped.

## Layout

- `core/`: files from the client's `UI/Packages/Core`, which every window builds its frame from. No UI package can
  replace them, so they are changed in the client itself.
- `packages/`: UI packages. They go into the client's per-user package folder; a window's replacement is picked in
  Options → Interface & HUD → UI packages, where this repository's packages show as
  `External [duramson.<window>] — UI+`.

## How changes are made

A change to something of Project Rubi-Ka's starts with an unchanged copy of their file or package, in a commit of
its own that names the client version it came from. The changes follow, one per commit. Only what is changed gets
copied; everything else stays the client's own.

So the history shows exactly what differs from the bundled version, and a newer client's files can be brought in
under the changes.

A change one can see gets a picture: the window before and after (and the original client's, where it has one) in
`docs/images/`, with a section in [docs/changes.md](docs/changes.md) that links its commits. The picture comes with
the change, or right after it once the change has been seen in game.

The copied files are Project Rubi-Ka's: ask them before publishing this.
