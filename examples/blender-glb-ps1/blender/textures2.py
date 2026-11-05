"""Second batch: medbay tiles, flesh, faces, posters, gauges, keyboard (python blender/textures2.py)."""
import numpy as np
from PIL import Image, ImageDraw
from textures import *


def wall_med():
    r = rng(71); w = h = 64
    img = base(w, h, "#a9b5ae", r, 0.04)
    for t in range(0, 64, 16):
        line(img, t, t + 1, 0, w, "#6e7a74", 0.8); line(img, 0, h, t, t + 1, "#6e7a74", 0.8)
    line(img, 40, 44, 0, w, "#3f7f86", 0.9)
    img = grime(img, r, 0.28, 8, bottom=0.3, streaks=0.25)
    img = scratches(img, r, 10, "#e8eeea", 0.3)
    save("wall_med", img)


def flesh():
    r = rng(72); w = h = 32
    n = fbm(w, h, r, (8, 4, 2))
    img = np.zeros((h, w, 3)) + hexc("#7a1e1a")
    img *= (0.55 + 0.8 * n)[..., None]
    v = fbm(w, h, rng(73), (4, 2))
    img = np.where((np.abs(v - 0.5) < 0.04)[..., None], hexc("#3a0806"), img)
    img = speckle(img, r, 0.08, 30)
    save("flesh", img)


def face(open_eyes):
    w, h = 32, 32
    r = rng(74)
    img = base(w, h, "#b48c74", r, 0.05, (8, 4, 2))
    img[:, :] *= np.linspace(1.05, 0.85, h)[:, None, None]
    # brows
    line(img, 11, 12, 6, 13, "#2a1c16", 1); line(img, 11, 12, 19, 26, "#2a1c16", 1)
    # deep sockets
    line(img, 13, 18, 6, 13, "#7a5848", 0.7); line(img, 13, 18, 19, 26, "#7a5848", 0.7)
    if open_eyes:
        for x0 in (7, 20):
            line(img, 14, 17, x0, x0 + 5, "#e8e0d0", 1)
            line(img, 14, 17, x0 + 2, x0 + 4, "#1a120e", 1)
            img[15, x0 + 2] = hexc("#f8f8f0")
            line(img, 13, 14, x0, x0 + 5, "#1a120e", 1)
    else:
        for x0 in (7, 20):
            line(img, 16, 17, x0, x0 + 5, "#2a1a14", 1)
            line(img, 17, 18, x0 + 1, x0 + 4, "#5a3a30", 0.6)
    # nose + mouth
    line(img, 17, 22, 15, 17, "#8a6656", 0.6); line(img, 22, 23, 14, 18, "#5a3a30", 0.8)
    line(img, 26, 27, 12, 20, "#5a2e28", 0.9)
    # under-eye bags
    line(img, 19, 20, 7, 12, "#8a6050", 0.5); line(img, 19, 20, 20, 25, "#8a6050", 0.5)
    save("face_open" if open_eyes else "face_closed", img)


def hair():
    r = rng(75); w = h = 32
    img = base(w, h, "#1c1714", r, 0.2, (4, 2))
    for x in range(0, w, 2):
        line(img, 0, h, x, x + 1, "#0c0a08", 0.4)
    save("hair", img)


def poster(name, title, sub, seed, motif):
    r = rng(seed); w, h = 48, 64
    im = Image.new("RGB", (w, h), "#d6ccb0"); d = ImageDraw.Draw(im); d.fontmode = "1"
    if motif == "eye":
        d.rectangle([3, 3, 44, 40], fill="#1c2a3a")
        d.ellipse([8, 12, 39, 31], fill="#e8e0c8"); d.ellipse([18, 15, 29, 28], fill="#6a2a1c"); d.ellipse([21, 18, 26, 25], fill="#0a0a0a")
        for x in range(8, 40, 4): d.line([(x, 12), (x - 2, 7)], fill="#e8e0c8")
    elif motif == "sun":
        for y in range(3, 41):
            k = (y - 3) / 38
            d.line([(3, y), (44, y)], fill=(int(220 - 60 * k), int(120 - 70 * k), int(40 + 20 * k)))
        d.ellipse([16, 14, 31, 29], fill="#ffd870"); d.rectangle([3, 26, 44, 40], fill="#6a1a20")
        for y in range(28, 40, 3): d.line([(18, y), (29, y)], fill="#e88a3a")
    elif motif == "ship":
        d.rectangle([3, 3, 44, 40], fill="#0c0f1c")
        for i in range(30): d.point((int(r.integers(4, 44)), int(r.integers(4, 40))), fill="#c8c8d8")
        d.polygon([(8, 26), (34, 20), (40, 23), (34, 27)], fill="#9a9a8a"); d.rectangle([12, 24, 18, 28], fill="#c84a2a")
    f = font(8)
    for i, t in enumerate((title, sub)):
        if not t: continue
        tw = d.textlength(t, font=f); d.text(((w - tw) // 2, 44 + i * 10), t, font=f, fill="#2a1a14" if i == 0 else "#7a2a1c")
    a = np.array(im).astype(float)
    a = grime(a, r, 0.4, 4, streaks=0.3); a = speckle(a, r, 0.05, 20)
    save(name, a, 32)


def gauge():
    w = h = 16
    im = Image.new("RGB", (w, h), "#1a1a18"); d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 14, 14], fill="#d8d2b8")
    for k in range(7):
        a = np.pi * (0.8 + 1.4 * k / 6); x, y = 7.5 + 5.5 * np.cos(a), 7.5 + 5.5 * np.sin(a)
        d.point((round(x), round(y)), fill="#202020")
    d.line([(8, 8), (11, 4)], fill="#a02018")
    save("gauge", np.array(im).astype(float), 32)


def keyboard():
    r = rng(76); w, h = 32, 16
    img = base(w, h, "#2a2a26", r, 0.06)
    for y in range(1, h - 1, 3):
        for x in range(1 + (y // 3) % 2, w - 2, 3):
            line(img, y, y + 2, x, x + 2, "#a49a80", 1)
    save("keyboard", img)


def exit_green():
    im = Image.new("RGB", (48, 24), "#0e3a1c"); d = ImageDraw.Draw(im); d.fontmode = "1"
    d.rectangle([1, 1, 46, 22], outline="#b8f8b0")
    # running figure pictogram (original)
    d.ellipse([7, 4, 11, 8], fill="#c8ffc0"); d.line([(9, 9), (8, 14)], fill="#c8ffc0", width=2)
    d.line([(8, 14), (5, 19)], fill="#c8ffc0", width=2); d.line([(8, 14), (12, 18)], fill="#c8ffc0", width=2)
    d.line([(9, 10), (13, 12)], fill="#c8ffc0", width=2); d.line([(9, 10), (5, 11)], fill="#c8ffc0", width=2)
    d.polygon([(26, 9), (36, 9), (36, 5), (43, 12), (36, 19), (36, 15), (26, 15)], fill="#c8ffc0")
    save("sg_exit_green", np.array(im).astype(float), 32)


def tank_label():
    sign("sg_n2", ["N2"], 16, 16, "#f0f0e0", "#2a4a8a")
    sign("sg_hiP", ["HIGH", "PRESSURE"], 64, 32, "#151513", "#c9a22a", border="#151513")
    sign("sg_cam", ["CAM 4"], 32, 16, "#c8c8b8", "#1c1c1a")
    sign("sg_bunk", ["B-2"], 32, 16, "#2a2a28", "#c8c4a8")


if __name__ == "__main__":
    wall_med(); flesh(); face(True); face(False); hair(); gauge(); keyboard(); exit_green(); tank_label()
    poster("poster_awake", "STAY", "AWAKE", 80, "eye")
    poster("poster_sun", "HOME", "", 81, "sun")
    poster("poster_ship", "ONE MORE", "SHIFT", 82, "ship")
    simple("metal_red", "#7a1c16", 83, 0.1, 0.3, chips="#2a2622", sc=10)
    simple("chrome", "#9aa0a0", 84, 0.08, 0.15, sc=10)
    simple("bottle", "#4a7a5a", 85, 0.1, 0.15, sc=2)
    print("ok")
