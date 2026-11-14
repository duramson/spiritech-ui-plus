# duramson UI+ for Spiritech

Additions to Project Rubi-Ka's Spiritech client: fixes for flaws in its bundled UI, reworked windows, and new
things of its own.

## Layout

- `core/`: files from the client's `UI/Packages/Core`, which every window builds its frame from. No UI package can
  replace them, so they are changed in the client itself.
- `packages/`: UI packages. They go into the client's per-user package folder; a window's replacement is picked in
  Options → Interface & HUD → UI packages, where this repository's packages carry `duramson` in their id and name.

## How changes are made

A change to something of Project Rubi-Ka's starts with an unchanged copy of their file or package, in a commit of
its own that names the client version it came from. The changes follow, one per commit. Only what is changed gets
copied; everything else stays the client's own.

So the history shows exactly what differs from the bundled version, and a newer client's files can be brought in
under the changes.

The copied files are Project Rubi-Ka's: ask them before publishing this.
