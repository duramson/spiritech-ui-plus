# Contributing

Fixes, reworked windows and pictures are welcome, as pull requests or as issues with a screenshot.

## The rules in short

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

| Type | For | Example |
| --- | --- | --- |
| `feat/` | Something new a player sees. | `feat/wear-window` |
| `fix/` | Something wrong put right. | `fix/options-too-see-through` |
| `docs/` | The README, the changelog, pictures and nothing else. | `docs/install-steps` |
| `chore/` | The rest: tools, a new client version, housekeeping. | `chore/client-0.2.2` |

The short name is lower-case letters, digits and hyphens, and says what the branch is for. Besides `main` only
`issue-pictures` stays for good: it holds the pictures the issues show and is never merged.

## A change, step by step

1. **Start a branch from the current `main`.**

   ```bash
   git fetch origin
   git switch -c fix/<short-name> origin/main
   ```

2. **Make the change** (see [Editing the patches](#editing-the-patches)) and commit as often as you like. The
   commits are squashed, so they needn't be tidy.
3. **Add what belongs to it:** the changelog line, the picture, the README's tables (see
   [What a pull request holds](#what-a-pull-request-holds)).
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

### Several changes at once

Each change gets a folder of its own beside the repository, so none gets in another's way:

```bash
git worktree add ../spiritech-ui-plus.wt/<short-name> -b fix/<short-name> origin/main
```

Each such folder has its own `work/`. The client holds whatever was synced last. When the branch is merged:
`git worktree remove ../spiritech-ui-plus.wt/<short-name>`.

## Pull requests

- **The title** is the commit `main` gets: [Conventional Commits](https://www.conventionalcommits.org/), in
  English, saying what a player sees. `fix(inventory): fill every row when the window is resized`.
- **The description** says why, and where a number comes from when it was measured. `Fixes #4` closes its issue.
  It becomes the commit's body.
- **One change each.** Two fixes are two branches and two pull requests.

### What a pull request holds

| The change | Comes with |
| --- | --- |
| Anything a player notices | A line at the top of [CHANGELOG.md](CHANGELOG.md). |
| Anything one can see | A picture in `docs/images/`, and its section at the top of [docs/changes.md](docs/changes.md). |
| A part got further | The Progress table and "Still to come" in [README.md](README.md). |
| A new window, or something new to switch on | "What you get" in [README.md](README.md). |
| A new UI+ version or client version | The line under the README's first picture. |

Tools, refactoring and changes to the documentation alone get no changelog line.

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

## Editing the patches

The repository holds only patches against Project Rubi-Ka's files, never a whole file of theirs or Funcom's.
`tools/dev.py` turns the patches into whole files to edit, and edited files back into patches:

```bash
python3 tools/dev.py fork      # work/: the client's files with UI+'s patches applied
python3 tools/dev.py sync      # patches from work/, then install into the client
```

1. `fork` puts the client's files, with UI+'s patches applied, into `work/` (not tracked).
2. Edit them there. `sync` writes the patches and installs them into your client; log out to character select and
   back in to see the change.
3. Commit what `sync` wrote to `core/` and `packages/`.

| Command | Does |
| --- | --- |
| `python3 tools/dev.py new <name> <BundledPackage>` | Starts a window from one of the client's bundled packages (the folder name in the client's `UI/Packages`). Give its `package.xml` its own id, `duramson.<short>`, and the name `UI+`, so it shows beside the bundled window in the UI package list. |
| `python3 tools/dev.py core <file>` | Starts patching another file of the client's `UI/Packages/Core`. |
| `python3 tools/dev.py diff` | Writes the patches from `work/` without installing. |
| `python3 tools/dev.py preview` | Shows a layout file (XML) without logging out: it installs a preview package (restart the game once after it), whose windows are copies of the window frame, the NCU window and the scroll bar, built from the layout files on disk. Each `sync` builds them again within a second; a change to Lua still needs a login. `preview off` removes it. |

`install.py` and `install.ps1` do the same and stay in step: a change to one goes into the other.
[docs/how-it-works.md](docs/how-it-works.md) says what they do.

## Where things are written down

| File | Holds | Order |
| --- | --- | --- |
| [README.md](README.md) | What a player needs at first sight: progress, what UI+ gives, installing. | |
| [CHANGELOG.md](CHANGELOG.md) | Every change in a line. | Newest first |
| [docs/changes.md](docs/changes.md) | Every change in pictures, with its measurements. | Newest first |
| [docs/notum-grotesk.md](docs/notum-grotesk.md) | The font: how it is made and what is open. | |
| [docs/how-it-works.md](docs/how-it-works.md) | Patches and the installers. | |

The README stays short. What takes more than a few lines goes into `docs/` and gets a link.

## License of contributions

Contributions are licensed under the repository's license, [CC BY-NC-SA 4.0](LICENSE). By contributing you
also allow duramson to license your contribution to others under other terms, so that a use the license
rules out, a commercial one for example, can still be allowed for the whole project.
