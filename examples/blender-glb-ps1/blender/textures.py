"""Pixel-art texture set for ПОСЛЕДНЯЯ СМЕНА (run with system Python: python blender/textures.py).

Every texture is painted at ~32 px per metre, 8-bit, no smoothing, so after the
375 px internal render the texels stay visible as chunky PS1-era pixels.
Colours are deliberately muddy: mustard plastic, teal-olive paint, rust, gunmetal.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "tex")
FONT = os.path.join(HERE, "..", "assets", "fonts", "PressStart2P.ttf")
os.makedirs(OUT, exist_ok=True)

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.47


def rng(seed):
    return np.random.default_rng(seed)


def vnoise(w, h, cell, r, tile=True):
    """value noise, bilinear between random lattice points (tileable)"""
    gw, gh = max(1, w // cell), max(1, h // cell)
    g = r.random((gh + 1, gw + 1))
    if tile:
        g[-1, :] = g[0, :]
        g[:, -1] = g[:, 0]
    ys = np.linspace(0, gh, h, endpoint=False)
    xs = np.linspace(0, gw, w, endpoint=False)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def fbm(w, h, r, cells=(16, 8, 4, 2), amps=(0.5, 0.25, 0.15, 0.1)):
    n = np.zeros((h, w))
    for c, a in zip(cells, amps):
        n += vnoise(w, h, c, r) * a
    return n / sum(amps)


def hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def dither(img, levels=24):
    """ordered dither every channel to a coarse ramp: the 'printed' PS1 texture look"""
    h, w, _ = img.shape
    t = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    step = 255.0 / levels
    return np.clip(np.floor(img / step + 0.5 + t * 0.9) * step, 0, 255)


def base(w, h, col, r, var=0.10, cells=(16, 8, 4, 2)):
    n = fbm(w, h, r, cells)
    img = np.zeros((h, w, 3)) + hexc(col)
    img *= (1 - var + 2 * var * n)[..., None]
    return img


def grime(img, r, amt=0.35, cell=8, bottom=0.0, streaks=0.0):
    h, w, _ = img.shape
    n = fbm(w, h, r, (cell * 2, cell, max(2, cell // 2)))
    m = np.clip((n - 0.45) * 2.2, 0, 1) * amt
    if bottom:
        m += np.linspace(0, 1, h)[:, None] ** 3 * bottom
    if streaks:
        cols = r.random(w) < 0.18
        lens = r.integers(h // 6, h // 2, w)
        for x in np.nonzero(cols)[0]:
            l = lens[x]
            m[:l, x] += np.linspace(streaks, 0, l)
    m = np.clip(m, 0, 0.85)[..., None]
    dirt = hexc("#2a2418")
    return img * (1 - m) + dirt * m


def speckle(img, r, p=0.04, amt=40):
    h, w, _ = img.shape
    s = (r.random((h, w)) < p) * (r.random((h, w)) - 0.5) * 2 * amt
    return img + s[..., None]


def scratches(img, r, n=10, col="#c8c0a8", alpha=0.35):
    h, w, _ = img.shape
    c = hexc(col)
    for _ in range(n):
        x, y = r.integers(0, w), r.integers(0, h)
        dx, dy = r.choice([-1, 0, 1]), r.choice([-1, 1])
        for k in range(r.integers(3, 9)):
            xx, yy = (x + dx * k) % w, (y + dy * k // 2) % h
            img[yy, xx] = img[yy, xx] * (1 - alpha) + c * alpha
    return img


def line(img, y0, y1, x0, x1, col, a=1.0):
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + hexc(col) * a


def rivet(img, x, y, light="#d8d0b0", dark="#1a1712"):
    h, w, _ = img.shape
    img[y % h, x % w] = hexc(light)
    img[(y + 1) % h, (x + 1) % w] = hexc(dark)
    img[y % h, (x + 1) % w] = (hexc(light) + hexc(dark)) / 2


def save(name, img, lv=28):
    img = dither(np.clip(img, 0, 255), lv).astype(np.uint8)
    Image.fromarray(img, "RGB").save(os.path.join(OUT, name + ".png"))


def font(size=8):
    return ImageFont.truetype(FONT, size)


# ---------------------------------------------------------------- walls
def wall_panel():
    """2 m x 2 m: mustard-beige plastic cladding, two horizontal panels, seams, rivets, streaks"""
    r = rng(11)
    w = h = 64
    img = base(w, h, "#9c8c66", r, 0.07)
    # horizontal band split at 2/3 height: upper panel slightly lighter
    img[:22] *= 1.06
    for y in (0, 22, 63):
        line(img, y, y + 1, 0, w, "#3a3326", 0.9)
        line(img, (y + 1) % h, (y + 1) % h + 1, 0, w, "#c9b98e", 0.5)
    for x in (0, 32):
        line(img, 0, h, x, x + 1, "#3a3326", 0.85)
        line(img, 0, h, x + 1, x + 2, "#c4b48a", 0.35)
    for x in (4, 28, 36, 60):
        for y in (3, 19, 26, 59):
            rivet(img, x, y)
    img = grime(img, r, 0.32, 8, bottom=0.25, streaks=0.35)
    img = scratches(img, r, 14)
    img = speckle(img, r, 0.05, 22)
    save("wall_panel", img)


def wall_teal():
    """2 m x 2 m: painted teal-olive metal with vertical ribs (machinery rooms)"""
    r = rng(12)
    w = h = 64
    img = base(w, h, "#4d6862", r, 0.09)
    for x in range(0, w, 8):
        line(img, 0, h, x, x + 1, "#22302c", 0.7)
        line(img, 0, h, x + 1, x + 2, "#7d9a90", 0.35)
        line(img, 0, h, x + 6, x + 7, "#2b3a36", 0.35)
    line(img, 0, 1, 0, w, "#151d1b", 1)
    line(img, 31, 33, 0, w, "#1b2422", 0.9)
    line(img, 33, 34, 0, w, "#86a399", 0.4)
    # paint chips -> rust
    n = fbm(w, h, r, (8, 4, 2))
    chip = (n > 0.72)[..., None]
    img = np.where(chip, hexc("#6e3d22") * (0.7 + 0.5 * n[..., None]), img)
    img = grime(img, r, 0.38, 8, bottom=0.35, streaks=0.4)
    img = speckle(img, r, 0.06, 26)
    save("wall_teal", img)


def wall_lower():
    """2 m x 1 m kick plate: dark worn diamond plate"""
    r = rng(13)
    w, h = 64, 32
    img = base(w, h, "#3d3b37", r, 0.08)
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            ox = 2 if (y // 4) % 2 else 0
            xx = (x + ox) % w
            img[y + 1, xx] = hexc("#6d6a62")
            img[y + 2, (xx + 1) % w] = hexc("#24221f")
    line(img, 0, 1, 0, w, "#7a766b", 0.6)
    line(img, h - 1, h, 0, w, "#141312", 1)
    img = grime(img, r, 0.4, 8, bottom=0.4)
    save("wall_lower", img)


def ceiling():
    """2 m x 2 m: grimy ceiling panel with vent slots"""
    r = rng(14)
    w = h = 64
    img = base(w, h, "#6d6858", r, 0.08)
    line(img, 0, 1, 0, w, "#24211a", 1); line(img, 0, h, 0, 1, "#24211a", 1)
    line(img, 32, 33, 0, w, "#2c281f", 0.8); line(img, 0, h, 32, 33, "#2c281f", 0.8)
    for y in range(40, 56, 3):
        line(img, y, y + 1, 40, 56, "#151410", 0.95)
    img = grime(img, r, 0.45, 8)
    img = speckle(img, r, 0.05, 20)
    save("ceiling", img)


# ---------------------------------------------------------------- floors
def floor_grate():
    r = rng(21)
    w = h = 64
    img = base(w, h, "#2f2d2a", r, 0.1)
    for y in range(0, h, 4):
        line(img, y, y + 1, 0, w, "#0d0c0b", 0.95)
    for x in range(0, w, 4):
        line(img, 0, h, x, x + 1, "#0d0c0b", 0.95)
    for y in range(1, h, 4):
        line(img, y, y + 1, 0, w, "#57534a", 0.35)
    line(img, 0, h, 31, 33, "#4a463e", 0.9)
    line(img, 31, 33, 0, w, "#4a463e", 0.9)
    img = grime(img, r, 0.3, 8)
    img = speckle(img, r, 0.05, 26)
    save("floor_grate", img)


def floor_rubber():
    """2 m x 2 m: worn grey-green rubber tiles with raised coins"""
    r = rng(22)
    w = h = 64
    img = base(w, h, "#4e5650", r, 0.08)
    for y in range(2, h, 6):
        for x in range(2 + (y // 6 % 2) * 3, w, 6):
            img[y, x] = hexc("#6b746c"); img[y + 1, x] = hexc("#353b37")
    for t in (0, 32):
        line(img, t, t + 1, 0, w, "#232724", 0.9)
        line(img, 0, h, t, t + 1, "#232724", 0.9)
    img = grime(img, r, 0.45, 16)
    img = scratches(img, r, 10, "#8a948a", 0.3)
    save("floor_rubber", img)


def floor_lino():
    """2 m x 2 m: hospital linoleum, pale blue-grey checker, scuffed"""
    r = rng(23)
    w = h = 64
    img = base(w, h, "#9aa3a0", r, 0.05)
    for y in range(0, h, 16):
        for x in range(0, w, 16):
            if (x // 16 + y // 16) % 2:
                img[y:y + 16, x:x + 16] *= 0.86
    img = grime(img, r, 0.3, 16)
    img = scratches(img, r, 18, "#5c6260", 0.3)
    save("floor_lino", img)


# ---------------------------------------------------------------- materials (1 m tiles)
def simple(name, col, seed, var=0.09, g=0.3, chips=None, sc=8, edge=False):
    r = rng(seed)
    w = h = 32
    img = base(w, h, col, r, var, (8, 4, 2))
    if chips:
        n = fbm(w, h, r, (8, 4, 2))
        img = np.where((n > 0.7)[..., None], hexc(chips) * (0.8 + 0.4 * n[..., None]), img)
    if edge:
        line(img, 0, 1, 0, w, "#000000", 0.35)
        line(img, 0, h, 0, 1, "#000000", 0.35)
    img = grime(img, r, g, 4)
    img = scratches(img, r, sc)
    img = speckle(img, r, 0.05, 18)
    save(name, img)


def hazard():
    r = rng(31)
    w, h = 32, 16
    img = np.zeros((h, w, 3))
    for y in range(h):
        for x in range(w):
            img[y, x] = hexc("#c99a1c") if ((x + y) // 4) % 2 == 0 else hexc("#1b1813")
    img *= (0.85 + 0.3 * fbm(w, h, r, (8, 4, 2)))[..., None]
    img = grime(img, r, 0.4, 4)
    img = scratches(img, r, 10, "#3a3a34", 0.6)
    save("hazard", img)


def door_heavy():
    """1 m tile: oxblood heavy-door plating with horizontal ribs and bolts"""
    r = rng(32)
    w = h = 32
    img = base(w, h, "#6a2a22", r, 0.1)
    for y in range(0, h, 8):
        line(img, y, y + 1, 0, w, "#2a0f0c", 0.9)
        line(img, y + 1, y + 2, 0, w, "#9a4a3a", 0.4)
    for x in (2, 29):
        for y in range(4, h, 8):
            rivet(img, x, y, "#c08a70", "#1a0806")
    n = fbm(w, h, r, (8, 4, 2))
    img = np.where((n > 0.74)[..., None], hexc("#4a4640") * (0.8 + 0.4 * n[..., None]), img)
    img = grime(img, r, 0.35, 4, streaks=0.3)
    img = scratches(img, r, 12, "#b08070")
    save("door_heavy", img)


def console_top():
    """1 m tile: dark console deck covered with button rows, toggles and tiny lamps"""
    r = rng(33)
    w = h = 32
    img = base(w, h, "#2e2f2b", r, 0.08)
    cols = ["#b8352a", "#d8b03a", "#3f8a4a", "#d8d2c0", "#3a5a8a"]
    for y in range(2, h - 2, 6):
        for x in range(2, w - 2, 5):
            c = cols[r.integers(0, len(cols))] if r.random() < 0.7 else "#5a5a52"
            img[y:y + 2, x:x + 3] = hexc(c) * (0.7 + 0.3 * r.random())
            img[y + 2, x:x + 3] = hexc("#0b0b0a")
    line(img, 0, 1, 0, w, "#6a6a60", 0.6)
    img = grime(img, r, 0.25, 4)
    save("console_top", img)


def vent():
    r = rng(34)
    w = h = 32
    img = base(w, h, "#5a5a52", r, 0.08)
    for y in range(3, h - 3, 3):
        line(img, y, y + 1, 3, w - 3, "#0e0e0c", 1)
        line(img, y + 1, y + 2, 3, w - 3, "#8a8a7c", 0.4)
    line(img, 0, 1, 0, w, "#2a2a26", 1); line(img, h - 1, h, 0, w, "#2a2a26", 1)
    img = grime(img, r, 0.4, 4)
    save("vent", img)


def locker():
    """1 m x 2 m locker front: vents at top, number plate, dents"""
    r = rng(35)
    w, h = 32, 64
    img = base(w, h, "#55705f", r, 0.08)
    line(img, 0, h, 0, 1, "#1a221d", 1); line(img, 0, 1, 0, w, "#1a221d", 1)
    for y in range(6, 18, 3):
        line(img, y, y + 1, 8, 24, "#111511", 1)
    line(img, 24, 28, 12, 20, "#c8c4a8", 1)
    line(img, 34, 40, 26, 28, "#2a2a26", 1)
    img = grime(img, r, 0.35, 8, bottom=0.3)
    img = scratches(img, r, 14, "#a8b8a0")
    save("locker", img)


def fabric(name, col, seed):
    r = rng(seed)
    w = h = 32
    img = base(w, h, col, r, 0.12, (8, 4, 2))
    for y in range(h):
        for x in range(w):
            if (x + y) % 2 == 0:
                img[y, x] *= 0.92
    img = grime(img, r, 0.3, 8)
    save(name, img)


def pipe():
    """1 m along U: pipe with clamp bands and stencil stripes"""
    r = rng(36)
    w, h = 32, 16
    img = base(w, h, "#7a7266", r, 0.1)
    line(img, 0, h, 0, 2, "#2a2824", 1)
    line(img, 0, h, 14, 18, "#a83a22", 0.85)
    for y in range(h):
        img[y] *= 0.75 + 0.35 * np.sin(np.pi * (y + 0.5) / h)
    img = grime(img, r, 0.4, 4)
    save("pipe", img)


def crt_shell():
    simple("crt_shell", "#a59a7c", 37, 0.06, 0.32, sc=10, edge=True)


def glass_grime():
    """RGBA: dirty glass smears (used with transparency)"""
    r = rng(38)
    w = h = 32
    n = fbm(w, h, r, (8, 4, 2))
    a = np.clip((n - 0.35) * 1.4, 0.08, 0.6)
    img = np.zeros((h, w, 4))
    img[..., :3] = hexc("#9ab0a8")
    img[..., 3] = a * 255
    Image.fromarray(img.astype(np.uint8), "RGBA").save(os.path.join(OUT, "glass.png"))


# ---------------------------------------------------------------- decals (text signs, exact 0..1 UVs)
def sign(name, lines, w, h, fg, bg, border=None, size=8, stripes=False, seed=50):
    r = rng(seed)
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    if stripes:
        for x in range(-h, w, 8):
            d.polygon([(x, h), (x + 4, h), (x + 4 + h, 0), (x + h, 0)], fill="#c99a1c")
        d.rectangle([3, 3, w - 4, h - 4], fill=bg)
    if border:
        d.rectangle([1, 1, w - 2, h - 2], outline=border)
    f = font(size)
    total = len(lines) * (size + 3) - 3
    y = (h - total) // 2
    for t in lines:
        tw = d.textlength(t, font=f)
        d.text(((w - tw) // 2, y), t, font=f, fill=fg)
        y += size + 3
    a = np.array(im).astype(float)
    a = grime(a, r, 0.3, 4)
    a = speckle(a, r, 0.04, 20)
    save(name, a, 32)


def sticker_set():
    sign("sg_exit", ["EMERGENCY EXIT"], 128, 16, "#f2ead0", "#8a1a14", border="#f2ead0")
    sign("sg_lifesup", ["LIFE SUPPORT", "RING 2"], 96, 32, "#151513", "#c9a22a", border="#151513")
    sign("sg_medbay", ["MED BAY", "C-04"], 64, 32, "#e8ecea", "#2c6a74", border="#e8ecea")
    sign("sg_ctrl", ["SYSTEMS", "CONTROL"], 80, 32, "#d8e8c8", "#253a2a", border="#d8e8c8")
    sign("sg_quarters", ["CREW", "QUARTERS"], 80, 32, "#e0d6b8", "#4a3a2a", border="#e0d6b8")
    sign("sg_noentry", ["NO ENTRY"], 64, 16, "#f0e8d0", "#1a1a18", stripes=True)
    sign("sg_deck", ["DECK 03"], 64, 16, "#c8c8b8", "#1c1c1a")
    sign("sg_hand", ["PULL"], 32, 16, "#151513", "#c9a22a")
    sign("sg_o2", ["O2", "LOW"], 32, 32, "#f0e0d0", "#6a1a14", border="#f0e0d0")
    sign("sg_cap", ["UNIT 1"], 48, 16, "#2a2a28", "#d8dcd8")
    sign("sg_locker", ["07"], 16, 16, "#1a1a18", "#c8c4a8")
    # an arrow pointing to exit
    im = Image.new("RGB", (32, 16), "#163a22")
    d = ImageDraw.Draw(im)
    d.polygon([(4, 6), (16, 6), (16, 2), (27, 8), (16, 14), (16, 10), (4, 10)], fill="#b8f0b0")
    save("sg_arrow", np.array(im).astype(float), 32)
    # torn safety poster (pictogram figure + lines)
    r = rng(60)
    w, h = 32, 48
    img = base(w, h, "#d8d0b4", r, 0.06)
    line(img, 3, 9, 3, 29, "#a02a1c", 1)
    line(img, 14, 16, 13, 19, "#202020", 1); line(img, 17, 26, 14, 18, "#202020", 1)
    line(img, 26, 32, 13, 15, "#202020", 1); line(img, 26, 32, 17, 19, "#202020", 1)
    for y in range(35, 45, 3):
        line(img, y, y + 1, 4, 4 + int(r.integers(14, 24)), "#5a5a52", 1)
    img = grime(img, r, 0.45, 4, streaks=0.3)
    img[40:, 22:] = hexc("#2a2620")
    save("sg_poster", img)


if __name__ == "__main__":
    wall_panel(); wall_teal(); wall_lower(); ceiling()
    floor_grate(); floor_rubber(); floor_lino()
    simple("metal_dark", "#3c3b37", 41, 0.1, 0.35, sc=14)
    simple("metal_teal", "#466259", 42, 0.1, 0.35, chips="#6a3a20", sc=10)
    simple("metal_orange", "#a8521e", 43, 0.1, 0.35, chips="#3a3630", sc=12)
    simple("metal_bare", "#7c7a72", 44, 0.12, 0.3, sc=16)
    simple("plastic_beige", "#b0a07a", 45, 0.06, 0.3, sc=8)
    simple("plastic_white", "#c8cdc8", 46, 0.04, 0.22, sc=6)
    simple("rubber", "#1c1c1b", 47, 0.12, 0.1, sc=4)
    simple("wood_dark", "#4a3424", 48, 0.12, 0.3, sc=10)
    simple("skin", "#b08a70", 49, 0.05, 0.1, sc=0)
    simple("suit", "#5a6a74", 50, 0.08, 0.3, sc=4)
    simple("suit_orange", "#a85a2a", 51, 0.08, 0.3, sc=4)
    hazard(); door_heavy(); console_top(); vent(); locker(); pipe(); crt_shell(); glass_grime()
    fabric("fabric_blue", "#3e5466", 52); fabric("fabric_white", "#b8bcb4", 53); fabric("fabric_red", "#6a2a26", 54)
    sticker_set()
    print("textures ->", os.path.abspath(OUT), len(os.listdir(OUT)))
