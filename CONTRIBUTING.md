# Contributing

Fixes, reworked windows and pictures are welcome, as pull requests or as issues with a screenshot.

## Making a change

1. `python3 tools/dev.py fork` puts the client's files, with UI+'s patches applied, into `work/` (not tracked).
2. Edit them there. `python3 tools/dev.py sync` writes the patches and installs them into your client; log out to
   character select and back in to see the change.
3. Commit what `sync` wrote to `core/` and `packages/`. The repository holds only that: never a whole file of
   Project Rubi-Ka's or Funcom's, only patches against them.

A new window starts from the bundled package it replaces: `python3 tools/dev.py new <name> <BundledPackage>`
(the folder name in the client's `UI/Packages`). Give its `package.xml` its own id, `duramson.<short>`, and the
name `UI+`, so it shows beside the bundled window in the UI package list.

## Commits

- One fix or feature per commit, so the history shows each change on its own.
- [Conventional Commits](https://www.conventionalcommits.org/), in English: `fix(core): …`,
  `feat(nano-programs): …`. The subject says what a player sees; the body says why, and where a number comes
  from when it was measured.
- A change one can see gets a picture: the window before and after, and the original client's where it has
  one, in `docs/images/`, with a section in [docs/changes.md](docs/changes.md) that links the commits. Crop
  screenshots to the windows: no character names or chat.

## License of contributions

Contributions are licensed under the repository's license, [CC BY-NC-SA 4.0](LICENSE). By contributing you
also allow duramson to license your contribution to others under other terms, so that a use the license
rules out, a commercial one for example, can still be allowed for the whole project.
