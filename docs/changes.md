# Changes, in pictures

What UI+ changes in Spiritech's UI. Each picture shows the original Anarchy Online client on the left, Spiritech 0.1.0
as shipped in the middle and Spiritech with UI+ on the right, all at the same spot in Ithaca on the same Mac. The
original client ran with [ao-vk](https://github.com/wannabuh/ao-vk) at 1920×1080; its pictures are doubled pixel for
pixel to match Spiritech's Retina pictures. The text in the UI+ pictures is [Notum Grotesk](notum-grotesk.md).

The newest change comes first. The [changelog](../CHANGELOG.md) lists every change in a line, with the pull
request or the commits that made it.

- [Window titles](#window-titles)
- [Nano Programs: framed search](#nano-programs-framed-search)
- [Inventory: search and slot count](#inventory-search-and-slot-count)
- [Inventory: full rows](#inventory-full-rows)
- [Tooltips](#tooltips)
- [Scroll bar](#scroll-bar)
- [NCU window](#ncu-window)
- [Nano Programs: the bundled layout](#nano-programs-the-bundled-layout)
- [Nano Programs: school tabs](#nano-programs-school-tabs)
- [Window frame and text](#window-frame-and-text)
- [Not done yet](#not-done-yet)

## Window titles

The original client writes every window's title in light grey, not white: 216 of 255, the same in its Inventory,
backpack, Bank, NCU and Wear windows. Spiritech's text is white, and UI+'s window frame had left the title at that.
Now the title has the original's grey. The picture shows the original client's title, then UI+'s before and now.

![A window's title: Anarchy Online, Spiritech with UI+ before and now](images/window-title.png)

## Nano Programs: framed search

The search under the grid in the Nano Programs window's bundled layout was Spiritech's grey, rounded input field. Now
it sits in a frame drawn as the window's second frame, as the Inventory's search does: the tab frame's blue line on its
dark background, the bottom corners cut as that frame's are and the top ones square as its are. Its lines stand 4 pixels
clear of the second frame's lines at the sides and the bottom, as the tiles do, and line up with the tiles' outlines on
the left; where the scroll bar shows, the frame runs on under it. It is 23 pixels high, as in the Inventory, so the
window grows by a pixel and the tiles keep their 4 pixels above it. The text starts 6 pixels in, and typed text takes
the frame's blue. The School Tabs layout keeps Spiritech's field for now.

## Inventory: search and slot count

UI+ replaces the Inventory window (Options > Interface & HUD > UI packages, "duramson.inventory"), the one package the
client draws the inventory, bags, banks and loot with. It takes out what got in the way: the tooltips on the search
field ("Item name, at least three letters, then Enter") and on the slot count ("Slots holding an item, of all slots")
only repeated what they show, and the search's opened right over the slot count and ran far past the window's edge.

The search and the count were Spiritech's grey, rounded input fields. Now each sits in a frame like the Nano Programs
window's second frame, in the tab frame's blue line on its dark background, and the two mirror each other: the
search's bottom-left corner is cut as the window's, the count's bottom-right one, and their cut top corners meet in a
notch between them. Their lines stand 5 pixels clear of the window's side and bottom lines, in line with the slots'
outlines, and run on under the scroll bar where it shows, as the Nano window's search does. The count reads "24/30"
in the blue of the NCU count in the corner of the screen, its digits 6 pixels from every line; typed text in the search
takes the same blue. The window's dark background now reaches under the two frames as well. The scroll bar is the
original client's (see [Scroll bar](#scroll-bar) below).

![Inventory with UI+: the search and the slot count in mirrored frames under the slots](images/inventory-footer.png)

## Inventory: full rows

Resized, the Inventory window takes only sizes whose rows are all full. Spiritech's takes any number of columns and as
many rows as the slots need, so most widths left the last row short: with 30 slots, 7 across gave four full rows and
two slots in a fifth, 4 across two slots in the eighth. Now the columns always divide the slots (for 30: 1, 2, 3, 5,
6, 10, 15 or 30 across), with or without the scroll bar. The bank keeps its smallest size of 6 by 4 with credits. The
picture shows the short row as it was, in UI+'s Inventory, which sized its grid as Spiritech's does.

![Inventory at 7 by 5: four full rows and two slots in the fifth](images/inventory-short-row.png)

## Tooltips

The shortcut bars and most windows. Spiritech shows a tooltip the moment the pointer touches a button, a slot or a bar,
so sweeping the pointer over the shortcut bars pops one up after another. The original client waited until the pointer
had rested on a button for about a second. Spiritech has no such delay of its own, so UI+ adds one in Core, which every
window package loads: a tooltip set from Lua shows only once the pointer has rested on its button for a second and a
half, and sweeping over the bars shows none. That covers the shortcut bars (the client draws their descriptions, but Lua
switches them on and off), the grids and lists of the Actions, NCU and Nano Programs windows, the health and nano bars
and the target panels. A delay shows in no picture, so this section has none.

The client draws the item tooltips in the inventory, bags, bank, Wear and Trade windows itself, and Lua can hold them
back only by unbinding the item, which would also stop clicks and drags; those still show at once. So do the tooltips
a layout file sets directly and those of the client's own windows, such as Options.

## Scroll bar

The scroll bar of the NCU window, the Nano Programs grid and the Inventory window. Spiritech draws its own: arrows in
three steps, 2 pixels under the frame's line and 5 from the bar. UI+ puts the original client's in its place, built
from its own pictures (GFX_GUI_SIMPLE_SB_*, which Spiritech has too): the arrows are smooth triangles 11 pixels wide
and 6 high, a pixel under the frame's line and a pixel clear of the line on the right, 3 pixels from the bar. The arrows
scroll a row and repeat while held, a press above or below the bar pages that way, and the bar can be dragged. The bar
picture is stretched to its length, a little softer than in the original client. In the Inventory the bar stands 4
pixels clear of the slots, as there, and the grid gives up the bar's width only while the bar shows. The picture shows
the Inventory window in all three.

![Scroll bar at eight times its size: Anarchy Online, Spiritech as shipped, Spiritech with UI+](images/scroll-bar.png)

## NCU window

The NCU window, and the target's NCU window in grid mode, which is built from the same files. The slots stand 47
pixels apart across with a pixel of background between them, and 29 down, each row covering the dark bottom line of
the slot above, as in the original client; Spiritech sets them 46 by 30 apart. They stand 4 pixels clear of the
window's frame lines on every side, where Spiritech leaves 6 to 10, so a window of 4 by 3 slots comes out 203 by 124
pixels instead of 207 by 135. The middle picture was taken with UI+'s window frame already on; the window's content is
as shipped. The original client's picture has no nano running.

![NCU: Anarchy Online, Spiritech as shipped, Spiritech with UI+](images/ncu.png)

## Nano Programs: the bundled layout

UI+ replaces the Nano Programs window (Options > Interface & HUD > UI packages, "duramson.nano"); its own layout is
brought close to the original client's. The window is called "Programs" as there. The school buttons are plain
buttons drawn as the original draws them: each as wide as its label and about 10 pixels more on either side, each
row's free width shared equally around its buttons, a lone one centred (Spiritech shows pictures with the label baked
in, at fixed widths, packed to the left). Under the buttons the list and the grid sit in a second frame, as in the
original client: its line one pixel clear of the window's frame at the sides and the bottom and 4 pixels under the
buttons, the tab background inside it a little darker and bluer than the window's. The search sits in that frame
under the grid, lined up with the tiles, as far from the frame on the left as on the right (it used to stand half a
pixel closer to it on the left). The tiles show the slot picture at 40 pixels, 2 apart, with the icon 4 pixels in, and
stand 4 pixels clear of the frame's lines at the sides and 3 under its top. The search field has no tooltip ("Nano
name"): it only repeated what the field shows. The middle picture has Psi picked, the others Medical; the UI+ picture
uses Notum Grotesk 200.

![Nano Programs: Anarchy Online, Spiritech as shipped, Spiritech with UI+](images/nano-programs-bundled.png)

## Nano Programs: school tabs

A second layout, picked in the window's menu (the i icon, School Tabs); the original client has none like it. The
schools are tabs over a tab frame, built like the Wear window's, each as wide as its label. The search sits under the
frame as in the Inventory window, the tab frame stands clear of the window's own frame, and the tiles stand 4 pixels
clear of the tab frame on every side. The picture shows Spiritech as shipped and the School Tabs layout.

![Nano Programs: Spiritech as shipped, and the School Tabs layout](images/nano-programs-tabs.png)

## Window frame and text

Every window. The frame and title bar follow the original client's measurements, taken from pictures of its windows
over a black and a white background: the outer frame is 3 pixels wide at 33 % (Spiritech draws 4 pixels at 85 %), the
line under the title sits 23 pixels below the top edge, the title tab starts 7 pixels down and is drawn opaque, and
the window icon, pin and close button stand 5 pixels below the top edge at 85 %. The title is set at 11 pixels, the
original's size. Each window's content keeps its size, so windows come out 2 pixels narrower and 4 shorter. The zooms
under the windows show their top-left corners at four times their size.

The installer offers Notum Grotesk, the original client's interface text: Verdana in black-and-white pixels, built on
the player's computer from the Verdana already there (nothing made from Verdana is in this repository). Picked as the
interface font, it draws Spiritech's text in crisp pixels instead of soft antialiased type. On a Retina screen or at
200 % display scaling Spiritech draws text at twice the resolution, so the pixels come out much finer than the
original client's (as in the Inventory picture, taken on a Retina Mac). For those screens the installer also builds
Notum Grotesk 200, which draws each of the font's pixels as 2 × 2, as in the second picture; both are still being
worked on. At 100 % plain Notum Grotesk should give the original's pixels; that is untested so far.

![Inventory: Anarchy Online, Spiritech as shipped, Spiritech with UI+](images/inventory.png)

![Text at four times its size: Anarchy Online, Spiritech as shipped, Spiritech with Notum Grotesk 200](images/notum-grotesk.png)

## Not done yet

- **Item tooltips.** The inventory, bags, bank, Wear and Trade windows still show item tooltips at once: the client
  draws them itself, and Lua can't make them wait (see [Tooltips](#tooltips) above).

- **Wear.** Its tab labels are set at 12 pixels where the original client draws 11, so with Notum Grotesk "Impl" is
  cut to "Imp". ("Socia" is cut in the original client too.)
