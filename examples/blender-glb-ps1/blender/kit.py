"""Reusable ship pieces built on lib.Room (Blender Z-up, metres)."""
import math
from mathutils import Vector
from lib import mat, box_bm, tube_bm, TR

E_RED = ("EMIT_red", (0.6, 0.05, 0.03), (1.0, 0.12, 0.06))
E_GRN = ("EMIT_green", (0.1, 0.5, 0.15), (0.3, 1.0, 0.35))
E_AMB = ("EMIT_amber", (0.7, 0.45, 0.1), (1.0, 0.7, 0.2))
E_WHT = ("EMIT_tube", (0.9, 0.9, 0.85), (1.0, 0.98, 0.9))


def em(spec):
    name, c, e = spec
    mat(name, color=c, emit=e)
    return name


def wall_x(R, x, y0, y1, h, face, thick=0.12, lower=0.8, m="wall_panel", ml="wall_lower"):
    """wall in the plane x=const between y0..y1, face=+1 if its visible side looks +X"""
    cx = x - face * thick / 2
    L = y1 - y0
    R.box(ml, (thick, L, lower), (cx, (y0 + y1) / 2, lower / 2))
    R.box(m, (thick, L, h - lower), (cx, (y0 + y1) / 2, lower + (h - lower) / 2))


def wall_y(R, y, x0, x1, h, face, thick=0.12, lower=0.8, m="wall_panel", ml="wall_lower"):
    cy = y - face * thick / 2
    L = x1 - x0
    R.box(ml, (L, thick, lower), ((x0 + x1) / 2, cy, lower / 2))
    R.box(m, (L, thick, h - lower), ((x0 + x1) / 2, cy, lower + (h - lower) / 2))


def floor_ceiling(R, x0, x1, y0, y1, h, mf="floor_grate", mc="ceiling"):
    R.box(mf, (x1 - x0, y1 - y0, 0.1), ((x0 + x1) / 2, (y0 + y1) / 2, -0.05), faces="Z")
    R.box(mc, (x1 - x0, y1 - y0, 0.1), ((x0 + x1) / 2, (y0 + y1) / 2, h + 0.05), faces="z")


def rib_y(R, y, x0, x1, h, depth=0.14, w=0.22, m="metal_dark"):
    """structural frame rib across a corridor running along Y"""
    R.box(m, (depth, w, h), (x0 + depth / 2, y, h / 2))
    R.box(m, (depth, w, h), (x1 - depth / 2, y, h / 2))
    R.box(m, (x1 - x0, w, depth), ((x0 + x1) / 2, y, h - depth / 2))
    # bolt plates
    for z in (0.3, 1.2, 2.0):
        R.box("metal_bare", (0.02, 0.1, 0.1), (x0 + depth + 0.01, y, z), seg=0)
        R.box("metal_bare", (0.02, 0.1, 0.1), (x1 - depth - 0.01, y, z), seg=0)


def cage_lamp(R, name, loc, face=(0, -1, 0), color=(1.0, 0.92, 0.75), power=1.0, dist=6.0, horiz=True, emit=E_WHT):
    """caged bulkhead lamp on a wall; face = outward normal of the wall"""
    x, y, z = loc
    fx, fy, _ = face
    rot = (0, 0, math.atan2(fx, -fy))  # local -Y → face
    M = TR(loc, rot)
    bm = R.bm("metal_dark")
    box_bm(bm, 0.42, 0.06, 0.2, seg=0, M=M @ TR((0, 0.03, 0)))
    tube_m = em(emit)
    box_bm(R.bm(tube_m), 0.32, 0.06, 0.07, seg=0, M=M @ TR((0, -0.04, 0)))
    for i in range(5):
        xx = -0.16 + i * 0.08
        box_bm(R.bm("metal_bare"), 0.015, 0.11, 0.015, seg=0, M=M @ TR((xx, -0.05, 0.07)))
        box_bm(R.bm("metal_bare"), 0.015, 0.11, 0.015, seg=0, M=M @ TR((xx, -0.05, -0.07)))
    box_bm(R.bm("metal_bare"), 0.4, 0.015, 0.015, seg=0, M=M @ TR((0, -0.1, 0.07)))
    box_bm(R.bm("metal_bare"), 0.4, 0.015, 0.015, seg=0, M=M @ TR((0, -0.1, -0.07)))
    R.light(name, (x + fx * 0.35, y + fy * 0.35, z), color, power, dist)


def ceiling_lamp(R, name, loc, length=1.0, color=(1.0, 0.95, 0.85), power=1.0, dist=6.0, emit=E_WHT):
    x, y, z = loc
    R.box("metal_dark", (0.3, length + 0.1, 0.08), (x, y, z - 0.04), seg=0)
    R.box(em(emit), (0.18, length, 0.03), (x, y, z - 0.09), seg=0)
    R.light(name, (x, y, z - 0.35), color, power, dist)


def pipe_run(R, pts, r=0.06, m="pipe", clamps=True, segs=8):
    R.tube(m, [Vector(p) for p in pts], r, segs)
    if clamps:
        for a, b in zip(pts, pts[1:]):
            a, b = Vector(a), Vector(b)
            L = (b - a).length
            n = int(L / 0.9)
            for i in range(1, n + 1):
                p = a.lerp(b, i / (n + 1))
                d = (b - a).normalized()
                R.tube("metal_dark", [p - d * 0.03, p + d * 0.03], r * 1.35, 8)


def cable(R, a, b, sag=0.25, r=0.018, m="rubber", n=10):
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(n + 1):
        u = i / n
        p = a.lerp(b, u)
        p.z -= sag * 4 * u * (1 - u)
        pts.append(p)
    R.tube(m, pts, r, 5, caps=False)


def button_grid(R, origin, rot, cols, rows, pitch=0.045, size=0.03, seed=1, mats=None):
    import random
    rnd = random.Random(seed)
    mats = mats or ["EMIT_red", "EMIT_amber", "EMIT_green", "plastic_beige", "metal_dark", "plastic_white"]
    em(E_RED); em(E_AMB); em(E_GRN)
    M = TR(origin, rot)
    for i in range(cols):
        for j in range(rows):
            m = rnd.choice(mats)
            box_bm(R.bm(m), size, 0.02, size, seg=0, M=M @ TR((i * pitch, -0.01, j * pitch)))


def tech_panel(R, name, loc, rot, w=0.6, h=0.8, scr=(0.36, 0.26), seed=3):
    """wall-mounted box with a small screen, a button grid and a toggle row; faces local -Y"""
    M = TR(loc, rot)
    box_bm(R.bm("plastic_beige"), w, 0.16, h, seg=0, M=M @ TR((0, 0.08, 0)))
    box_bm(R.bm("metal_dark"), scr[0] + 0.06, 0.02, scr[1] + 0.06, seg=0, M=M @ TR((0, -0.005, h / 2 - scr[1] / 2 - 0.08)))
    # screen quad slightly in front
    sw, sh = scr
    sloc = M @ Vector((0, -0.017, h / 2 - sh / 2 - 0.08))
    R.screen(name, sw, sh, tuple(sloc), rot)
    button_grid(R, tuple(M @ Vector((-w / 2 + 0.08, 0, -h / 2 + 0.1))), rot, int((w - 0.12) / 0.045), 3, seed=seed)
    # toggles
    for i in range(5):
        p = M @ Vector((-0.18 + i * 0.09, -0.03, -h / 2 + 0.33))
        R.cyl("metal_bare", 0.008, 0.06, tuple(p), (math.pi / 2 + 0.4, 0, rot[2]), segs=4)
    R.cyl("metal_dark", 0.035, 0.03, tuple(M @ Vector((w / 2 - 0.09, -0.015, h / 2 - 0.12))), (math.pi / 2, 0, rot[2]), segs=8)


def crt(R, name, loc, rot, w=0.42, h=0.34, depth=0.38, shell="crt_shell", screen=True):
    """boxy CRT monitor; screen faces local -Y"""
    M = TR(loc, rot)
    bm = R.bm(shell)
    box_bm(bm, w, 0.08, h, seg=0, M=M @ TR((0, 0.04, 0)))  # bezel
    box_bm(bm, w * 0.75, depth - 0.08, h * 0.78, seg=0, M=M @ TR((0, 0.08 + (depth - 0.08) / 2, -h * 0.05)))  # tube housing
    box_bm(R.bm("metal_dark"), w * 0.12, 0.012, 0.02, seg=0, M=M @ TR((w * 0.32, -0.002, -h * 0.42)))
    if screen:
        p = M @ Vector((0, -0.003, h * 0.04))
        R.screen(name, w * 0.82, h * 0.72, tuple(p), rot)


def heavy_door(R, name, x, y, z0=0.0, w=1.1, h=2.0, wall_h=2.5, wall_x0=-1.2, wall_x1=1.2, face=-1, window=True, sign="sg_exit"):
    """sealed hatch in a wall at plane y. face=-1 → seen from -Y side. leaf = DYN_<name> (hinge on -x side)"""
    t = 0.12
    cy = y - face * t / 2
    # wall around the opening
    if x - w / 2 - 0.25 > wall_x0:
        R.box("wall_teal", ((x - w / 2 - 0.25) - wall_x0, t, wall_h), ((wall_x0 + x - w / 2 - 0.25) / 2, cy, wall_h / 2))
    if wall_x1 > x + w / 2 + 0.25:
        R.box("wall_teal", (wall_x1 - (x + w / 2 + 0.25), t, wall_h), ((wall_x1 + x + w / 2 + 0.25) / 2, cy, wall_h / 2))
    R.box("wall_teal", (w + 0.5, t, wall_h - h - 0.25), (x, cy, h + 0.25 + (wall_h - h - 0.25) / 2))
    # thick hazard frame (stands proud of the wall)
    fd = 0.32
    fy = y + face * 0.06
    R.box("hazard", (0.25, fd, h + 0.25), (x - w / 2 - 0.125, fy, (h + 0.25) / 2), seg=0.25)
    R.box("hazard", (0.25, fd, h + 0.25), (x + w / 2 + 0.125, fy, (h + 0.25) / 2), seg=0.25)
    R.box("hazard", (w, fd, 0.25), (x, fy, h + 0.125), seg=0.25)
    R.box("metal_dark", (w + 0.5, fd + 0.1, 0.06), (x, fy, 0.03), seg=0.25)
    # inner jamb shadows
    R.box("metal_dark", (0.04, 0.5, h), (x - w / 2 + 0.02, y, h / 2), seg=0.25)
    R.box("metal_dark", (0.04, 0.5, h), (x + w / 2 - 0.02, y, h / 2), seg=0.25)
    # hinges
    for zz in (0.35, h - 0.35):
        R.cyl("metal_bare", 0.05, 0.22, (x - w / 2 - 0.02, fy + face * 0.18, zz), segs=8)
    # leaf
    lw, lt = w - 0.02, 0.14
    wx0, wx1, wz0, wz1 = 0.3, 0.72, 1.3, 1.72  # window rect in leaf-local (x from hinge, z)

    def build(bm):
        if window:
            box_bm(bm, wx0, lt, h, seg=0.4, M=TR((wx0 / 2, 0, h / 2)))
            box_bm(bm, lw - wx1, lt, h, seg=0.4, M=TR((wx1 + (lw - wx1) / 2, 0, h / 2)))
            box_bm(bm, wx1 - wx0, lt, wz0, seg=0.4, M=TR(((wx0 + wx1) / 2, 0, wz0 / 2)))
            box_bm(bm, wx1 - wx0, lt, h - wz1, seg=0.4, M=TR(((wx0 + wx1) / 2, 0, wz1 + (h - wz1) / 2)))
        else:
            box_bm(bm, lw, lt, h, seg=0.4, M=TR((lw / 2, 0, h / 2)))

    leaf = R.dyn("DYN_" + name, "door_heavy", build, loc=(x - w / 2 + 0.01, y + face * 0.02, z0))
    # leaf details as children (local coords)
    def sub(nm, m, sx, sy, sz, loc):
        return R.dyn(nm, m, lambda bm: box_bm(bm, sx, sy, sz, seg=0), loc=loc, parent=leaf)

    side = face  # leaf front faces -Y when face=-1
    sub(f"DYN_{name}_wf", "metal_dark", wx1 - wx0 + 0.08, 0.04, 0.04, ((wx0 + wx1) / 2, side * 0.08, wz0 - 0.02))
    sub(f"DYN_{name}_wf2", "metal_dark", wx1 - wx0 + 0.08, 0.04, 0.04, ((wx0 + wx1) / 2, side * 0.08, wz1 + 0.02))
    sub(f"DYN_{name}_wf3", "metal_dark", 0.04, 0.04, wz1 - wz0, (wx0 - 0.02, side * 0.08, (wz0 + wz1) / 2))
    sub(f"DYN_{name}_wf4", "metal_dark", 0.04, 0.04, wz1 - wz0, (wx1 + 0.02, side * 0.08, (wz0 + wz1) / 2))
    sub(f"DYN_{name}_bar", "metal_bare", 0.08, 0.1, 0.5, (lw - 0.14, side * 0.1, 1.0))
    sub(f"DYN_{name}_plate", "hazard", lw - 0.1, 0.02, 0.18, (lw / 2, side * 0.08, 0.2))
    if window:
        g = mat("glass", alpha=True)
        R.quad(f"GLASS_{name}", g, wx1 - wx0, wz1 - wz0, ((wx0 + wx1) / 2, side * 0.01, (wz0 + wz1) / 2), parent=leaf)
    # sign above the frame
    if sign:
        R.decal(sign, 1.0, 0.125, (x, fy + face * (fd / 2 + 0.006), h + 0.125), (0, 0, 0 if face < 0 else math.pi))
    return leaf
