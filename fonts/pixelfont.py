#!/usr/bin/env python3
"""Notum Grotesk: the original Anarchy Online client's interface font for Spiritech, built on the player's computer.

The original client draws its interface text with Verdana, monochrome and hinted: 11 px in windows, on buttons and
in the Stats window, 12 px in the chat (as AO draws it under Wine). Spiritech draws its text antialiased, so even
Verdana comes out thicker and softer there. This tool rasterises the player's own Verdana the way the original client
does, at every size from 6 to 72 px, and builds one TrueType font from it, Notum Grotesk: each glyph carries its
pixels for every one of those sizes, and the font's hinting program picks the set for the size being drawn. So the
text stays crisp pixels at any font size and any interface scale (fractional sizes snap to whole pixels); without
hinting, or above 72 px, it shows Verdana's own outline.

Nothing made from Verdana is shipped: the font is built where it is used, from the Verdana already there.

    pixelfont.py status                        the Verdana found, whether it gives the original pixels, what's installed
    pixelfont.py build [options]               build the font (default: into build/ beside this script)
    pixelfont.py check [--verdana PATH]        compare a Verdana with the original client's pixels
    pixelfont.py install [options]             build, then install into the user's font folder
    pixelfont.py uninstall [--fonts-dir DIR]   remove the installed font

Options:
    --verdana PATH     use this Verdana instead of searching for one
    --out DIR          where build puts the font
    --fonts-dir DIR    install into this folder instead of the user's font folder (no registry, no font cache)

Needs Python 3.9+ with fonttools and freetype-py (requirements.txt). When they are missing, this tool puts them
into a folder of its own (build/venv beside it, about 20 MB, downloaded once) and runs from there.
"""
import argparse
import ctypes
import hashlib
import json
import math
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

# FreeType's v35 TrueType interpreter hints the way Windows' GDI does. Its newer default (v40) leaves out some
# hinting and, in FreeType 2.13, draws 208 accented Latin letters of Verdana differently in black and white. Set
# before FreeType starts; _use_v35 sets it again through the API, in case this FreeType ignores the environment.
os.environ["FREETYPE_PROPERTIES"] = "truetype:interpreter-version=35"

HERE = Path(__file__).resolve().parent
VENV = HERE / "build" / "venv"
CHECKSUMS = HERE / "ao-pixels.json"
FAMILY = "Notum Grotesk"
SIZES = range(6, 73)  # pixel sizes the font carries Verdana's monochrome glyphs for
CHECK_SIZE = 11  # the original client's interface size (AO's "NORMAL" font), which ao-pixels.json holds
FILENAME = "notum-grotesk.ttf"

# Characters built into the fonts: Latin (with Extended-A/B), Greek, Cyrillic, punctuation, currency, letterlike
# symbols, arrows, maths, box drawing and geometric shapes, as far as Verdana has them.
RANGES = [(0x20, 0x7E), (0xA0, 0x24F), (0x370, 0x3FF), (0x400, 0x4FF), (0x2000, 0x206F), (0x20A0, 0x20CF),
          (0x2100, 0x214F), (0x2190, 0x21FF), (0x2200, 0x22FF), (0x2500, 0x259F), (0x25A0, 0x25FF)]

NO_VERDANA = """No Verdana found. Notum Grotesk is built from a copy of Verdana on this computer:
  - Windows and macOS have one (macOS: /System/Library/Fonts/Supplemental/Verdana.ttf)
  - on Linux: the distribution's Microsoft core fonts package (ttf-mscorefonts-installer on Debian/Ubuntu,
    msttcore-fonts-installer on Fedora, ttf-ms-fonts on Arch), or `winetricks corefonts` in a Wine prefix.
    Those bring Verdana 2.35, older than Windows' and macOS' copies: `check` says whether it gives the same pixels
  - or name one: --verdana /path/to/verdana.ttf"""


# --- the two packages --------------------------------------------------------------------------------------------

def _need_packages():
    """Imports fonttools and freetype-py; when they are missing, installs them into VENV once and runs this tool
    again from there."""
    global freetype, FontBuilder, timestampNow, TTGlyphPen, TransformPen, DecomposingRecordingPen, TTFont, newTable
    global ttProgram, Glyph, GlyphCoordinates
    try:
        import freetype
        from fontTools.fontBuilder import FontBuilder
        from fontTools.misc.timeTools import timestampNow
        from fontTools.pens.recordingPen import DecomposingRecordingPen
        from fontTools.pens.transformPen import TransformPen
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        from fontTools.ttLib import TTFont, newTable
        from fontTools.ttLib.tables import ttProgram
        from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
        return
    except ImportError as e:
        missing = e.name
    python = VENV / ("Scripts/python.exe" if sys.platform.startswith("win") else "bin/python")
    if Path(sys.prefix).resolve() == VENV.resolve():
        sys.exit(f"{missing} is still missing in {VENV}: delete that folder and try again")
    requirements = HERE / "requirements.txt"
    if not python.exists() or subprocess.run([str(python), "-c", "import freetype, fontTools"],
                                             capture_output=True).returncode != 0:
        print(f"Getting fonttools and freetype-py into {VENV} (once, needs the internet) ...", flush=True)
        steps = [[sys.executable, "-m", "venv", str(VENV)],
                 [str(python), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "-r",
                  str(requirements)]]
        for step in steps:
            if subprocess.run(step).returncode != 0:
                sys.exit(f"That didn't work. Install them yourself, then run this again:\n"
                         f"    {Path(sys.executable).name} -m pip install -r {requirements}")
    sys.exit(subprocess.run([str(python), str(Path(__file__).resolve())] + sys.argv[1:]).returncode)


# --- finding Verdana ---------------------------------------------------------------------------------------------

def _font_names(path):
    try:
        names = TTFont(str(path), lazy=True, fontNumber=0)["name"]
    except Exception:
        return None
    return names.getBestFamilyName(), names.getBestSubFamilyName(), names.getDebugName(5) or "?"


def _in_dir(directory, filename):
    """A file in a folder, whatever the case of its name (Linux and Wine folders differ)."""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return [p for p in directory.iterdir() if p.name.lower() == filename.lower()]


def _fc_match(family):
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", family], capture_output=True, text=True, timeout=10)
        return [Path(out.stdout.strip())] if out.returncode == 0 and out.stdout.strip() else []
    except (OSError, subprocess.TimeoutExpired):
        return []


def verdana_candidates():
    home = Path.home()
    found = []
    if sys.platform == "darwin":
        for d in ["/System/Library/Fonts/Supplemental", "/Library/Fonts", home / "Library/Fonts"]:
            found += _in_dir(d, "Verdana.ttf")
        for bottle in sorted((home / "Library/Application Support/CrossOver/Bottles").glob("*")):
            found += _in_dir(bottle / "drive_c/windows/Fonts", "verdana.ttf")
    elif sys.platform.startswith("win"):
        found += _in_dir(Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts", "verdana.ttf")
        if os.environ.get("LOCALAPPDATA"):
            found += _in_dir(Path(os.environ["LOCALAPPDATA"]) / "Microsoft/Windows/Fonts", "verdana.ttf")
    else:
        found += _fc_match("Verdana")
        for d in ["/usr/share/fonts/truetype/msttcorefonts", "/usr/share/fonts/msttcore", "/usr/share/fonts/TTF",
                  "/usr/share/fonts/corefonts", "/usr/share/fonts/truetype/corefonts", home / ".local/share/fonts",
                  home / ".fonts"]:
            found += _in_dir(d, "verdana.ttf")
        for prefix in [os.environ.get("WINEPREFIX"), home / ".wine"]:
            if prefix:
                found += _in_dir(Path(prefix) / "drive_c/windows/Fonts", "verdana.ttf")
    return found


def find_verdana(path=None):
    """(path, version) of Verdana Regular, checked by its name table: fc-match quietly offers a substitute, and a
    file named verdana.ttf may be something else."""
    seen = set()
    for candidate in ([Path(path)] if path else verdana_candidates()):
        if candidate in seen or not candidate.is_file():
            continue
        seen.add(candidate)
        names = _font_names(candidate)
        if names and names[0] == "Verdana" and names[1] == "Regular":
            return candidate, names[2]
    if path:
        sys.exit(f"{path} is not Verdana Regular")
    return None, None


# --- rasterising as the original client does --------------------------------------------------------------------

def _use_v35():
    try:
        lib, handle = freetype.raw._lib, freetype.get_handle()
        version = ctypes.c_uint(35)
        lib.FT_Property_Set(handle, b"truetype", b"interpreter-version", ctypes.byref(version))
    except Exception:
        pass  # the environment variable set at the top still applies


class Rasteriser:
    """Glyphs as the original client draws them: TrueType hinting (v35), 1 bit per pixel."""

    def __init__(self, path):
        _use_v35()
        self.path = str(path)
        self.face = freetype.Face(self.path)
        self.font = TTFont(self.path)
        self.upem = self.font["head"].unitsPerEm
        self.cmap = {c: g for c, g in self.font.getBestCmap().items() if any(a <= c <= b for a, b in RANGES)}

    def glyph(self, name, ppem):
        """(rows of '0'/'1', left, top) of the glyph, top-down, with left/top relative to the pen origin."""
        self.face.set_pixel_sizes(0, ppem)
        self.face.load_glyph(self.font.getGlyphID(name), freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
        g = self.face.glyph
        bm = g.bitmap
        buf = bytes(bm.buffer)
        rows = ["".join("1" if buf[y * bm.pitch + (x >> 3)] & (0x80 >> (x & 7)) else "0" for x in range(bm.width))
                for y in range(bm.rows)]
        return rows, g.bitmap_left, g.bitmap_top

    def advance(self, name, ppem):
        """The original client's pen advance: the unhinted advance width, rounded to whole pixels (not the hinted
        hdmx width Windows would use: AO under Wine draws "Combat" a pixel tighter than that)."""
        return math.floor(Fraction(self.font["hmtx"][name][0] * ppem, self.upem) + Fraction(1, 2))


def glyph_checksum(rows, left, top, advance):
    return hashlib.sha256(f"{'|'.join(rows)};{left};{top};{advance}".encode()).hexdigest()[:12]


# --- pixels to outlines ------------------------------------------------------------------------------------------

def trace(rows, left, top):
    """Outlines of the set pixels in pixel units (y up, baseline 0): outer contours clockwise, holes
    counter-clockwise, as TrueType wants them; straight runs merged into one edge."""
    filled = {(left + x, top - y - 1) for y, row in enumerate(rows) for x, bit in enumerate(row) if bit == "1"}
    edges = {}
    for (i, j) in filled:
        if (i - 1, j) not in filled:
            edges.setdefault((i, j), []).append((i, j + 1))
        if (i, j + 1) not in filled:
            edges.setdefault((i, j + 1), []).append((i + 1, j + 1))
        if (i + 1, j) not in filled:
            edges.setdefault((i + 1, j + 1), []).append((i + 1, j))
        if (i, j - 1) not in filled:
            edges.setdefault((i + 1, j), []).append((i, j))
    contours = []
    while edges:
        start = min(edges)
        path, cur, heading = [start], start, None
        while True:
            options = edges[cur]
            if len(options) == 1:
                nxt = options[0]
            else:  # two pixels touching only at a corner: turn towards the filled side, keeping them apart
                dx, dy = heading
                order = [(dy, -dx), (dx, dy), (-dy, dx)]
                nxt = min(options, key=lambda p: order.index((p[0] - cur[0], p[1] - cur[1])))
            options.remove(nxt)
            if not options:
                del edges[cur]
            heading = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start:
                break
            path.append(cur)
        n = len(path)
        corners = [b for k, b in enumerate(path) for a, c in [(path[k - 1], path[(k + 1) % n])]
                   if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0]
        contours.append(corners)
    return contours


# --- one font for every size ---------------------------------------------------------------------------------------
#
# Each glyph holds Verdana's own outline, then one pixel outline per size in SIZES. The pixel outlines are stored flat
# (every point at y = 0, so they draw nothing) with x already on that size's pixel grid: the em is 16384 units, so a
# pixel edge lands within 1/128 px of a whole pixel at any size, and FreeType's 1/64 px precision puts it exactly on
# it. The glyph program asks for the size, flattens Verdana's outline and lifts the matching pixel outline's points
# to their rows. It only moves points up and down, which FreeType's newer (v40) interpreter does too, in grayscale
# and in black and white. Without hinting nothing runs, and Verdana's outline is what shows.

# TrueType instructions used below
SVTCA_Y, SRP0, MPPEM, EQ, IF, EIF, CALL, FDEF, ENDF = 0x00, 0x10, 0x4B, 0x54, 0x58, 0x59, 0x2B, 0x2C, 0x2D
SWAP, DUP, POP, CINDEX, ROLL, ADD, SUB, MUL, ALIGNRP, MSIRP, JROT = (0x23, 0x20, 0x21, 0x25, 0x8A, 0x60, 0x61, 0x63,
                                                                   0x3C, 0x3A, 0x78)


def _push(values, words=False):
    out, values = [], list(values)
    while values:
        chunk, values = values[:255], values[255:]
        data = [b for v in chunk for b in ((v >> 8) & 0xFF, v & 0xFF)] if words else chunk
        if len(chunk) <= 8:
            out += [(0xB8 if words else 0xB0) + len(chunk) - 1] + data
        else:
            out += [0x41 if words else 0x40, len(chunk)] + data
    return out


def _range_loop(body):
    """Runs body once per point of a range: [start, count] on the stack, body leaves them as it found them."""
    code = body + [SWAP] + _push([1]) + [ADD, SWAP] + _push([1]) + [SUB, DUP]
    back = len(code) + 4  # from the JROT back to the loop's start, over the PUSHW (3 bytes) and SWAP before it
    return code + _push([-back & 0xFFFF], words=True) + [SWAP, JROT, POP, POP]


def _functions():
    # 0 (start, count): flatten the points onto rp0's height
    flatten = _range_loop([SWAP, DUP, ALIGNRP, SWAP])
    # 1 (rows..., start, count): put each point (row - 128) pixels above rp0; the first point's row is on top of the
    # rows, just under start and count
    lift = _range_loop(_push([3]) + [CINDEX] + _push([128]) + [SUB] + _push([4096], words=True) + [MUL]  # row * 64
                       + _push([3]) + [CINDEX, SWAP, MSIRP, ROLL, POP])
    return _push([0]) + [FDEF] + flatten + [ENDF] + _push([1]) + [FDEF] + lift + [ENDF]


def build_font(raster, out_path):
    src = raster.font
    k = 16384 // raster.upem
    upem = raster.upem * k  # 16384 for Verdana: advances scale exactly, so they round as Verdana's own do
    glyph_set = src.getGlyphSet()
    order = src.getGlyphOrder()
    names = [".notdef"] + sorted(set(raster.cmap.values()) - {".notdef"}, key=order.index)
    glyphs, metrics = {}, {}
    most_points = longest_program = deepest_stack = 0
    top_ink = bottom_ink = 0
    for name in names:
        pen = TTGlyphPen(None)
        recording = DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(recording)
        recording.replay(TransformPen(pen, (k, 0, 0, k, 0, 0)))
        outline = pen.glyph()
        if outline.numberOfContours > 0:
            coords, flags = list(outline.coordinates), list(outline.flags)
            ends = list(outline.endPtsOfContours)
        else:
            coords, flags, ends = [], [], []
        verdana_points = len(coords)
        top_ink = max([top_ink] + [y for _, y in coords])
        bottom_ink = min([bottom_ink] + [y for _, y in coords])
        sets = []  # (size, first point, rows + 128 per point)
        for ppem in SIZES:
            rows, left, top = raster.glyph(name, ppem)
            first, lifts = len(coords), []
            for contour in trace(rows, left, top):
                for x, y in contour:
                    coords.append((round(x * upem / ppem), 0))
                    flags.append(1)  # on the curve
                    lifts.append(y + 128)
                    top_ink, bottom_ink = max(top_ink, y * upem // ppem), min(bottom_ink, y * upem // ppem)
                ends.append(len(coords) - 1)
            sets.append((ppem, first, lifts))
        glyph = Glyph()
        glyph.numberOfContours = len(ends)
        program = []
        if coords:
            glyph.coordinates, glyph.flags, glyph.endPtsOfContours = GlyphCoordinates(coords), bytearray(flags), ends
            program = [SVTCA_Y] + _push([len(coords)], words=True) + [SRP0]  # rp0: the origin (phantom point 1)
            for ppem, first, lifts in sets:
                block = []
                if verdana_points:
                    block += _push([0, verdana_points], words=True) + _push([0]) + [CALL]
                if lifts:
                    block += (_push(reversed(lifts)) + _push([first, len(lifts)], words=True) + _push([1]) + [CALL])
                    deepest_stack = max(deepest_stack, len(lifts) + 8)
                if block:
                    program += [MPPEM] + _push([ppem]) + [EQ, IF] + block + [EIF]
            most_points = max(most_points, len(coords))
        glyph.program = ttProgram.Program()
        glyph.program.fromBytecode(bytes(program))
        longest_program = max(longest_program, len(program))
        glyphs[name] = glyph
        metrics[name] = (src["hmtx"][name][0] * k, min((x for x, _ in coords), default=0))

    # line spacing as the original client spaces its lines: the size above the baseline, 2 px below at 11 px
    ascent, descent = upem, round(upem * 2 / 11)
    ps = FAMILY.replace(" ", "") + "-Regular"
    fb = FontBuilder(upem, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap(dict(raster.cmap))
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=-descent, lineGap=0)
    fb.setupNameTable(dict(
        familyName=FAMILY, styleName="Regular", uniqueFontIdentifier=f"{ps};2.0", fullName=FAMILY, psName=ps,
        version="Version 2.000",
        copyright="Built on this computer from its own copy of Verdana (c) Microsoft Corporation. "
                  "For personal use only: do not pass this file on.",
        licenseDescription="Personal use only. Not for distribution.",
        description=f"Verdana as the original Anarchy Online client draws it (monochrome, hinted), as pixels for "
                    f"every size from {SIZES[0]} to {SIZES[-1]} px."))
    os2 = src["OS/2"]
    fb.setupOS2(version=4, sTypoAscender=ascent, sTypoDescender=-descent, sTypoLineGap=0,
                usWinAscent=max(ascent, top_ink), usWinDescent=max(descent, -bottom_ink),
                sxHeight=os2.sxHeight * k, sCapHeight=os2.sCapHeight * k, fsSelection=0x40 | 0x80,
                achVendID="NONE", usWeightClass=400)
    post = src["post"]
    fb.setupPost(isFixedPitch=0, underlinePosition=post.underlinePosition * k,
                 underlineThickness=post.underlineThickness * k)
    now = timestampNow()
    fb.setupHead(unitsPerEm=upem, fontRevision=2.0, lowestRecPPEM=SIZES[0], created=now, modified=now)
    font = fb.font
    font["head"].flags |= 1 << 3  # whole-pixel sizes: a fractional size (UI scaling) snaps to the nearest one
    fpgm = newTable("fpgm")
    fpgm.program = ttProgram.Program()
    fpgm.program.fromBytecode(bytes(_functions()))
    font["fpgm"] = fpgm
    prep = newTable("prep")
    prep.program = ttProgram.Program()
    prep.program.fromBytecode(bytes([SVTCA_Y]))
    font["prep"] = prep
    gasp = newTable("gasp")
    gasp.version, gasp.gaspRange = 1, {0xFFFF: 0x000F}
    font["gasp"] = gasp
    maxp = font["maxp"]
    maxp.maxZones, maxp.maxTwilightPoints, maxp.maxStorage = 2, 0, 0
    maxp.maxFunctionDefs, maxp.maxInstructionDefs = 2, 0
    maxp.maxStackElements, maxp.maxSizeOfInstructions = deepest_stack + 16, longest_program
    font["OS/2"].recalcUnicodeRanges(font)
    font["OS/2"].ulCodePageRange1 = 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(out_path))
    return FAMILY


# --- comparing a Verdana with the original client ---------------------------------------------------------------

def check(path):
    """{size: (matching, total, [differing characters])} against the checksums of the original client's pixels."""
    if not CHECKSUMS.exists():
        return None
    ref = json.loads(CHECKSUMS.read_text())
    raster = Rasteriser(path)
    result = {}
    for size, table in ref["sizes"].items():
        ppem = int(size)
        same, differ = 0, []
        for code, expected in table.items():
            name = raster.cmap.get(int(code, 16))
            if name is None:
                differ.append(chr(int(code, 16)))
                continue
            rows, left, top = raster.glyph(name, ppem)
            if glyph_checksum(rows, left, top, raster.advance(name, ppem)) == expected:
                same += 1
            else:
                differ.append(chr(int(code, 16)))
        result[ppem] = (same, len(table), differ)
    return result


def print_check(result):
    if result is None:
        print("  (no ao-pixels.json beside this script: can't compare)")
        return True
    ok = True
    for ppem, (same, total, differ) in sorted(result.items()):
        line = f"  {ppem} px: {same} of {total} characters give the original client's pixels"
        if differ:
            ok = False
            line += ": different " + "".join(differ[:40]) + (" ..." if len(differ) > 40 else "")
        print(line)
    return ok


def make_checksums(path, sizes):
    """Maintainers: write ao-pixels.json from a Verdana known to give the original pixels (macOS' 5.01, which the
    original client draws with under CrossOver). Checksums only: no glyph shapes go into the repository."""
    raster = Rasteriser(path)
    sizes_out = {}
    for ppem in sizes:
        table = {}
        for code, name in sorted(raster.cmap.items()):
            rows, left, top = raster.glyph(name, ppem)
            table[f"{code:04X}"] = glyph_checksum(rows, left, top, raster.advance(name, ppem))
        sizes_out[str(ppem)] = table
    data = {"about": "Checksums of Verdana's glyphs as the original Anarchy Online client draws them (FreeType v35 "
                     "TrueType hinting, monochrome, advance = rounded unhinted width), from Verdana "
                     f"{_font_names(path)[2]}. Used by `pixelfont.py check`.", "sizes": sizes_out}
    CHECKSUMS.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(f"wrote {CHECKSUMS.name}: {', '.join(f'{s} px: {len(t)} characters' for s, t in sizes_out.items())}")


# --- installing --------------------------------------------------------------------------------------------------

def user_font_dir():
    if sys.platform == "darwin":
        return Path.home() / "Library/Fonts"
    if sys.platform.startswith("win"):
        return Path(os.environ["LOCALAPPDATA"]) / "Microsoft/Windows/Fonts"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "fonts/notum-grotesk"


def _windows_registry(fonts, remove=False):
    import winreg  # Windows only
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts", 0,
                         winreg.KEY_ALL_ACCESS)
    if remove:
        i, stale = 0, []
        while True:
            try:
                value_name = winreg.EnumValue(key, i)[0]
            except OSError:
                break
            if value_name.startswith(FAMILY):
                stale.append(value_name)
            i += 1
        for value_name in stale:
            winreg.DeleteValue(key, value_name)
    else:
        for family, path in fonts:
            winreg.SetValueEx(key, f"{family} (TrueType)", 0, winreg.REG_SZ, str(path))
    winreg.CloseKey(key)
    # tell running programs that the installed fonts changed (WM_FONTCHANGE to all top-level windows)
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)


def install(built, fonts_dir=None):
    target = Path(fonts_dir) if fonts_dir else user_font_dir()
    target.mkdir(parents=True, exist_ok=True)
    placed = []
    for family, path in built:
        dest = target / path.name
        dest.write_bytes(path.read_bytes())
        placed.append((family, dest))
        print(f"installed {family}: {dest}")
    if not fonts_dir:
        if sys.platform.startswith("win"):
            _windows_registry(placed)
        elif sys.platform != "darwin":
            subprocess.run(["fc-cache", "-f", str(target)], check=False)
    print(f"Restart Spiritech, then pick {FAMILY} as the interface font in Options. It is sharp at every size from "
          f"{SIZES[0]} to {SIZES[-1]} px.")


def uninstall(fonts_dir=None):
    target = Path(fonts_dir) if fonts_dir else user_font_dir()
    removed = [target / FILENAME] if (target / FILENAME).is_file() else []
    for path in removed:
        path.unlink()
        print(f"removed {path}")
    if not fonts_dir:
        if sys.platform.startswith("win"):
            _windows_registry([], remove=True)
        elif sys.platform != "darwin" and target.is_dir():
            if not any(target.iterdir()):
                target.rmdir()
            subprocess.run(["fc-cache", "-f"], check=False)
    if not removed:
        print(f"nothing of ours in {target}")


# --- commands ----------------------------------------------------------------------------------------------------

def build_all(args):
    path, version = find_verdana(args.verdana)
    if not path:
        sys.exit(NO_VERDANA)
    print(f"Verdana {version}: {path}")
    print_check(check(path))
    dest = (Path(args.out) if args.out else HERE / "build") / FILENAME
    print(f"Building {FAMILY} ({SIZES[0]} to {SIZES[-1]} px) ...", flush=True)
    family = build_font(Rasteriser(path), dest)
    print(f"  built {family}: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    return [(family, dest)]


def status(args):
    path, version = find_verdana(args.verdana)
    if path:
        print(f"Verdana {version}: {path}")
        print(f"  would build: {FAMILY} ({SIZES[0]} to {SIZES[-1]} px)")
        print_check(check(path))
    else:
        print(NO_VERDANA)
    target = Path(args.fonts_dir) if args.fonts_dir else user_font_dir()
    print(f"{FAMILY} in {target}: {'installed' if (target / FILENAME).is_file() else 'not installed'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     usage="pixelfont.py {status,build,check,install,uninstall} [options]")
    parser.add_argument("command", choices=["status", "build", "check", "install", "uninstall", "checksums"])
    parser.add_argument("--verdana")
    parser.add_argument("--out")
    parser.add_argument("--fonts-dir")
    args = parser.parse_args()
    if args.command != "uninstall":
        _need_packages()
    if args.command == "status":
        status(args)
    elif args.command == "build":
        build_all(args)
    elif args.command == "check":
        path, version = find_verdana(args.verdana)
        if not path:
            sys.exit(NO_VERDANA)
        print(f"Verdana {version}: {path}")
        sys.exit(0 if print_check(check(path)) else 2)
    elif args.command == "install":
        install(build_all(args), args.fonts_dir)
    elif args.command == "uninstall":
        uninstall(args.fonts_dir)
    elif args.command == "checksums":
        if not args.verdana:
            sys.exit("checksums needs --verdana PATH (a Verdana known to give the original pixels)")
        make_checksums(args.verdana, [CHECK_SIZE])


if __name__ == "__main__":
    main()
