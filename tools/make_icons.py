#!/usr/bin/env python3
"""Generate the site's logo and icon files from assets/src/logo-source.jpg.
Pure Python (zlib only) plus macOS `sips` for the JPEG decode - no other tools needed.

    python3 tools/make_icons.py

Writes:
    assets/logo.png             transparent black logo (header, footer)
    assets/favicon-32.png       32x32, transparent
    assets/apple-touch-icon.png 180x180 on the site background (iOS needs opaque)
    assets/og-image.png         1200x630 link-preview image, logo on the site background
"""
import struct, subprocess, sys, tempfile, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "src" / "logo-source.jpg"
PAPER = (0xF9, 0xFB, 0xFA)   # --paper
LINE = (0xD3, 0xDB, 0xD6)    # --line


# ---------- PNG read / write ----------

def read_png(path):
    d = Path(path).read_bytes()
    assert d[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, w = 8, [], None
    while pos < len(d):
        ln = struct.unpack(">I", d[pos:pos + 4])[0]
        typ, body = d[pos + 4:pos + 8], d[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and ctype in (2, 6) and interlace == 0, f"unsupported PNG (depth {depth}, type {ctype})"
            bpp = 3 if ctype == 2 else 4
        elif typ == b"IDAT":
            idat.append(body)
        pos += 12 + ln
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[p]; p += 1
        cur = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(bpp, stride): cur[i] = (cur[i] + cur[i - bpp]) & 255
        elif f == 2:
            for i in range(stride): cur[i] = (cur[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = cur[i - bpp] if i >= bpp else 0
                cur[i] = (cur[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = cur[i - bpp] if i >= bpp else 0
                b = prev[i]; c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                cur[i] = (cur[i] + pred) & 255
        rows.append(cur); prev = cur
    return w, h, bpp, rows


def write_png(path, w, h, rows, alpha):
    ctype = 6 if alpha else 2
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    Path(path).write_bytes(png)


# ---------- logo mask ----------

def logo_mask(w, h, bpp, rows):
    """Darkness -> alpha. Anything lighter than LIGHT is dropped (kills the JPEG's soft shadow),
    anything darker than DARK is fully opaque, in between is the anti-aliased edge."""
    LIGHT, DARK, CORE, REACH = 185.0, 45.0, 60.0, 3
    lums = []
    for r in rows:
        lums.append([0.299 * r[x * bpp] + 0.587 * r[x * bpp + 1] + 0.114 * r[x * bpp + 2] for x in range(w)])
    # The source JPEG has a soft drop shadow (mid-gray, never black). Keep only pixels within
    # REACH px of a near-black "core" pixel, so the shadow is dropped but anti-aliased edges survive.
    core = [[1 if v < CORE else 0 for v in row] for row in lums]
    horiz = [[max(row[max(0, x - REACH):x + REACH + 1]) for x in range(w)] for row in core]
    near = [[max(horiz[yy][x] for yy in range(max(0, y - REACH), min(h, y + REACH + 1))) for x in range(w)] for y in range(h)]
    mask = []
    for y in range(h):
        m = []
        for x in range(w):
            lum = lums[y][x]
            a = min(1.0, max(0.0, (LIGHT - lum) / (LIGHT - DARK))) if near[y][x] else 0.0
            m.append(a)
        mask.append(m)
    xs = [x for m in mask for x, v in enumerate(m) if v > 0.05]
    ys = [y for y, m in enumerate(mask) if max(m) > 0.05]
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    pad = max(2, int(0.02 * max(x1 - x0, y1 - y0)))
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(w, x1 + pad), min(h, y1 + pad)
    return [m[x0:x1] for m in mask[y0:y1]]


def resize(mask, nw, nh):
    """Area-averaging resample of a 2-D float mask (summed-area table, exact box filter)."""
    h, w = len(mask), len(mask[0])
    sat = [[0.0] * (w + 1) for _ in range(h + 1)]
    for y in range(h):
        acc, row, out = 0.0, mask[y], sat[y + 1]
        up = sat[y]
        for x in range(w):
            acc += row[x]
            out[x + 1] = up[x + 1] + acc

    def area(x0, y0, x1, y1):
        return sat[y1][x1] - sat[y0][x1] - sat[y1][x0] + sat[y0][x0]

    res = []
    for j in range(nh):
        sy0, sy1 = j * h / nh, (j + 1) * h / nh
        iy0, iy1 = int(sy0), min(h, int(sy1) + 1)
        row = []
        for i in range(nw):
            sx0, sx1 = i * w / nw, (i + 1) * w / nw
            ix0, ix1 = int(sx0), min(w, int(sx1) + 1)
            # integer-box approximation is fine at these ratios; normalise by the box actually summed
            row.append(area(ix0, iy0, ix1, iy1) / ((ix1 - ix0) * (iy1 - iy0)))
        res.append(row)
    return res


def fit(mask, box_w, box_h):
    h, w = len(mask), len(mask[0])
    s = min(box_w / w, box_h / h)
    return resize(mask, max(1, round(w * s)), max(1, round(h * s)))


def canvas(w, h, bg):
    return [bytearray(bg * w) for _ in range(h)]


def blit_black(rows, mask, ox, oy, alpha):
    """Paint the mask as black onto rows (RGBA if alpha else RGB) at offset."""
    bpp = 4 if alpha else 3
    for j, m in enumerate(mask):
        r = rows[oy + j]
        for i, a in enumerate(m):
            if a <= 0.002:
                continue
            k = (ox + i) * bpp
            if alpha:
                r[k] = r[k + 1] = r[k + 2] = 0
                r[k + 3] = max(r[k + 3], round(a * 255))
            else:
                for c in range(3):
                    r[k + c] = round(r[k + c] * (1 - a))


def rect_outline(rows, x0, y0, x1, y1, color, thick=2):
    for y in range(y0, y1):
        r = rows[y]
        for x in range(x0, x1):
            if x < x0 + thick or x >= x1 - thick or y < y0 + thick or y >= y1 - thick:
                k = x * 3
                r[k], r[k + 1], r[k + 2] = color


def main():
    if not SRC.exists():
        sys.exit(f"missing {SRC.relative_to(ROOT)}")
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "logo.png"
        subprocess.run(["sips", "-s", "format", "png", str(SRC), "--out", str(png)], check=True, capture_output=True)
        w, h, bpp, rows = read_png(png)
    mask = logo_mask(w, h, bpp, rows)
    mh, mw = len(mask), len(mask[0])
    print(f"logo bounding box {mw}x{mh} (from {w}x{h})")

    out = ROOT / "assets"

    m = fit(mask, 800, 800)
    c = canvas(len(m[0]), len(m), (0, 0, 0, 0))
    blit_black(c, m, 0, 0, True)
    write_png(out / "logo.png", len(m[0]), len(m), c, True)
    print(f"wrote assets/logo.png {len(m[0])}x{len(m)}")

    m = fit(mask, 32, 32)
    c = canvas(32, 32, (0, 0, 0, 0))
    blit_black(c, m, (32 - len(m[0])) // 2, (32 - len(m)) // 2, True)
    write_png(out / "favicon-32.png", 32, 32, c, True)
    print("wrote assets/favicon-32.png 32x32")

    m = fit(mask, 148, 148)
    c = canvas(180, 180, PAPER)
    blit_black(c, m, (180 - len(m[0])) // 2, (180 - len(m)) // 2, False)
    write_png(out / "apple-touch-icon.png", 180, 180, c, False)
    print("wrote assets/apple-touch-icon.png 180x180")

    m = fit(mask, 560, 300)
    c = canvas(1200, 630, PAPER)
    rect_outline(c, 120, 120, 1080, 510, LINE)
    blit_black(c, m, (1200 - len(m[0])) // 2, (630 - len(m)) // 2, False)
    write_png(out / "og-image.png", 1200, 630, c, False)
    print("wrote assets/og-image.png 1200x630")


if __name__ == "__main__":
    main()
