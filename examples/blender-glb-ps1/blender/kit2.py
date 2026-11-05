"""Furniture and machinery for the ship rooms (Blender Z-up, metres).
Facing rule: rot z = θ turns local -Y into (sinθ, -cosθ).  θ: 0 → faces -Y, π → +Y, π/2 → +X, -π/2 → -X.
"""
import math, random
from mathutils import Vector
from lib import mat, box_bm, tube_bm, TR
from kit import em, E_RED, E_GRN, E_AMB, E_WHT, button_grid, cable

ATLAS_COLS, ATLAS_ROWS = 16, 8


def atlas_uv(i):
    c, r = i % ATLAS_COLS, i // ATLAS_COLS
    return (c / ATLAS_COLS, 1 - (r + 1) / ATLAS_ROWS, (c + 1) / ATLAS_COLS, 1 - r / ATLAS_ROWS)


class Atlas:
    def __init__(self):
        self.i = 0

    def take(self):
        i = self.i
        self.i += 1
        return i


def P(M, x, y, z):
    return tuple(M @ Vector((x, y, z)))


def screen_atlas(R, A, w, h, M, rot, x=0, y=-0.003, z=0):
    i = A.take()
    scr = mat("EMIT_screen", color=(0.1, 0.2, 0.1), emit=(0.2, 0.5, 0.2))
    R.quad(f"SCRA_{i}", scr, w, h, P(M, x, y, z), rot, uv=atlas_uv(i))
    return i


def crt_unit(R, A, M, rot, w, h, depth=0.3, shell="crt_shell", own=None):
    """monitor in a rack: bezel + housing + screen (atlas cell or own canvas)"""
    bm = R.bm(shell)
    box_bm(bm, w, 0.06, h, seg=0, M=M @ TR((0, 0.03, 0)))
    box_bm(bm, w * 0.8, depth, h * 0.8, seg=0, M=M @ TR((0, 0.06 + depth / 2, 0)))
    box_bm(R.bm("metal_dark"), w * 0.86, 0.01, h * 0.8, seg=0, M=M @ TR((0, -0.001, 0)))
    if own:
        R.screen(own, w * 0.8, h * 0.72, P(M, 0, -0.007, 0), rot)
    else:
        screen_atlas(R, A, w * 0.8, h * 0.72, M, rot, y=-0.007)
    # small knobs / led strip under the screen
    box_bm(R.bm(em(E_GRN) if random.random() < 0.5 else em(E_AMB)), 0.015, 0.01, 0.01, seg=0, M=M @ TR((w * 0.38, -0.002, -h * 0.43)))


def monitor_wall(R, A, cx, y, z0, z1, width, rot, seed=1, rows=None, depth=0.35, own=None, gap=0.025):
    """dense wall of CRTs: rows of different heights, each filled with different widths.
    own = {(row, col): name} gives specific monitors their own canvas"""
    rnd = random.Random(seed)
    random.seed(seed)
    M0 = TR((cx, y, 0), rot)
    # rack behind
    box_bm(R.bm("metal_dark"), width + 0.1, 0.12, z1 - z0 + 0.1, seg=0.5, M=M0 @ TR((0, depth + 0.1, (z0 + z1) / 2)))
    rows = rows or [0.34, 0.28, 0.4, 0.3]
    z = z0
    out = {}
    for ri, rh in enumerate(rows):
        x = -width / 2
        ci = 0
        while x < width / 2 - 0.15:
            w = rnd.choice([0.32, 0.42, 0.5, 0.36, 0.6, 0.28])
            w = min(w, width / 2 - x)
            if w < 0.2:
                break
            h = rh - gap
            Mm = M0 @ TR((x + w / 2, rnd.uniform(0, 0.08), z + rh / 2))
            nm = (own or {}).get((ri, ci))
            shell = rnd.choice(["crt_shell", "crt_shell", "metal_dark", "plastic_beige"])
            crt_unit(R, A, Mm, rot, w - gap, h, depth=rnd.uniform(0.2, depth), shell=shell, own=nm)
            if nm:
                out[nm] = Mm
            x += w
            ci += 1
        # shelf strip between rows
        box_bm(R.bm("metal_dark"), width + 0.06, depth + 0.1, 0.03, seg=0, M=M0 @ TR((0, depth / 2 + 0.05, z - 0.015)))
        z += rh
    box_bm(R.bm("metal_dark"), width + 0.06, depth + 0.1, 0.04, seg=0, M=M0 @ TR((0, depth / 2 + 0.05, z)))
    return out


def gauge_cluster(R, M, rot, n, pitch=0.11, r=0.045):
    for i in range(n):
        p = P(M, i * pitch, 0, 0)
        R.cyl("metal_dark", r + 0.012, 0.03, P(M, i * pitch, 0.012, 0), (math.pi / 2, 0, rot[2]), segs=10)
        R.n += 1
        R.quad(f"DEC_gauge_{R.n}", "gauge", r * 2, r * 2, P(M, i * pitch, -0.005, 0), rot)


def console_desk(R, A, cx, y, width, rot, depth=0.8, h=0.78, seed=2, tilt=0.45, screens=4, own=None):
    """angled operator console; operator stands at local -Y"""
    rnd = random.Random(seed)
    M = TR((cx, y, 0), rot)
    # body
    box_bm(R.bm("metal_dark"), width, depth, h - 0.05, seg=0.4, M=M @ TR((0, 0, (h - 0.05) / 2)))
    box_bm(R.bm("wall_lower"), width - 0.04, 0.02, 0.5, seg=0.4, M=M @ TR((0, -depth / 2 - 0.005, 0.3)))
    # angled deck (front half) + rear raised flat strip
    Md = M @ TR((0, -depth / 4, h), (tilt, 0, 0))
    box_bm(R.bm("console_top"), width, depth / 2 + 0.04, 0.05, seg=0.3, M=Md)
    box_bm(R.bm("plastic_beige"), width, depth / 2, 0.24, seg=0.3, M=M @ TR((0, depth / 4, h + 0.12)))
    box_bm(R.bm("metal_dark"), width + 0.04, 0.06, 0.06, seg=0.3, M=M @ TR((0, -depth / 2 - 0.02, h - 0.12)))
    # small screens on the rear strip
    for i in range(screens):
        xx = -width / 2 + (i + 0.5) * width / screens
        Ms = M @ TR((xx, depth / 4 - 0.12, h + 0.15), (-0.25, 0, 0))
        sw = min(0.3, width / screens - 0.08)
        box_bm(R.bm("metal_dark"), sw + 0.04, 0.02, 0.18, seg=0, M=Ms @ TR((0, 0.01, 0)))
        rr = (rot[0] + (-0.25), rot[1], rot[2])
        if own and i in own:
            R.screen(own[i], sw, 0.14, P(Ms, 0, -0.002, 0), (math.pi / 2 - 0.25 - math.pi / 2, 0, rot[2]))
        else:
            ii = A.take()
            R.quad(f"SCRA_{ii}", mat("EMIT_screen"), sw, 0.14, P(Ms, 0, -0.002, 0), (-0.25, 0, rot[2]), uv=atlas_uv(ii))
    # joysticks, knobs, toggles on the deck
    for k in range(int(width / 0.35)):
        xx = -width / 2 + 0.2 + k * 0.35 + rnd.uniform(-0.05, 0.05)
        kind = rnd.random()
        p = Md @ Vector((xx, rnd.uniform(-0.1, 0.1), 0.03))
        if kind < 0.3:
            R.cyl("metal_dark", 0.04, 0.03, tuple(p), (tilt, 0, rot[2]), segs=8)
            stick = Md @ Vector((xx, 0, 0.12))
            R.tube("metal_bare", [p, stick], 0.01, 5)
            R.cyl("rubber", 0.022, 0.05, tuple(stick), (tilt, 0, rot[2]), segs=6)
        elif kind < 0.6:
            for j in range(3):
                R.cyl("plastic_white" if j % 2 else "metal_bare", 0.018, 0.025, tuple(Md @ Vector((xx - 0.06 + j * 0.06, 0, 0.035))), (tilt, 0, rot[2]), segs=6)
        else:
            m = em(E_RED) if rnd.random() < 0.5 else em(E_AMB)
            R.cyl(m, 0.03, 0.02, tuple(p), (tilt, 0, rot[2]), segs=8)
    # gauges on the raised strip front
    gauge_cluster(R, M @ TR((-width / 2 + 0.12, -0.002, h + 0.04)), rot, max(1, int(width / 0.5)), pitch=0.45, r=0.035)


def chair(R, loc, rot, name=None, m_seat="fabric_red"):
    def build(bm, M):
        box_bm(bm, 0.5, 0.48, 0.08, seg=0, M=M @ TR((0, 0, 0.48)))
        box_bm(bm, 0.48, 0.08, 0.55, seg=0, M=M @ TR((0, 0.24, 0.8), (-0.12, 0, 0)))
        box_bm(bm, 0.36, 0.1, 0.16, seg=0, M=M @ TR((0, 0.27, 1.15), (-0.12, 0, 0)))

    def build_frame(bm, M):
        box_bm(bm, 0.06, 0.06, 0.4, seg=0, M=M @ TR((0, 0, 0.24)))
        for k in range(5):
            a = k * 2 * math.pi / 5
            box_bm(bm, 0.04, 0.3, 0.04, seg=0, M=M @ TR((math.sin(a) * 0.14, math.cos(a) * 0.14, 0.04), (0, 0, -a)))
        box_bm(bm, 0.05, 0.3, 0.04, seg=0, M=M @ TR((-0.26, 0.0, 0.62)))
        box_bm(bm, 0.05, 0.3, 0.04, seg=0, M=M @ TR((0.26, 0.0, 0.62)))
        box_bm(bm, 0.03, 0.03, 0.14, seg=0, M=M @ TR((-0.26, 0.1, 0.54)))
        box_bm(bm, 0.03, 0.03, 0.14, seg=0, M=M @ TR((0.26, 0.1, 0.54)))

    if name:
        ob = R.dyn(name, m_seat, lambda bm: build(bm, TR()), loc=loc, rot=(0, 0, rot))
        R.dyn(name + "_f", "metal_dark", lambda bm: build_frame(bm, TR()), parent=ob)
        return ob
    M = TR(loc, (0, 0, rot))
    build(R.bm(m_seat), M)
    build_frame(R.bm("metal_dark"), M)


def bed(R, loc, rot, sheet="fabric_white", blanket="fabric_blue", rumpled=0.0):
    M = TR(loc, (0, 0, rot))
    L, Wd = 2.0, 0.9
    box_bm(R.bm("chrome"), Wd, L, 0.06, seg=0.5, M=M @ TR((0, 0, 0.5)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box_bm(R.bm("chrome"), 0.04, 0.04, 0.5, seg=0, M=M @ TR((sx * (Wd / 2 - 0.04), sy * (L / 2 - 0.05), 0.25)))
            R.cyl("rubber", 0.04, 0.03, P(M, sx * (Wd / 2 - 0.04), sy * (L / 2 - 0.05), 0.04), (0, math.pi / 2, rot), segs=6)
        R.tube("chrome", [M @ Vector((sx * Wd / 2, -0.4, 0.6)), M @ Vector((sx * Wd / 2, -0.4, 0.78)), M @ Vector((sx * Wd / 2, 0.5, 0.78)), M @ Vector((sx * Wd / 2, 0.5, 0.6))], 0.015, 5)
    box_bm(R.bm("chrome"), Wd, 0.04, 0.5, seg=0, M=M @ TR((0, L / 2, 0.75)))
    box_bm(R.bm(sheet), Wd - 0.06, L - 0.06, 0.14, seg=0.3, M=M @ TR((0, 0, 0.6)))
    box_bm(R.bm(sheet), 0.6, 0.35, 0.1, seg=0, M=M @ TR((0, L / 2 - 0.25, 0.71), (0.15, 0, 0)))
    box_bm(R.bm(blanket), Wd - 0.02, 1.1, 0.06, seg=0.3, M=M @ TR((0, -0.4, 0.69), (0, rumpled, 0)))
    box_bm(R.bm(blanket), 0.04, 1.1, 0.25, seg=0.3, M=M @ TR((Wd / 2 - 0.01, -0.4, 0.58)))


def iv_stand(R, loc):
    x, y, z = loc
    R.tube("chrome", [(x, y, 0.05), (x, y, 1.9)], 0.015, 5)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        R.tube("chrome", [(x, y, 0.08), (x + math.cos(a) * 0.25, y + math.sin(a) * 0.25, 0.03)], 0.012, 4)
    R.tube("chrome", [(x - 0.15, y, 1.9), (x + 0.15, y, 1.9)], 0.01, 4)
    R.cyl("bottle", 0.05, 0.2, (x + 0.12, y, 1.72), segs=6)
    cable(R, (x + 0.12, y, 1.6), (x + 0.4, y + 0.6, 0.8), sag=0.2, r=0.006, m="plastic_white", n=8)


def capsule(R, name, loc, rot=0.0):
    """med capsule along local X. returns dict of anchors (inside light, face position)"""
    M = TR(loc, (0, 0, rot))
    L, Wd = 2.3, 0.95
    # pedestal
    box_bm(R.bm("metal_dark"), L - 0.5, Wd - 0.3, 0.4, seg=0.4, M=M @ TR((0, 0, 0.2)))
    box_bm(R.bm("hazard"), L - 0.48, Wd - 0.28, 0.08, seg=0.4, M=M @ TR((0, 0, 0.04)))
    # tub
    box_bm(R.bm("plastic_white"), L, Wd, 0.12, seg=0.4, M=M @ TR((0, 0, 0.46)))
    for sy in (-1, 1):
        box_bm(R.bm("plastic_white"), L, 0.08, 0.3, seg=0.4, M=M @ TR((0, sy * (Wd / 2 - 0.04), 0.65)))
    box_bm(R.bm("plastic_white"), 0.12, Wd, 0.5, seg=0.4, M=M @ TR((L / 2 - 0.06, 0, 0.75)))
    box_bm(R.bm("plastic_white"), 0.12, Wd, 0.36, seg=0.4, M=M @ TR((-L / 2 + 0.06, 0, 0.68)))
    box_bm(R.bm("fabric_white"), L - 0.3, Wd - 0.2, 0.08, seg=0.3, M=M @ TR((0, 0, 0.55)))
    box_bm(R.bm("fabric_white"), 0.3, 0.45, 0.08, seg=0, M=M @ TR((L / 2 - 0.35, 0, 0.62), (0, -0.15, 0)))
    # glass hood: half tube along X
    seg = 10
    pts = []
    r = Wd / 2 - 0.02
    import bmesh as _b
    g = mat("glass", alpha=True)

    def hood(bm):
        rings = []
        for xi in range(5):
            xx = -L / 2 + 0.12 + xi * (L - 0.24) / 4
            ring = []
            for s in range(seg + 1):
                a = math.pi * s / seg
                ring.append(bm.verts.new((xx, math.cos(a) * r, 0.8 + math.sin(a) * r * 0.75)))
            rings.append(ring)
        lay = bm.loops.layers.uv.new("UVMap")
        for i in range(4):
            for s in range(seg):
                f = bm.faces.new((rings[i][s], rings[i + 1][s], rings[i + 1][s + 1], rings[i][s + 1]))
                for lp in f.loops:
                    lp[lay].uv = ((lp.vert.co.x + L / 2) / 0.8, lp.vert.co.z / 0.8 + lp.vert.co.y)

    ob = R.dyn("GLASS_" + name, g, hood, loc=loc, rot=(0, 0, rot))
    ob["uv_fixed"] = 1
    # hood ribs
    for xi in (0, 4):
        xx = -L / 2 + 0.12 + xi * (L - 0.24) / 4
        R.tube("metal_dark", [M @ Vector((xx, math.cos(math.pi * s / 8) * (r + 0.02), 0.8 + math.sin(math.pi * s / 8) * (r + 0.02) * 0.75)) for s in range(9)], 0.025, 6, caps=False)
    # control box + small screen at the head end
    Mc = M @ TR((L / 2 + 0.18, 0, 0.95), (0, 0, math.pi / 2))
    box_bm(R.bm("plastic_beige"), 0.6, 0.2, 0.5, seg=0, M=Mc @ TR((0, 0.1, 0)))
    R.screen(name + "_ctl", 0.34, 0.2, P(Mc, 0, -0.003, 0.08), (0, 0, rot + math.pi / 2))
    button_grid(R, P(Mc, -0.22, 0, -0.18), (0, 0, rot + math.pi / 2), 9, 2, seed=11)
    # hoses to the floor/wall
    for k in range(3):
        cable(R, P(M, -L / 2 + 0.05, -0.25 + k * 0.25, 0.7), P(M, -L / 2 - 0.6, -0.3 + k * 0.3, 0.02), sag=0.15, r=0.03, m="rubber" if k != 1 else "metal_teal", n=8)
    R.decal("sg_cap", 0.36, 0.12, P(M, 0, -Wd / 2 - 0.003, 0.6), (0, 0, rot))
    R.light(name + "_in", P(M, 0, 0, 0.95), (0.6, 0.9, 1.0), 0.5, 2.5)
    R.anchor("FACE_" + name, P(M, L / 2 - 0.4, 0, 0.72))


def locker_row(R, x0, y, n, rot, open_idx=None, w=0.5, h=1.9, d=0.5, prefix="LK"):
    M0 = TR((x0, y, 0), (0, 0, rot))
    box_bm(R.bm("metal_dark"), n * w + 0.04, d, 0.08, seg=0.5, M=M0 @ TR(((n * w) / 2 - w / 2, d / 2, h + 0.04)))
    doors = []
    for i in range(n):
        M = M0 @ TR((i * w, 0, 0))
        # carcass
        box_bm(R.bm("metal_teal"), w, d, 0.06, seg=0, M=M @ TR((0, d / 2, 0.03)))
        box_bm(R.bm("metal_teal"), 0.02, d, h, seg=0.5, M=M @ TR((-w / 2 + 0.01, d / 2, h / 2)))
        box_bm(R.bm("metal_teal"), 0.02, d, h, seg=0.5, M=M @ TR((w / 2 - 0.01, d / 2, h / 2)))
        box_bm(R.bm("metal_dark"), w, 0.02, h, seg=0.5, M=M @ TR((0, d - 0.01, h / 2)))
        box_bm(R.bm("metal_teal"), w, d, 0.02, seg=0, M=M @ TR((0, d / 2, 1.5)))
        hinge = M @ Vector((-w / 2 + 0.02, 0.0, 0))
        nm = f"DYN_{prefix}{i}"

        def door(bm):
            box_bm(bm, w - 0.03, 0.025, h - 0.06, seg=0.5, M=TR(((w - 0.03) / 2, 0, (h - 0.06) / 2 + 0.03)))

        ob = R.dyn(nm, "locker", door, loc=tuple(hinge), rot=(0, 0, rot))
        ob.data.materials.clear()
        ob.data.materials.append(mat("locker"))
        ob["uv_local"] = 1
        doors.append(ob)
        R.quad(f"DEC_lk_{prefix}{i}", "sg_locker", 0.08, 0.08, (w / 2 - 0.015, -0.015, 1.25), (0, 0, 0), parent=ob)
    return doors


def tank(R, loc, r=0.45, h=2.0, m="metal_teal", label=None, rot=0.0):
    x, y, z = loc
    R.cyl(m, r, h, (x, y, z + h / 2), segs=12)
    R.cyl("metal_dark", r * 0.7, 0.15, (x, y, z + h + 0.07), segs=12, r2=r * 0.3)
    for zz in (0.25, h - 0.3):
        R.cyl("metal_dark", r + 0.025, 0.08, (x, y, z + zz), segs=12)
    R.cyl("metal_bare", 0.06, 0.4, (x, y, z + h + 0.3), segs=6)
    if label:
        ang = rot
        R.decal(label, 0.4, 0.2, (x + math.sin(ang) * (r + 0.01), y - math.cos(ang) * (r + 0.01), z + h * 0.6), (0, 0, ang))


def railing(R, pts, h=1.0, m="metal_orange"):
    pts = [Vector(p) for p in pts]
    R.tube(m, [p + Vector((0, 0, h)) for p in pts], 0.025, 6, caps=False)
    R.tube(m, [p + Vector((0, 0, h * 0.5)) for p in pts], 0.018, 6, caps=False)
    for a, b in zip(pts, pts[1:]):
        L = (b - a).length
        n = max(1, round(L / 1.0))
        for i in range(n + 1):
            p = a.lerp(b, i / n)
            R.tube(m, [p, p + Vector((0, 0, h))], 0.025, 6)


def shelf(R, loc, rot, w=1.0, levels=(0.9, 1.3, 1.7), seed=5, items=True):
    rnd = random.Random(seed)
    M = TR(loc, (0, 0, rot))
    for z in levels:
        box_bm(R.bm("metal_bare"), w, 0.3, 0.03, seg=0, M=M @ TR((0, 0.15, z)))
        box_bm(R.bm("metal_dark"), 0.03, 0.3, 0.12, seg=0, M=M @ TR((-w / 2 + 0.05, 0.15, z - 0.07)))
        box_bm(R.bm("metal_dark"), 0.03, 0.3, 0.12, seg=0, M=M @ TR((w / 2 - 0.05, 0.15, z - 0.07)))
        if not items:
            continue
        x = -w / 2 + 0.08
        while x < w / 2 - 0.1:
            k = rnd.random()
            if k < 0.45:
                rr = rnd.uniform(0.03, 0.05); hh = rnd.uniform(0.1, 0.22)
                R.cyl(rnd.choice(["bottle", "plastic_white", "metal_red", "plastic_beige"]), rr, hh, P(M, x + rr, 0.12, z + hh / 2 + 0.015), segs=6)
                x += rr * 2 + 0.03
            elif k < 0.8:
                bw = rnd.uniform(0.1, 0.22); bh = rnd.uniform(0.08, 0.2)
                box_bm(R.bm(rnd.choice(["plastic_beige", "metal_teal", "fabric_red", "plastic_white", "metal_orange"])), bw, 0.2, bh, seg=0, M=M @ TR((x + bw / 2, 0.14, z + bh / 2 + 0.015), (0, 0, rnd.uniform(-0.15, 0.15))))
                x += bw + 0.03
            else:
                x += 0.12


def pendant_lamp(R, name, loc, color=(1.0, 0.3, 0.2), power=1.0, dist=5.0, shade="metal_red"):
    x, y, z = loc
    R.tube("rubber", [(x, y, z + 0.6), (x, y, z + 0.1)], 0.008, 4)
    R.cyl(shade, 0.08, 0.12, (x, y, z + 0.06), segs=10, r2=0.04)
    R.cyl(shade, 0.32, 0.12, (x, y, z - 0.04), segs=12, r2=0.1, caps=False)
    R.cyl(shade, 0.36, 0.03, (x, y, z - 0.11), segs=12, r2=0.32, caps=False)
    R.cyl(em(("EMIT_bulb", (0.9, 0.6, 0.4), (1.0, 0.75, 0.5))), 0.06, 0.06, (x, y, z - 0.08), segs=6)
    R.light(name, (x, y, z - 0.35), color, power, dist)


def porthole(R, loc, rot, r=0.28):
    M = TR(loc, (0, 0, rot))
    pts = [M @ Vector((math.cos(a) * r, 0, math.sin(a) * r)) for a in [2 * math.pi * k / 12 for k in range(13)]]
    R.tube("metal_bare", pts, 0.05, 6, caps=False)
    for k in range(8):
        a = 2 * math.pi * k / 8
        R.cyl("metal_dark", 0.02, 0.03, P(M, math.cos(a) * (r + 0.07), -0.02, math.sin(a) * (r + 0.07)), (math.pi / 2, 0, rot), segs=6)
    R.quad("SCR_stars", mat("EMIT_screen"), r * 1.9, r * 1.9, P(M, 0, 0.02, 0), (0, 0, rot))


def table(R, loc, rot, w=1.2, d=0.7, m="wood_dark"):
    M = TR(loc, (0, 0, rot))
    box_bm(R.bm(m), w, d, 0.05, seg=0.4, M=M @ TR((0, 0, 0.74)))
    box_bm(R.bm("metal_dark"), 0.12, 0.12, 0.7, seg=0, M=M @ TR((0, 0, 0.36)))
    box_bm(R.bm("metal_dark"), 0.6, 0.5, 0.03, seg=0, M=M @ TR((0, 0, 0.015)))


def bunk(R, loc, rot):
    M = TR(loc, (0, 0, rot))
    for z in (0.35, 1.35):
        box_bm(R.bm("metal_teal"), 0.9, 2.0, 0.08, seg=0.5, M=M @ TR((0, 0, z)))
        box_bm(R.bm("fabric_blue"), 0.84, 1.9, 0.12, seg=0.4, M=M @ TR((0, 0, z + 0.1)))
        box_bm(R.bm("fabric_white"), 0.5, 0.3, 0.08, seg=0, M=M @ TR((0, 0.75, z + 0.2)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box_bm(R.bm("metal_teal"), 0.05, 0.05, 1.9, seg=0.5, M=M @ TR((sx * 0.43, sy * 0.98, 0.95)))
    for k in range(5):
        box_bm(R.bm("metal_bare"), 0.3, 0.03, 0.03, seg=0, M=M @ TR((0.0, -1.0, 0.5 + k * 0.25)))


def junction_box(R, loc, rot, w=0.4, h=0.5, seed=7):
    M = TR(loc, (0, 0, rot))
    box_bm(R.bm("metal_teal"), w, 0.14, h, seg=0, M=M @ TR((0, 0.07, 0)))
    box_bm(R.bm("metal_dark"), w - 0.06, 0.01, h - 0.06, seg=0, M=M @ TR((0, -0.002, 0)))
    box_bm(R.bm(em(E_AMB)), 0.03, 0.01, 0.03, seg=0, M=M @ TR((w / 2 - 0.06, -0.008, h / 2 - 0.06)))
    for k in range(3):
        R.tube("rubber", [M @ Vector((-w / 4 + k * w / 4, 0.07, -h / 2)), M @ Vector((-w / 4 + k * w / 4, 0.07, -h / 2 - 0.4 - k * 0.2))], 0.015, 5)


def extinguisher(R, loc, rot):
    x, y, z = loc
    R.cyl("metal_red", 0.07, 0.45, (x, y, z + 0.25), segs=8)
    R.cyl("metal_dark", 0.03, 0.08, (x, y, z + 0.5), segs=6)
    R.box("metal_dark", (0.2, 0.04, 0.1), (x, y + 0.08 * math.cos(rot), z + 0.4), rot=(0, 0, rot), seg=0)


def sec_camera(R, loc, rot, tilt=0.4):
    M = TR(loc, (tilt, 0, rot))
    box_bm(R.bm("plastic_beige"), 0.12, 0.26, 0.11, seg=0, M=M)
    R.cyl("metal_dark", 0.04, 0.06, P(M, 0, -0.15, 0), (math.pi / 2 + tilt, 0, rot), segs=8)
    box_bm(R.bm(em(E_RED)), 0.015, 0.015, 0.015, seg=0, M=M @ TR((0.04, -0.13, 0.04)))
    box_bm(R.bm("metal_dark"), 0.04, 0.04, 0.2, seg=0, M=M @ TR((0, 0.1, 0.12)))


def doorway(R, x, y, w, h, rot, depth=1.2, void=True):
    """open doorway frame with a dark stub corridor behind (local +Y = through the door)"""
    M = TR((x, y, 0), (0, 0, rot))
    for sx in (-1, 1):
        box_bm(R.bm("metal_dark"), 0.18, 0.3, h + 0.1, seg=0.5, M=M @ TR((sx * (w / 2 + 0.09), 0, (h + 0.1) / 2)))
    box_bm(R.bm("metal_dark"), w + 0.36, 0.3, 0.18, seg=0.5, M=M @ TR((0, 0, h + 0.09)))
    box_bm(R.bm("hazard"), w, 0.3, 0.04, seg=0.5, M=M @ TR((0, 0, 0.02)))
    if void:
        box_bm(R.bm("wall_lower"), w, depth, 0.05, seg=0.5, M=M @ TR((0, depth / 2 + 0.15, -0.02)), faces="Z")
        box_bm(R.bm("metal_dark"), 0.05, depth, h, seg=0.5, M=M @ TR((-w / 2 - 0.02, depth / 2 + 0.15, h / 2)), faces="X")
        box_bm(R.bm("metal_dark"), 0.05, depth, h, seg=0.5, M=M @ TR((w / 2 + 0.02, depth / 2 + 0.15, h / 2)), faces="x")
        box_bm(R.bm("metal_dark"), w, depth, 0.05, seg=0.5, M=M @ TR((0, depth / 2 + 0.15, h)), faces="z")
        box_bm(R.bm("metal_dark"), w, 0.05, h, seg=0.5, M=M @ TR((0, depth + 0.15, h / 2)), faces="y")


def wall_seg(R, axis, c, a0, a1, h, face, gaps=(), m="wall_panel", ml="wall_lower", lower=0.8, thick=0.12):
    """wall plane x=c (axis='x', running along Y from a0..a1) or y=c (axis='y', along X).
    gaps = [(center, width, height)]; face = +1/-1 visible side normal sign along the plane normal."""
    cuts = sorted(gaps)
    spans = []
    s = a0
    for (gc, gw, gh) in cuts:
        spans.append((s, gc - gw / 2, None))
        spans.append((gc - gw / 2, gc + gw / 2, gh))
        s = gc + gw / 2
    spans.append((s, a1, None))
    cc = c - face * thick / 2
    for (u0, u1, gh) in spans:
        L = u1 - u0
        if L <= 1e-4:
            continue
        mid = (u0 + u1) / 2
        if gh is None:
            parts = [(0, lower, ml), (lower, h, m)]
        else:
            parts = [(gh, h, m)]
        for z0, z1, mm in parts:
            if z1 - z0 <= 1e-4:
                continue
            if axis == "x":
                R.box(mm, (thick, L, z1 - z0), (cc, mid, (z0 + z1) / 2))
            else:
                R.box(mm, (L, thick, z1 - z0), (mid, cc, (z0 + z1) / 2))
