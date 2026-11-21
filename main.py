"""Draw the open passport spread of the Republic of Velmora, a country that
isn't there: data page, portrait, machine-readable zone, endorsements and a
travel history in border stamps that all agree with one another.

Python 3.13, standard library only, deterministic. Writes /output/entry.png
(1024x1024). Every printed fact comes from the constants below, and the
machine-readable zone is built from the same constants, so the document
cannot disagree with itself.
"""

import math
import os
import struct
import zlib

W = H = 1024

# ---------------------------------------------------------------- document --
SURNAME = "KOVALIK"
GIVEN = "JANA MARA"
NATIONALITY = "VELMORAN"
DOB = "14 MAY 1989"
POB = "SELIN"
SEX = "F"
ISSUE = "22 APR 2021"
EXPIRY = "22 APR 2031"
DOCNO = "V84 220 517"
AUTHORITY = "MINISTRY OF THE INTERIOR, BRASEN"
ENDORSEMENT = (
    "ENDORSEMENT - THE HOLDER IS A LICENSED GLACIER GUIDE. "
    "MOUNTAIN EQUIPMENT CARRIED FOR PROFESSIONAL USE IS EXEMPT FROM DUTY."
)

# Machine-readable zone: two lines of exactly 44 characters, built from the
# same facts as the printed fields (birth 890514, expiry 310422, sex F).
MRZ1 = "P<VLM" + SURNAME + "<<" + GIVEN.replace(" ", "<")
MRZ1 = (MRZ1 + "<" * 44)[:44]
_MRZ2_PARTS = "V84220517" + "<" + "4" + "VLM" + "890514" + "2" + SEX + "310422" + "6"
MRZ2 = _MRZ2_PARTS + "<" * (44 - len(_MRZ2_PARTS) - 2) + "08"
assert len(MRZ1) == 44 and len(MRZ2) == 44

# -------------------------------------------------------------------- font --
# One hand-coded 5x7 bitmap font: capitals, digits, basic punctuation.
# Glyphs are written as string art (the picture reads exactly as the letter
# appears on the page) and compiled to row bitmasks, bit 4 = leftmost pixel.
FONT_ART = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", "#.#..", ".#..."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "...#.", "..#..", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#####", "...#.", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "—": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "·": (".....", ".....", ".....", "..#..", ".....", ".....", "....."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "'": ("..#..", "..#..", "...#.", ".....", ".....", ".....", "....."),
}
FONT = {ch: tuple(int(r.replace("#", "1").replace(".", "0"), 2) for r in rows)
        for ch, rows in FONT_ART.items()}

# ------------------------------------------------------------------ canvas --
class Img:
    """An RGB canvas; optionally carries an alpha channel (stamp buffers)."""

    def __init__(self, w, h, color=(0, 0, 0), alpha=False):
        self.w = w
        self.h = h
        self.d = bytearray(bytes(color) * (w * h))
        self.a = bytearray(w * h) if alpha else None


def px(img, x, y, c, a=1.0):
    if 0 <= x < img.w and 0 <= y < img.h:
        i = (y * img.w + x) * 3
        if img.a is not None:
            na = int(a * 255)
            j = y * img.w + x
            if na >= img.a[j]:
                img.d[i] = c[0]
                img.d[i + 1] = c[1]
                img.d[i + 2] = c[2]
                img.a[j] = na
        elif a >= 1.0:
            img.d[i] = c[0]
            img.d[i + 1] = c[1]
            img.d[i + 2] = c[2]
        else:
            ia = 1.0 - a
            img.d[i] = int(img.d[i] * ia + c[0] * a)
            img.d[i + 1] = int(img.d[i + 1] * ia + c[1] * a)
            img.d[i + 2] = int(img.d[i + 2] * ia + c[2] * a)


def rect(img, x, y, w, h, c, a=1.0):
    x0 = max(0, int(x))
    y0 = max(0, int(y))
    x1 = min(img.w, int(x) + int(w))
    y1 = min(img.h, int(y) + int(h))
    if x1 <= x0 or y1 <= y0:
        return
    if img.a is None and a >= 1.0:
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * img.w + x0) * 3
            img.d[i:i + len(row)] = row
    else:
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                px(img, xx, yy, c, a)


def ellipse(img, cx, cy, rx, ry, c, a=1.0):
    if rx < 0.6 or ry < 0.6:
        px(img, int(cx), int(cy), c, a)
        return
    m = min(rx, ry)
    for yy in range(int(cy - ry - 1), int(cy + ry + 1) + 1):
        for xx in range(int(cx - rx - 1), int(cx + rx + 1) + 1):
            dx = (xx - cx) / rx
            dy = (yy - cy) / ry
            d = math.sqrt(dx * dx + dy * dy)
            if d < 1.15:
                cov = (1.0 - d) * m + 0.6
                if cov > 0:
                    px(img, xx, yy, c, a * min(1.0, cov))


def erase_ellipse(img, cx, cy, rx, ry):
    """Clear the alpha channel inside an ellipse (stamp ring carving)."""
    for yy in range(int(cy - ry - 1), int(cy + ry + 1) + 1):
        for xx in range(int(cx - rx - 1), int(cx + rx + 1) + 1):
            if 0 <= xx < img.w and 0 <= yy < img.h:
                dx = (xx - cx) / rx
                dy = (yy - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    img.a[yy * img.w + xx] = 0


def line(img, x0, y0, x1, y1, c, th=1, a=1.0):
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    r = th / 2.0
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        if th <= 1.4:
            px(img, int(round(x)), int(round(y)), c, a)
        else:
            ellipse(img, x, y, r, r, c, a)


def poly(img, pts, c, a=1.0):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(pts)
    for yy in range(int(min(ys)), int(max(ys)) + 1):
        for xx in range(int(min(xs)), int(max(xs)) + 1):
            inside = False
            j = n - 1
            for i in range(n):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > yy) != (yj > yy) and xx < (xj - xi) * (yy - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
            if inside:
                px(img, xx, yy, c, a)


def blit(dst, src, dx, dy, a=1.0):
    for sy in range(src.h):
        for sx in range(src.w):
            sa = src.a[sy * src.w + sx] / 255.0 if src.a is not None else 1.0
            if sa <= 0:
                continue
            i = (sy * src.w + sx) * 3
            px(dst, dx + sx, dy + sy, (src.d[i], src.d[i + 1], src.d[i + 2]), a * sa)


def blit_scale(dst, src, dx, dy, dw, dh, a=1.0):
    for yy in range(dh):
        sy = yy * src.h // dh
        for xx in range(dw):
            sx = xx * src.w // dw
            sa = src.a[sy * src.w + sx] / 255.0 if src.a is not None else 1.0
            if sa <= 0:
                continue
            i = (sy * src.w + sx) * 3
            px(dst, dx + xx, dy + yy, (src.d[i], src.d[i + 1], src.d[i + 2]), a * sa)


def blit_rot(dst, src, cx, cy, deg, a=1.0):
    """Blit a stamp buffer rotated about (cx, cy), with uneven ink."""
    rad = math.radians(deg)
    cosr = math.cos(rad)
    sinr = math.sin(rad)
    hw = src.w / 2.0
    hh = src.h / 2.0
    R = math.hypot(hw, hh)
    for yy in range(int(cy - R), int(cy + R) + 1):
        for xx in range(int(cx - R), int(cx + R) + 1):
            ox = xx - cx
            oy = yy - cy
            sx = ox * cosr + oy * sinr + hw
            sy = -ox * sinr + oy * cosr + hh
            ix = int(sx)
            iy = int(sy)
            if 0 <= ix < src.w and 0 <= iy < src.h:
                sa = src.a[iy * src.w + ix] / 255.0 if src.a is not None else 1.0
                if sa <= 0:
                    continue
                n = ((ix * 73856093) ^ (iy * 19349663)) & 0xFF
                f = 0.84 + (n % 20) / 100.0
                i = (iy * src.w + ix) * 3
                px(dst, xx, yy, (src.d[i], src.d[i + 1], src.d[i + 2]),
                   a * sa * min(1.0, f))


# -------------------------------------------------------------------- text --
def text_w(s, scale, track=0):
    return len(s) * (6 * scale + track)


def draw_text(img, x, y, s, scale, c, a=1.0, track=0, bold=False):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = g[row]
            if not bits:
                continue
            for col in range(5):
                if (bits >> (4 - col)) & 1:
                    rect(img, cx + col * scale, y + row * scale, scale, scale, c, a)
                    if bold:
                        rect(img, cx + col * scale + max(1, scale // 2),
                             y + row * scale, scale, scale, c, a)
        cx += 6 * scale + track
    return cx - x


def draw_text_c(img, cx, y, s, scale, c, a=1.0, track=0, bold=False):
    return draw_text(img, cx - text_w(s, scale, track) // 2, y, s, scale, c, a, track, bold)


def wrap(s, scale, maxw):
    words = s.split()
    lines = []
    cur = ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if text_w(t, scale) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


INK = (32, 32, 40)
LAB = (100, 112, 132)
RULEC = (178, 174, 160)


def field(img, x, y, label, value, w, vscale=2):
    """A label over a value with a hairline under it."""
    draw_text(img, x, y, label, 1, LAB)
    draw_text(img, x, y + 11, value, vscale, INK)
    rect(img, x, y + 33, w, 1, RULEC)


# ----------------------------------------------------------------- emblem --
def emblem(img, cx, top):
    """Line-drawn twin mountain peaks with a star, in slate blue-grey."""
    c = (58, 66, 88)
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = 11 if i % 2 == 0 else 4.6
        pts.append((cx + r * math.cos(ang), top + 11 + r * math.sin(ang)))
    poly(img, pts, c)
    line(img, cx - 34, top + 58, cx - 12, top + 22, c, 3)
    line(img, cx - 12, top + 22, cx + 8, top + 58, c, 3)
    line(img, cx - 4, top + 58, cx + 12, top + 32, c, 3)
    line(img, cx + 12, top + 32, cx + 30, top + 58, c, 3)
    rect(img, cx - 36, top + 58, 72, 2, c)


# --------------------------------------------------------------- portrait --
def make_portrait():
    """A drawn ID portrait, 190x250, rendered once into its own buffer."""
    p = Img(190, 250, (148, 158, 172))
    for yy in range(250):  # photo background, slight vertical gradient
        t = yy / 250
        rect(p, 0, yy, 190, 1,
             (int(152 - 14 * t), int(162 - 14 * t), int(176 - 13 * t)))
    hair = (96, 62, 38)
    skin = (237, 199, 169)
    shade = (208, 163, 128)
    ellipse(p, 95, 112, 64, 88, hair)                    # hair mass behind
    ellipse(p, 95, 232, 88, 52, (50, 48, 64))            # shoulders / blouse
    rect(p, 0, 214, 190, 36, (50, 48, 64))
    ellipse(p, 95, 238, 60, 30, (59, 57, 75), 0.5)       # blouse shading
    rect(p, 84, 148, 22, 42, (216, 174, 140))            # neck
    ellipse(p, 95, 152, 12, 8, (200, 155, 120), 0.6)     # neck shadow
    ellipse(p, 95, 104, 47, 61, skin)                    # face
    ellipse(p, 95, 50, 50, 28, hair)                     # fringe / hairline
    ellipse(p, 46, 128, 13, 52, hair)                    # side strands
    ellipse(p, 144, 128, 13, 52, hair)
    ellipse(p, 66, 132, 10, 6, (232, 170, 150), 0.25)    # blush
    ellipse(p, 124, 132, 10, 6, (232, 170, 150), 0.25)
    line(p, 68, 99, 85, 96, (84, 55, 34), 3)             # brows
    line(p, 105, 96, 122, 99, (84, 55, 34), 3)
    for ex in (76, 114):                                 # eyes
        ellipse(p, ex, 110, 9, 5, (250, 248, 245))
        ellipse(p, ex, 110, 4, 4, (96, 64, 38))
        ellipse(p, ex, 110, 2, 2, (20, 16, 12))
        px(p, ex + 1, 108, (255, 255, 255))
        line(p, ex - 9, 108, ex + 9, 107, (60, 40, 30), 2)
    line(p, 96, 114, 93, 128, shade, 2)                  # nose
    ellipse(p, 88, 131, 2, 1.5, shade)
    ellipse(p, 100, 131, 2, 1.5, shade)
    ellipse(p, 95, 147, 13, 5, (188, 108, 102))          # lips
    line(p, 84, 147, 106, 147, (158, 80, 76), 1)
    return p


def signature(img, x, y):
    """A cursive-looking scrawl in dark blue ink."""
    c = (38, 48, 92)
    pts = []
    for t in range(60):
        xx = x + t * 3.1
        yy = y - 8 * math.sin(t * 0.32) - 5 * math.sin(t * 0.13 + 1.2) - 3 * math.cos(t * 0.53)
        pts.append((xx, yy))
    for i in range(len(pts) - 1):
        line(img, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c, 2, 0.85)
    line(img, x + 186, y + 4, x + 8, y + 15, c, 2, 0.6)  # flourish


# ----------------------------------------------------------------- stamps --
def stamp_rect(lines, ink, w=308, h=116):
    s = Img(w, h, (0, 0, 0), alpha=True)
    for inset, th in ((3, 4), (10, 2)):
        rect(s, inset, inset, w - 2 * inset, th, ink, 0.88)
        rect(s, inset, h - inset - th, w - 2 * inset, th, ink, 0.88)
        rect(s, inset, inset, th, h - 2 * inset, ink, 0.88)
        rect(s, w - inset - th, inset, th, h - 2 * inset, ink, 0.88)
    total = sum(sc * 7 for _, sc, _ in lines) + 7 * (len(lines) - 1)
    yy = (h - total) // 2
    for txt, sc, b in lines:
        draw_text_c(s, w // 2, yy, txt, sc, ink, 0.88, bold=bool(b))
        yy += sc * 7 + 7
    return s


def stamp_oval(lines, ink, w=300, h=150):
    s = Img(w, h, (0, 0, 0), alpha=True)
    cx, cy = w / 2, h / 2
    ellipse(s, cx, cy, w / 2 - 3, h / 2 - 3, ink, 0.88)
    erase_ellipse(s, cx, cy, w / 2 - 8, h / 2 - 8)
    ellipse(s, cx, cy, w / 2 - 13, h / 2 - 13, ink, 0.88)
    erase_ellipse(s, cx, cy, w / 2 - 17, h / 2 - 17)
    total = sum(sc * 7 for _, sc, _ in lines) + 7 * (len(lines) - 1)
    yy = int(cy - total / 2)
    for txt, sc, b in lines:
        draw_text_c(s, w // 2, yy, txt, sc, ink, 0.88, bold=bool(b))
        yy += sc * 7 + 7
    return s


def visa_label(img):
    """One neat, unrotated Thessia visitor-visa label on the right page."""
    x, y, w, h = 576, 108, 360, 92
    ink = (70, 80, 110)
    txt = (40, 44, 60)
    rect(img, x, y, w, 2, ink)
    rect(img, x, y + h - 2, w, 2, ink)
    rect(img, x, y, 2, h, ink)
    rect(img, x + w - 2, y, 2, h, ink)
    rect(img, x + 5, y + 5, w - 10, 1, ink)
    rect(img, x + 5, y + h - 6, w - 10, 1, ink)
    rect(img, x + 5, y + 5, 1, h - 10, ink)
    rect(img, x + w - 6, y + 5, 1, h - 10, ink)
    draw_text_c(img, x + w // 2, y + 14, "THESSIA", 2, txt)
    draw_text_c(img, x + w // 2, y + 38, "VISITOR VISA · SINGLE ENTRY", 2, txt)
    draw_text_c(img, x + w // 2, y + 62, "FEE PAID", 2, txt)


# -------------------------------------------------------------- guilloche --
def guilloche(img, x0, y0, w, h):
    c = (172, 178, 202)
    for i in range(15):
        base = y0 + 34 + i * 60
        ph = i * 1.37
        for xx in range(x0 + 8, x0 + w - 8, 3):
            yy = base + 9 * math.sin((xx - x0) * 0.021 + ph) + 5 * math.sin((xx - x0) * 0.006 + ph * 2.0)
            if y0 + 6 < yy < y0 + h - 6:
                px(img, xx, int(yy), c, 0.10)
    for i in range(15):
        base = y0 + 62 + i * 60
        ph = i * 0.91 + 2.0
        for xx in range(x0 + 8, x0 + w - 8, 3):
            yy = base + 9 * math.sin((xx - x0) * 0.019 + ph) + 5 * math.cos((xx - x0) * 0.005 + ph)
            if y0 + 6 < yy < y0 + h - 6:
                px(img, xx, int(yy), c, 0.07)


# ------------------------------------------------------------------ pages --
def left_page(img):
    emblem(img, 88, 50)
    draw_text(img, 140, 62, "REPUBLIC OF VELMORA", 3, (44, 48, 64))
    draw_text(img, 140, 92, "REPUBLIKA VELMORA · PASSPORT", 2, (90, 96, 116))
    rect(img, 48, 132, 440, 2, (150, 144, 128))
    rect(img, 48, 137, 440, 1, (196, 190, 170))

    port = make_portrait()
    blit(img, port, 48, 156)
    bc = (110, 112, 118)
    rect(img, 48, 156, 190, 1, bc)
    rect(img, 48, 405, 190, 1, bc)
    rect(img, 48, 156, 1, 250, bc)
    rect(img, 237, 156, 1, 250, bc)

    field(img, 256, 156, "TYPE", "P", 96)
    field(img, 376, 156, "CODE", "VLM", 112)
    field(img, 256, 198, "PASSPORT NO", DOCNO, 232)
    field(img, 256, 240, "NATIONALITY", NATIONALITY, 232)
    field(img, 256, 282, "DATE OF BIRTH", DOB, 232)
    field(img, 256, 324, "PLACE OF BIRTH", POB, 232)
    field(img, 256, 366, "SEX", SEX, 232)

    field(img, 48, 430, "SURNAME", SURNAME, 200)
    field(img, 264, 430, "GIVEN NAMES", GIVEN, 224)
    field(img, 48, 474, "DATE OF ISSUE", ISSUE, 200)
    field(img, 264, 474, "DATE OF EXPIRY", EXPIRY, 224)
    field(img, 48, 518, "ISSUING AUTHORITY", AUTHORITY, 440)

    # The one telling detail: a printed endorsement in a ruled box.
    bc2 = (150, 148, 138)
    rect(img, 48, 566, 440, 1, bc2)
    rect(img, 48, 697, 440, 1, bc2)
    rect(img, 48, 566, 1, 132, bc2)
    rect(img, 487, 566, 1, 132, bc2)
    yy = 582
    for ln in wrap(ENDORSEMENT, 2, 412):
        draw_text(img, 64, yy, ln, 2, (42, 42, 50))
        yy += 21

    signature(img, 58, 762)
    rect(img, 48, 796, 252, 1, RULEC)
    draw_text(img, 48, 804, "HOLDER'S SIGNATURE", 1, LAB)
    blit_scale(img, port, 392, 726, 84, 110, 0.15)  # ghost portrait


def right_page(img):
    draw_text(img, 536, 60, "VISAS", 2, LAB)
    draw_text(img, 940, 60, "12", 2, LAB)
    rect(img, 536, 84, 440, 1, (196, 190, 170))
    visa_label(img)

    blue = (38, 64, 150)
    violet = (108, 58, 148)
    red = (148, 36, 42)
    k_in = stamp_rect([("KORDANIA", 3, 0), ("MERIDIAN AIRPORT", 2, 0),
                       ("ENTRY", 3, 1), ("03 JUN 2022", 2, 0)], blue)
    k_out = stamp_rect([("KORDANIA", 3, 0), ("MERIDIAN AIRPORT", 2, 0),
                        ("EXIT", 3, 1), ("11 JUN 2022", 2, 0)], blue)
    t_in = stamp_oval([("THESSIA", 3, 0), ("PORT OF LUMEN", 2, 0),
                       ("ENTRY", 3, 1), ("28 SEP 2023", 2, 0)], violet)
    t_out = stamp_oval([("THESSIA", 3, 0), ("PORT OF LUMEN", 2, 0),
                        ("EXIT", 3, 1), ("05 OCT 2023", 2, 0)], violet)
    m_in = stamp_rect([("MAROVIA", 3, 0), ("HIGH PASS BORDER POST", 2, 0),
                       ("ENTRY", 3, 1), ("17 JAN 2024", 2, 0)], red, w=344)
    blit_rot(img, k_in, 690, 296, -6)
    blit_rot(img, k_out, 806, 432, 4)
    blit_rot(img, t_in, 688, 584, 3)
    blit_rot(img, t_out, 812, 700, -5)
    blit_rot(img, m_in, 700, 826, 2)


def compose():
    img = Img(W, H, (40, 41, 45))
    for yy in range(H):  # dark neutral surround, gentle vertical gradient
        t = yy / H
        rect(img, 0, yy, W, 1,
             (int(52 - 14 * t), int(53 - 14 * t), int(57 - 15 * t)))
    for k in range(9, 0, -1):  # soft shadow under the open book
        rect(img, 24 - k * 2, 40 + k * 2, 976 + k * 4, 944, (0, 0, 0), 0.05)
    paper = (244, 239, 226)
    rect(img, 24, 40, 488, 944, paper)
    rect(img, 512, 40, 488, 944, paper)
    rect(img, 994, 40, 6, 944, (228, 220, 198))   # page-edge shading
    rect(img, 24, 978, 976, 6, (230, 222, 200))
    guilloche(img, 24, 40, 488, 944)
    guilloche(img, 512, 40, 488, 944)
    for dx in range(-22, 23):  # centre gutter shadow
        a = 0.17 * (1 - abs(dx) / 22.0)
        rect(img, 512 + dx, 40, 1, 944, (30, 28, 24), a)
    rect(img, 511, 40, 2, 944, (60, 55, 45), 0.25)

    left_page(img)
    right_page(img)

    # Machine-readable zone across the very bottom of the spread.
    rect(img, 24, 912, 976, 72, (238, 231, 210))
    rect(img, 24, 912, 976, 1, (196, 188, 164))
    draw_text(img, 50, 924, MRZ1, 2, (36, 36, 36), track=9)
    draw_text(img, 50, 950, MRZ2, 2, (36, 36, 36), track=9)

    oc = (170, 160, 140)  # book outline, drawn last
    rect(img, 24, 40, 976, 1, oc)
    rect(img, 24, 983, 976, 1, oc)
    rect(img, 24, 40, 1, 944, oc)
    rect(img, 999, 40, 1, 944, oc)
    return img


# -------------------------------------------------------------------- png --
def save_png(img, path):
    raw = bytearray()
    d = img.d
    w3 = img.w * 3
    prev = bytes(w3)
    for yy in range(img.h):
        row = bytes(d[yy * w3:(yy + 1) * w3])
        filt = bytearray(w3)
        for i in range(w3):
            left = row[i - 3] if i >= 3 else 0
            filt[i] = (row[i] - left) & 0xFF
        raw.append(1)
        raw += filt
        prev = row
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", img.w, img.h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", comp)
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def main():
    img = compose()
    os.makedirs("/output", exist_ok=True)
    save_png(img, "/output/entry.png")


if __name__ == "__main__":
    main()
