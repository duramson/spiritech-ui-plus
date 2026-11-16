# Contributing

Fixes, reworked windows and pictures are welcome, as pull requests or as issues with a screenshot.

## Rules

1. **`main` is what players download.** Nobody commits or pushes to it. It changes only when a pull request is
   merged.
2. **One change, one branch, one pull request.** A fix or a feature, together with its changelog line and its
   picture.
3. **Branches are named `<type>/<short-name>`**, for example `fix/inventory-short-rows`.
4. **Pull requests are squashed.** Each lands on `main` as one commit with the pull request's title, so `main`
   reads as a list of changes.
5. **Merged branches are deleted.** A branch that exists is work in progress.

GitHub holds `main` to this: it takes pull requests only, squashed, and no forced pushes, and it deletes a branch
once its pull request is merged. The hooks in `.githooks/` say so on your computer, before anything is pushed.
Switch them on once after cloning:

```bash
git config core.hooksPath .githooks
```

## Branches

- **`feat/`** for something new a player sees: `feat/wear-window`
- **`fix/`** for something wrong put right: `fix/options-too-see-through`
- **`docs/`** for the README, the changelog and pictures, and nothing else: `docs/install-steps`
- **`chore/`** for the rest, such as tools or a new client version: `chore/client-0.2.2`

The short name is lower-case letters, digits and hyphens, and says what the branch is for. Besides `main` only
`issue-pictures` stays for good: it holds the pictures the issues show and is never merged.

## Steps

1. **Start a branch from the current `main`.**

   ```bash
   git fetch origin
   git switch -c fix/<short-name> origin/main
   ```

2. **Make the change** (see [Patches](#patches)) and commit as often as you like. The commits are squashed, so
   they needn't be tidy.
3. **Add what belongs to it** (see [Checklist](#checklist)).
4. **Push the branch and open a pull request.**

   ```bash
   git push -u origin fix/<short-name>
   gh pr create
   ```

5. **Put the pull request's number into the changelog line** and push again.
6. **duramson merges it.** GitHub squashes it onto `main` and deletes the branch. Then, on your computer:

   ```bash
   git switch main
   git pull --ff-only
   git branch -D fix/<short-name>
   ```

When `main` has moved on meanwhile, bring the branch up to date with a rebase, not with a merge:

```bash
git fetch origin
git rebase origin/main
git push --force-with-lease
```

Two branches that both add a changelog line collide at the top of that file. Keep both lines, the later one on
top.

Several changes at once each get a folder of their own beside the repository, so none gets in another's way:

```bash
git worktree add ../spiritech-ui-plus.wt/<short-name> -b fix/<short-name> origin/main
```

Each such folder has its own `work/`, and the client holds whatever was synced last. When the branch is merged:
`git worktree remove ../spiritech-ui-plus.wt/<short-name>`.

## Pull requests

- **The title** is the commit `main` gets: [Conventional Commits](https://www.conventionalcommits.org/), in
  English, saying what a player sees. `fix(inventory): fill every row when the window is resized`.
- **The description** says why, and where a number comes from when it was measured. `Fixes #4` closes its issue.
  It becomes the commit's body.
- **One change each.** Two fixes are two branches and two pull requests.

## Checklist

- **A player notices it:** a line at the top of [CHANGELOG.md](CHANGELOG.md).
- **One can see it:** a picture in `docs/images/`, and its section at the top of
  [docs/changes.md](docs/changes.md).
- **Something got further:** its place under Progress in [README.md](README.md) (see below).

Tools, refactoring and changes to the documentation alone get no changelog line.

### Progress in the README

The README stays short: the picture, installing, progress. Anything longer goes into `docs/` and gets a link. No
tables. Progress has four groups:

- **Windows:** every window a UI package can replace, as the client lists them under Options → Interface & HUD →
  UI packages. A window that is started gets a bar with its per cent; the others are named in the folded list.
  Keep the counts in the two lines above and below the bars right. An entry that draws several windows names
  them after its per cent (Inventory containers: the inventory, backpacks, the bank, loot and overflow), and the
  per cent covers them all.
- **Elements:** pieces the windows share, such as the window frame or the scroll bar. The bar says how close the
  piece is to the original client's, and the count how many windows have it.
- **Features:** what is new with UI+, such as a font or a layout the client doesn't have.
- **Bug fixes:** bugs in Spiritech itself that UI+ fixes until the client does. A bug of UI+'s own is fixed and
  gets a changelog line, not an entry here.

The bars are pictures, one for every ten per cent: `![30 %](docs/images/progress/30.svg)`. A bar under way is
turquoise, a full one gold. `python3 tools/progress.py` draws them; the colours are at its top.

### The changelog line

```markdown
- **Inventory:** resized, the window takes only sizes whose rows are all full.
  ([#5](https://github.com/duramson/spiritech-ui-plus/pull/5))
```

The newest comes first: a new line goes on top, under the heading of its day (`## 2026-11-15`), and a new day
gets a new heading above the others. Start with the part in bold. Write for players: what they see and where, not
the file that changed.

### Pictures

A change one can see gets a picture: the window before and after, and the original client's where it has one.
Crop screenshots to the windows: no character names or chat. In [docs/changes.md](docs/changes.md) the newest
change comes first too: a new section goes on top, and a section that is changed moves to the top.

## Where a change goes

UI+ rebuilds the original client's look, and changes each thing where it comes from:

- **A window that looks different** is a window of UI+'s own (`packages/`), which the player picks under Options →
  Interface & HUD → UI packages. That is the client's own way to change a window, and it is used as far as it goes.
- **What no package can reach**, such as the window frame, is patched in Core (`core/`).
- **A piece many windows share** is patched once, where it comes from: in Core when it lives there (the list every
  list view is built from), and in each window's own layout when the client gives it no shared place (the scroll
  bar, `bundled/`). A spacing every window takes from one value is changed in that value, not in one window.
- **Nothing that plays the game** for the player.

## Patches

The repository holds only patches against Project Rubi-Ka's files, never a whole file of theirs or Funcom's
([docs/patches.md](docs/patches.md)). `tools/dev.py` turns the patches into whole files to edit, and edited files
back into patches:

```bash
python3 tools/dev.py fork      # work/: the client's files with UI+'s patches applied
python3 tools/dev.py sync      # patches from work/, then install into the client
```

1. `fork` puts the client's files, with UI+'s patches applied, into `work/` (not tracked).
2. Edit them there. `sync` writes the patches and installs them into your client; log out to character select and
   back in to see the change.
3. Commit what `sync` wrote to `core/`, `bundled/` and `packages/`.

More of `tools/dev.py`:

- **`new <name> <BundledPackage>`** starts a window from one of the client's bundled packages (the folder name in
  the client's `UI/Packages`). Give its `package.xml` its own id, `duramson.<short>`, and the name `UI+`, so it
  shows beside the bundled window in the UI package list.
- **`core <file>`** starts patching another file of the client's `UI/Packages/Core`.
- **`bundled <Package>/<file>`** starts patching a file of another of the client's bundled packages in place, for
  a shared piece that sits in each window's own layout. UI+'s windows made from that package are built on top of
  it.
- **`diff`** writes the patches from `work/` without installing.
- **`preview`** shows a layout file (XML) without logging out. It installs a preview package (restart the game
  once after it), whose windows are copies of the window frame, the NCU window and the scroll bar, built from the
  layout files on disk. Each `sync` builds them again within a second; a change to Lua still needs a login.
  `preview off` removes it.

`install.py` and `install.ps1` do the same and stay in step: a change to one goes into the other.

## License of contributions

Contributions are licensed under the repository's license, [CC BY-NC-SA 4.0](LICENSE). By contributing you
also allow duramson to license your contribution to others under other terms, so that a use the license
rules out, a commercial one for example, can still be allowed for the whole project.
