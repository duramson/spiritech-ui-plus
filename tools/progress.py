#!/usr/bin/env python3
"""Draws the README's progress bars: docs/images/progress/0.svg to 100.svg, in steps of ten.

    python3 tools/progress.py

A bar is ten slots in a small frame with the window's cut corner. The colours are taken from UI+'s Nano Programs
window in docs/images/nano-programs-bundled.png: the frame's line, the dark background, an empty slot, and the gold
of the selected school button for a bar that is full.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "progress"

LINE = "#80c0d0"        # the window frame's line
BACKGROUND = "#102028"  # the window's background
EMPTY = "#284858"       # an empty slot
FILLED = "#98e0f0"      # a slot of a bar that is under way
FULL = "#f0d070"        # every slot of a bar at 100 %

SLOTS, SLOT_W, SLOT_H, GAP, PAD = 10, 9, 8, 2, 5
WIDTH = 2 * PAD + SLOTS * SLOT_W + (SLOTS - 1) * GAP
HEIGHT = SLOT_H + 8
CUT = 4


def bar(per_cent):
    filled = per_cent // 10
    frame = (f"M.5 .5H{WIDTH - .5}V{HEIGHT - .5}H{CUT + .5}L.5 {HEIGHT - CUT - .5}Z")
    slots = []
    for i in range(SLOTS):
        colour = EMPTY if i >= filled else FULL if filled == SLOTS else FILLED
        slots.append(f'<rect x="{PAD + i * (SLOT_W + GAP)}" y="4" width="{SLOT_W}" height="{SLOT_H}" '
                     f'fill="{colour}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{per_cent} %">\n'
            f'<title>{per_cent} %</title>\n'
            f'<path d="{frame}" fill="{BACKGROUND}" stroke="{LINE}"/>\n'
            + "\n".join(slots) + "\n</svg>\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for per_cent in range(0, 101, 10):
        (OUT / f"{per_cent}.svg").write_text(bar(per_cent), encoding="utf-8")
    print(f"wrote 11 bars to {OUT}")


if __name__ == "__main__":
    main()
