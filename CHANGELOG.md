# Changelog

What changed for players, the newest first. Each line links the pull request or the commits that made the change;
[docs/changes.md](docs/changes.md) shows the changes in pictures.

## 2026-11-15

- **Client 0.2.2:** UI+ installs on it. The client now draws a nameplate's health bar as its filled and its empty
  part side by side instead of one over the other, and UI+'s nameplates do the same.
  ([#13](https://github.com/duramson/spiritech-ui-plus/pull/13))
- **Planet Map:** the mouse wheel zooms the map, around the spot under the pointer: three turns to twice the size,
  from the whole planet in the window to twice the most detailed map's own size, the picture scaled between the
  map's own detail levels. The zoom buttons keep the middle of the map in place. Set **Planet Map** to **UI+** in
  Options → Interface & HUD → UI packages. ([#14](https://github.com/duramson/spiritech-ui-plus/pull/14))
- **Nameplates:** the names over the heads are written in the original client's pixels: Notum Grotesk at 13
  pixels, a pixel further apart, white and without the thick outline, crisp at every distance. Set
  **Overhead nameplates** to **UI+** in Options → Interface & HUD → UI packages.
  ([#12](https://github.com/duramson/spiritech-ui-plus/pull/12))
- **Wear:** UI+ has a Wear window of its own, with the original client's measures: 202 by 348 pixels, the tab and
  slot labels at 11 pixels so that "Impl" is whole again, a slot's name over the item worn in it, and the tabs that
  aren't chosen fainter. One thing differs from the original on purpose: its last tab reads "Socia", UI+'s reads
  "Social". Set **Wear** to **UI+** in Options → Interface & HUD → UI packages.
  ([#10](https://github.com/duramson/spiritech-ui-plus/pull/10))
- **Window frame:** the window titles are the original client's light grey instead of white.
  ([#8](https://github.com/duramson/spiritech-ui-plus/pull/8))
- **Nano Programs:** the search under the grid sits in a frame like the window's second frame, as the Inventory's
  does: the same blue line on the dark background, its bottom corners cut as that frame's.
  ([#7](https://github.com/duramson/spiritech-ui-plus/pull/7))
- **Name:** UI+ is called duramson's UI+ now, in the installer too.
  ([#6](https://github.com/duramson/spiritech-ui-plus/pull/6))

## 2026-11-14

- **Inventory:** the search and the slot count sit in mirrored frames like the Nano Programs window's second frame,
  and the window's dark background reaches under them.
  ([94c18e8](https://github.com/duramson/spiritech-ui-plus/commit/94c18e8),
  [29c8fa3](https://github.com/duramson/spiritech-ui-plus/commit/29c8fa3))
- **Tooltips:** they show only once the pointer has rested on a button, a slot or a bar for a second and a half,
  instead of the moment it passes: on the shortcut bars, in grids and lists, on the health and nano bars.
  ([6a2372d](https://github.com/duramson/spiritech-ui-plus/commit/6a2372d),
  [0da4149](https://github.com/duramson/spiritech-ui-plus/commit/0da4149))
- **Installer:** installing again after `ui-plus.json` was deleted no longer adds UI+'s own files a second time.
  ([1d4b988](https://github.com/duramson/spiritech-ui-plus/commit/1d4b988))
- **Installer:** uninstalling after a reinstall no longer leaves three empty files in the client's Core folder.
  An install already in that state is mended by installing again.
  ([1eccf72](https://github.com/duramson/spiritech-ui-plus/commit/1eccf72))
- **Inventory:** resized, the window takes only sizes whose rows are all full.
  ([#5](https://github.com/duramson/spiritech-ui-plus/pull/5), fixes
  [#4](https://github.com/duramson/spiritech-ui-plus/issues/4))
- **Notum Grotesk:** the wide gap after "m" in Spiritech's chat is closed.
  ([852f4fb](https://github.com/duramson/spiritech-ui-plus/commit/852f4fb))
- **Inventory:** the background is as dark as the original client's, the slots stand as far from the frame as
  there, and the columns stay when the window grows past the scroll bar.
  ([1dd0ea1](https://github.com/duramson/spiritech-ui-plus/commit/1dd0ea1),
  [137ca06](https://github.com/duramson/spiritech-ui-plus/commit/137ca06),
  [8e9498c](https://github.com/duramson/spiritech-ui-plus/commit/8e9498c))
- **Inventory:** the grid has the original client's scroll bar.
  ([3e4521f](https://github.com/duramson/spiritech-ui-plus/commit/3e4521f))
- **Scroll bar:** new. The original client's scroll bar, built from its own pictures, in the NCU window and the
  Nano Programs grid.
  ([06dd9a8](https://github.com/duramson/spiritech-ui-plus/commit/06dd9a8),
  [672cc84](https://github.com/duramson/spiritech-ui-plus/commit/672cc84),
  [aead52d](https://github.com/duramson/spiritech-ui-plus/commit/aead52d))
- **Nano Programs:** the search field's tooltip is gone; it only repeated what the field shows.
  ([dc62d56](https://github.com/duramson/spiritech-ui-plus/commit/dc62d56))
- **Inventory:** new. UI+'s own Inventory window (`duramson.inventory`), without the tooltips on the search and the
  slot count, and without "Slots:" in front of the count.
  ([15d653f](https://github.com/duramson/spiritech-ui-plus/commit/15d653f))
- **Client 0.2.1:** every patch still applies.
  ([d5665c3](https://github.com/duramson/spiritech-ui-plus/commit/d5665c3))
- **NCU:** the slots, their spacing and the margins follow the original client's measurements, in the target's NCU
  window too.
  ([13f0e81](https://github.com/duramson/spiritech-ui-plus/commit/13f0e81))
- **Window frame:** the frame fits client 0.2.0, and a docked window's content stays as tall as when it floated.
  ([097dfc9](https://github.com/duramson/spiritech-ui-plus/commit/097dfc9),
  [00e2dac](https://github.com/duramson/spiritech-ui-plus/commit/00e2dac))
- **Nano Programs:** the bundled layout's grid sits in a second frame, as in the original client.
  ([7ddbe9f](https://github.com/duramson/spiritech-ui-plus/commit/7ddbe9f))
- **Notum Grotesk 200:** new. The same font with every pixel doubled, for Retina screens and 200 % scaling.
  ([265f4f1](https://github.com/duramson/spiritech-ui-plus/commit/265f4f1),
  [a80993c](https://github.com/duramson/spiritech-ui-plus/commit/a80993c))
- **Notum Grotesk:** new. The original client's pixel text as a font, built by the installer from the Verdana on
  your computer.
  ([b6fbd31](https://github.com/duramson/spiritech-ui-plus/commit/b6fbd31),
  [30d9e51](https://github.com/duramson/spiritech-ui-plus/commit/30d9e51))
- **Installer:** Windows needs no Python: `install.bat` does the same with Windows' own PowerShell.
  ([89a160b](https://github.com/duramson/spiritech-ui-plus/commit/89a160b))
- **Installer:** new. UI+ installs as patches against your own client, and uninstalling puts the client's files
  back.
  ([33eea00](https://github.com/duramson/spiritech-ui-plus/commit/33eea00))
- **Window frame:** the frame and the title bar are built to the original client's measurements: a faint outer
  frame, an opaque title tab, the title, icon, pin and close button where the original has them.
  ([dd68578](https://github.com/duramson/spiritech-ui-plus/commit/dd68578),
  [0e31786](https://github.com/duramson/spiritech-ui-plus/commit/0e31786),
  [d6c52ca](https://github.com/duramson/spiritech-ui-plus/commit/d6c52ca))
- **Nano Programs:** the school buttons, the tiles and the title are drawn as the original client draws them, and
  the bundled layout's search sits under the list.
  ([24250e8](https://github.com/duramson/spiritech-ui-plus/commit/24250e8),
  [b366aab](https://github.com/duramson/spiritech-ui-plus/commit/b366aab),
  [be7c9e7](https://github.com/duramson/spiritech-ui-plus/commit/be7c9e7))
- **Nano Programs:** new. A School Tabs layout, with the schools as tabs like the Wear window's; the window's menu
  (the i icon) switches between it and the bundled layout.
  ([fa29de2](https://github.com/duramson/spiritech-ui-plus/commit/fa29de2),
  [25b960c](https://github.com/duramson/spiritech-ui-plus/commit/25b960c))
- **Nano Programs:** new. UI+'s own Nano Programs window (`duramson.nano`), picked in Options → Interface & HUD →
  UI packages.
  ([2a45fd6](https://github.com/duramson/spiritech-ui-plus/commit/2a45fd6))
