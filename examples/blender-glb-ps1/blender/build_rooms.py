"""Builds one ship room per Blender run:  blender -b --factory-startup --python build_rooms.py -- <med|corr|ctrl|ring|quarters|crew>
Each room is centred on its own origin, AO-baked into vertex colours, saved as blender/<room>.blend
and exported to assets/models/<room>.glb.
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import lib, kit, kit2
from lib import Room, mat, box_bm, tube_bm, TR
from kit import *
from kit2 import *

PI = math.pi
H_PI = PI / 2


# =====================================================================  MED BAY (scenes A, G, H)
def med():
    R = Room("med"); A = Atlas()
    X0, X1, Y0, Y1, H = -3.5, 3.5, -3.0, 3.0, 2.5
    floor_ceiling(R, X0, X1, Y0, Y1, H, mf="floor_lino")
    wall_seg(R, "y", Y0, X0, X1, H, +1, gaps=[(0, 1.1, 2.05)], m="wall_med")
    wall_seg(R, "y", Y1, X0, X1, H, -1, m="wall_med")
    wall_seg(R, "x", X0, Y0, Y1, H, +1, m="wall_med")
    wall_seg(R, "x", X1, Y0, Y1, H, -1, m="wall_med")
    doorway(R, 0, Y0, 1.1, 2.05, PI, depth=2.0)
    R.decal("sg_exit_green", 0.48, 0.24, (0, Y0 + 0.01, 2.27), (0, 0, PI))
    R.light("exitsign", (0, Y0 + 0.4, 2.2), (0.3, 1.0, 0.4), 0.35, 2.5)
    # ceiling beams + lamps
    for y in (-1.5, 0.0, 1.5):
        R.box("metal_dark", (X1 - X0, 0.18, 0.14), (0, y, H - 0.07))
    ceiling_lamp(R, "m1", (-1.6, -0.75, H - 0.14), 1.2, (0.85, 0.95, 1.0), 1.0)
    ceiling_lamp(R, "m2", (1.6, -0.75, H - 0.14), 1.2, (0.85, 0.95, 1.0), 1.0)
    ceiling_lamp(R, "m3", (0.3, 0.75, H - 0.14), 1.2, (0.85, 0.95, 1.0), 1.0)
    cage_lamp(R, "red1", (X0 + 0.12, 2.6, 2.1), (1, 0, 0), (1, 0.12, 0.08), 1.0, 7, emit=E_RED)
    cage_lamp(R, "red2", (X1 - 0.12, -2.6, 2.1), (-1, 0, 0), (1, 0.12, 0.08), 1.0, 7, emit=E_RED)
    cage_lamp(R, "red3", (2.0, Y1 - 0.12, 2.15), (0, -1, 0), (1, 0.12, 0.08), 1.0, 7, emit=E_RED)
    # ---- diagnostic terminal on the east wall (scene A)
    tx, ty = X1 - 0.45, -0.6
    M = TR((tx, ty, 0), (0, 0, -H_PI))  # faces -X
    box_bm(R.bm("plastic_beige"), 1.6, 0.8, 0.06, seg=0.4, M=M @ TR((0, 0, 0.82)))
    box_bm(R.bm("metal_dark"), 1.5, 0.7, 0.8, seg=0.4, M=M @ TR((0, 0.05, 0.4)))
    box_bm(R.bm("wall_lower"), 1.4, 0.02, 0.6, seg=0.4, M=M @ TR((0, -0.31, 0.38)))
    # big CRT
    Mc = M @ TR((0, 0.05, 1.22), (-0.08, 0, 0))
    box_bm(R.bm("crt_shell"), 0.78, 0.1, 0.62, seg=0, M=Mc @ TR((0, 0.05, 0)))
    box_bm(R.bm("crt_shell"), 0.6, 0.5, 0.5, seg=0, M=Mc @ TR((0, 0.33, -0.02)))
    box_bm(R.bm("metal_dark"), 0.68, 0.01, 0.52, seg=0, M=Mc @ TR((0, -0.001, 0.02)))
    R.screen("diag", 0.62, 0.46, P(Mc, 0, -0.008, 0.02), (-0.08, 0, -H_PI))
    box_bm(R.bm("crt_shell"), 0.3, 0.3, 0.14, seg=0, M=M @ TR((0, 0.2, 0.92)))
    for k in range(4):
        box_bm(R.bm(em(E_GRN) if k % 2 else em(E_AMB)), 0.02, 0.01, 0.02, seg=0, M=Mc @ TR((0.22 + k * 0.035, -0.002, -0.27)))
    # keyboard
    Mk = M @ TR((0, -0.22, 0.87), (0.1, 0, 0))
    box_bm(R.bm("keyboard"), 0.5, 0.18, 0.03, seg=0, M=Mk)
    # side modules: ECG + small screens
    for sx, w, h, z in ((-0.62, 0.3, 0.24, 1.1), (0.62, 0.3, 0.24, 1.08), (0.62, 0.26, 0.2, 1.4), (-0.6, 0.26, 0.2, 1.42)):
        crt_unit(R, A, M @ TR((sx, 0.1, z)), (0, 0, -H_PI), w, h, depth=0.25)
    gauge_cluster(R, M @ TR((-0.7, -0.25, 0.92), (0.0, 0, 0)), (0, 0, -H_PI), 3, pitch=0.12, r=0.035)
    for k in range(6):
        cable(R, P(M, -0.5 + k * 0.18, 0.4, 1.0), P(M, -0.6 + k * 0.22, 0.38, 0.05), sag=0.1 + 0.05 * k, r=0.012)
    R.light("term", P(M, 0, -0.7, 1.25), (0.35, 1.0, 0.45), 0.9, 4.5)
    # wall cabinet above the terminal
    box_bm(R.bm("plastic_white"), 1.4, 0.35, 0.55, seg=0, M=M @ TR((0, 0.17, 2.05)))
    box_bm(R.bm("metal_dark"), 0.01, 0.02, 0.5, seg=0, M=M @ TR((0, -0.02, 2.05)))
    # ---- capsule (scenes G, H)
    capsule(R, "cap", (0.2, 1.7, 0.0), 0.0)
    # surgical lamp
    R.tube("chrome", [(0.2, 1.7, H), (0.2, 1.7, 2.15), (0.6, 1.5, 1.95)], 0.025, 6)
    R.cyl("plastic_white", 0.28, 0.12, (0.6, 1.5, 1.9), segs=12, r2=0.18)
    R.cyl(em(E_WHT), 0.22, 0.02, (0.6, 1.5, 1.83), segs=12)
    # vitals monitor on a pole (faces south-west)
    vx, vy = 1.95, 0.75
    R.tube("chrome", [(vx, vy, 0.05), (vx, vy, 1.35)], 0.025, 6)
    for k in range(5):
        a = k * 2 * PI / 5
        R.tube("chrome", [(vx, vy, 0.08), (vx + math.cos(a) * 0.3, vy + math.sin(a) * 0.3, 0.03)], 0.018, 4)
    Mv = TR((vx, vy, 1.5), (0, 0, -0.5))
    box_bm(R.bm("plastic_white"), 0.46, 0.12, 0.36, seg=0, M=Mv @ TR((0, 0.06, 0)))
    box_bm(R.bm("metal_dark"), 0.42, 0.01, 0.3, seg=0, M=Mv @ TR((0, -0.001, 0.0)))
    R.screen("vitals", 0.4, 0.28, P(Mv, 0, -0.008, 0.0), (0, 0, -0.5))
    cable(R, (vx - 0.1, vy, 1.35), (1.1, 1.7, 0.9), sag=0.3, r=0.01, m="plastic_white")
    # security monitor on the north wall above the capsule (feed of this room)
    Ms = TR((-0.9, Y1 - 0.3, 1.75), (0.12, 0, 0))
    box_bm(R.bm("crt_shell"), 0.66, 0.08, 0.52, seg=0, M=Ms @ TR((0, 0.04, 0)))
    box_bm(R.bm("crt_shell"), 0.5, 0.36, 0.42, seg=0, M=Ms @ TR((0, 0.25, -0.02)))
    box_bm(R.bm("metal_dark"), 0.6, 0.01, 0.45, seg=0, M=Ms @ TR((0, -0.001, 0.0)))
    R.screen("secmed", 0.54, 0.4, P(Ms, 0, -0.008, 0.0), (0.12, 0, 0))
    R.box("metal_dark", (0.06, 0.32, 0.06), (-0.9, Y1 - 0.15, 2.05))
    R.decal("sg_cam", 0.2, 0.1, P(Ms, 0, -0.045, -0.31), (0.12, 0, 0))
    sec_camera(R, (X1 - 0.3, -Y1 + 0.35, H - 0.25), PI * 0.75, tilt=-0.5)
    R.anchor("CAM_secmed", (X1 - 0.45, -Y1 + 0.5, H - 0.35))
    # ---- beds with curtains (west)
    for i, by in enumerate((-1.7, 0.5)):
        bed(R, (X0 + 1.05, by, 0), H_PI, rumpled=0.08 * i)
        iv_stand(R, (X0 + 0.45, by + 0.75, 0))
        # curtain rail + curtains
        R.tube("chrome", [(X0, by - 1.05, H - 0.15), (X0 + 2.2, by - 1.05, H - 0.15), (X0 + 2.2, by + 1.05, H - 0.15), (X0, by + 1.05, H - 0.15)], 0.015, 5, caps=False)
        for k in range(6):
            fold = 0.06 * (1 if k % 2 else -1)
            R.box("fabric_white", (0.02, 0.22, 1.9), (X0 + 2.2 + fold, by + 1.05 - 0.12 - k * 0.2, H - 1.13))
    # cabinet + shelves on the west wall (north part)
    shelf(R, (X0 + 0.02, 2.2, 0), -H_PI, w=1.2, levels=(1.0, 1.4, 1.8), seed=21)
    R.box("plastic_white", (0.5, 1.2, 0.85), (X0 + 0.25, 2.2, 0.425))
    for k in range(3):
        R.box("metal_dark", (0.02, 0.3, 0.02), (X0 + 0.51, 1.8 + k * 0.4, 0.7))
    # posters + labels
    R.decal("poster_awake", 0.48, 0.64, (X0 + 0.01, -0.55, 1.55), (0, 0, H_PI))
    R.decal("sg_medbay", 0.64, 0.32, (X1 - 0.01, 1.8, 1.9), (0, 0, -H_PI))
    R.decal("sg_o2", 0.24, 0.24, (2.8, Y1 - 0.01, 1.4), (0, 0, 0))
    # pipes along the ceiling edges
    pipe_run(R, [(X0 + 0.15, Y0, H - 0.15), (X0 + 0.15, Y1, H - 0.15)], r=0.06)
    pipe_run(R, [(X1 - 0.15, Y0, H - 0.18), (X1 - 0.15, Y1, H - 0.18)], r=0.05, m="metal_teal")
    pipe_run(R, [(X0, Y1 - 0.15, H - 0.3), (X1, Y1 - 0.15, H - 0.3)], r=0.05, m="metal_orange")
    junction_box(R, (X1 - 0.08, 1.0, 1.55), -H_PI)
    junction_box(R, (-2.4, Y1 - 0.08, 1.6), 0, w=0.5, h=0.4)
    # more clutter around the terminal corner and the doorway (scene A pull-back)
    R.box("plastic_white", (0.6, 0.55, 1.7), (X1 - 0.3, -2.45, 0.85))
    R.box("metal_dark", (0.02, 0.5, 1.6), (X1 - 0.605, -2.45, 0.85))
    R.box("metal_dark", (0.02, 0.04, 0.3), (X1 - 0.62, -2.25, 1.0))
    R.decal("sg_o2", 0.2, 0.2, (X1 - 0.612, -2.45, 1.45), (0, 0, -H_PI))
    shelf(R, (1.6, Y0 + 0.02, 0), 0, w=1.4, levels=(1.2, 1.6, 2.0), seed=27)
    R.box("plastic_beige", (1.4, 0.5, 0.9), (1.6, Y0 + 0.27, 0.45))
    button_grid(R, (1.05, Y0 + 0.52, 0.75), (0, 0, PI), 6, 2, seed=8)
    R.decal("poster_ship", 0.48, 0.64, (-1.6, Y0 + 0.01, 1.5), (0, 0, PI))
    for k in range(4):
        cable(R, (0.75 + k * 0.08, Y0 + 0.05, 2.3), (2.4 - k * 0.1, Y0 + 0.05, 2.25), sag=0.3 + 0.06 * k, r=0.014)
    junction_box(R, (-0.95, Y0 + 0.08, 1.4), PI)
    # floor drain + cables across the floor
    R.cyl("metal_dark", 0.15, 0.02, (-0.6, 0.0, 0.005), segs=10)
    for k in range(3):
        cable(R, (X1 - 0.6, -0.2 + k * 0.1, 0.02), (1.1, 1.3 + k * 0.1, 0.02), sag=-0.0, r=0.02)
    R.anchor("CAM_term", (X1 - 1.6, ty, 1.62))
    R.light("fill", (0, 0, 1.6), (0.5, 0.55, 0.6), 0.25, 6)
    return R


# =====================================================================  CORRIDOR (scene B)
def corr():
    R = Room("corr"); A = Atlas()
    H = 2.5
    floor_ceiling(R, -1.3, 1.3, -1.0, 7.0, H)
    wall_x(R, -1.3, -1.0, 7.0, H, +1)
    wall_seg(R, "x", 1.3, -1.0, 7.0, H, -1, gaps=[(2.6, 1.6, 2.2)])
    wall_y(R, -1.0, -1.3, 1.3, H, +1, m="wall_teal")
    heavy_door(R, "exit", 0, 7.0, wall_h=H, wall_x0=-1.3, wall_x1=1.3)
    for y in (0.6, 1.8, 3.4, 5.0, 6.2):
        rib_y(R, y, -1.3, 1.3, H)
    cage_lamp(R, "c1", (-1.18, 1.2, 2.05), (1, 0, 0), (1.0, 0.8, 0.55), 1.0, 6)
    cage_lamp(R, "c2", (-1.18, 4.2, 2.05), (1, 0, 0), (1.0, 0.8, 0.55), 0.8, 6)
    cage_lamp(R, "alarm", (0.0, 6.88, 2.42), (0, -1, 0), (1.0, 0.12, 0.08), 1.2, 6, emit=E_RED)
    # alcove on the east side with a compressor block
    R.box("floor_grate", (1.0, 1.6, 0.1), (1.8, 2.6, -0.05), faces="Z")
    R.box("ceiling", (1.0, 1.6, 0.1), (1.8, 2.6, 2.25), faces="z")
    R.box("wall_teal", (0.12, 1.6, 2.2), (2.36, 2.6, 1.1))
    R.box("wall_teal", (1.0, 0.12, 2.2), (1.8, 1.74, 1.1))
    R.box("wall_teal", (1.0, 0.12, 2.2), (1.8, 3.46, 1.1))
    R.box("metal_orange", (0.8, 1.2, 1.0), (1.85, 2.6, 0.5))
    R.box("metal_dark", (0.6, 1.0, 0.25), (1.85, 2.6, 1.12))
    R.cyl("metal_dark", 0.32, 0.12, (1.85, 2.6, 1.32), segs=10)
    R.box("vent", (0.02, 0.8, 0.5), (1.44, 2.6, 0.5))
    for k in range(4):
        R.tube("pipe", [(2.2, 2.2 + k * 0.25, 1.0), (2.2, 2.2 + k * 0.25, 2.25)], 0.04, 6)
    R.decal("sg_hiP", 0.4, 0.2, (1.44, 2.6, 0.85), (0, 0, -H_PI))
    # pipes / cable trays
    pipe_run(R, [(1.05, -1.0, 2.3), (1.05, 7.0, 2.3)], r=0.07)
    pipe_run(R, [(0.86, -1.0, 2.36), (0.86, 7.0, 2.36)], r=0.05, m="metal_orange")
    pipe_run(R, [(-1.0, -1.0, 2.34), (-1.0, 6.4, 2.34), (-1.0, 6.4, 0.4), (-1.0, 6.9, 0.4)], r=0.05, m="metal_teal")
    R.box("metal_bare", (0.4, 7.8, 0.03), (-0.55, 3.0, 2.4), seg=0.8)
    for i in range(6):
        cable(R, (-0.7 + i * 0.06, -1.0, 2.37), (-0.7 + i * 0.06, 7.0, 2.37), sag=0.0, r=0.015)
    for i in range(3):
        cable(R, (-1.15, 0.8 + i * 0.1, 2.2), (-1.15, 3.2 + i * 0.12, 2.2), sag=0.35 + 0.1 * i)
    # wall junk
    tech_panel(R, "keypad", (1.12, 6.2, 1.3), (0, 0, -H_PI), w=0.36, h=0.5, scr=(0.26, 0.18), seed=4)
    junction_box(R, (-1.22, 2.5, 1.5), H_PI)
    junction_box(R, (-1.22, 5.6, 1.35), H_PI, w=0.3, h=0.6)
    extinguisher(R, (1.18, 4.2, 0.1), -H_PI)
    for k in range(3):
        R.box("vent", (0.5, 0.5, 0.02), (0, 0.6 + k * 2.4, H - 0.01), faces="z")
    R.decal("sg_arrow", 0.32, 0.16, (-1.29, 3.9, 1.5), (0, 0, H_PI))
    R.decal("sg_deck", 0.48, 0.12, (1.29, 0.2, 1.7), (0, 0, -H_PI))
    R.decal("sg_poster", 0.32, 0.48, (-1.29, 0.0, 1.4), (0, 0, H_PI))
    R.decal("sg_noentry", 0.48, 0.12, (-1.29, 6.6, 1.0), (0, 0, H_PI))
    # floor hatch
    R.box("hazard", (0.8, 0.8, 0.02), (0, 4.2, 0.005), faces="Z", seg=0.4)
    R.box("metal_dark", (0.6, 0.6, 0.03), (0, 4.2, 0.012), faces="Z", seg=0)
    # compartment behind the hatch
    floor_ceiling(R, -2.2, 2.2, 7.0, 11.0, H)
    wall_y(R, 11.0, -2.2, 2.2, H, -1, m="wall_teal")
    wall_x(R, -2.2, 7.0, 11.0, H, +1, m="wall_teal")
    wall_x(R, 2.2, 7.0, 11.0, H, -1, m="wall_teal")
    R.box("metal_orange", (0.8, 0.6, 0.9), (1.4, 10.4, 0.45))
    R.box("metal_dark", (0.6, 0.6, 0.6), (1.4, 10.4, 1.2), rot=(0, 0, 0.3))
    tank(R, (-1.5, 10.2, 0), 0.4, 1.9, label="sg_n2")
    pipe_run(R, [(-2.0, 7.2, 2.2), (-2.0, 11, 2.2)], r=0.06)
    ceiling_lamp(R, "far", (0.3, 9.0, H), 1.0, (0.8, 0.9, 1.0), 0.7)
    R.anchor("FIG_spot", (-0.3, 9.6, 0))
    return R


# =====================================================================  CONTROL ROOM (scene C)
def ctrl():
    R = Room("ctrl"); A = Atlas()
    X0, X1, Y0, Y1, H = -2.7, 2.7, -2.2, 2.3, 2.7
    floor_ceiling(R, X0, X1, Y0, Y1, H, mf="floor_rubber")
    wall_seg(R, "y", Y0, X0, X1, H, +1, gaps=[(0.0, 1.1, 2.05)], m="wall_teal")
    wall_seg(R, "y", Y1, X0, X1, H, -1, m="wall_teal")
    wall_seg(R, "x", X0, Y0, Y1, H, +1, m="wall_teal")
    wall_seg(R, "x", X1, Y0, Y1, H, -1, m="wall_teal")
    doorway(R, 0.0, Y0, 1.1, 2.05, PI, depth=1.5)
    # --- north: monitor wall + big main screen
    yw = Y1 - 0.5
    monitor_wall(R, A, -1.65, yw, 0.95, 2.6, 1.9, (0, 0, 0), seed=31, rows=[0.36, 0.3, 0.42, 0.32, 0.25])
    monitor_wall(R, A, 1.65, yw, 0.95, 2.6, 1.9, (0, 0, 0), seed=32, rows=[0.3, 0.42, 0.36, 0.32, 0.25])
    Mm = TR((0, yw - 0.02, 1.55))
    box_bm(R.bm("metal_dark"), 1.36, 0.5, 1.2, seg=0, M=Mm @ TR((0, 0.3, 0.1)))
    box_bm(R.bm("crt_shell"), 1.3, 0.08, 0.92, seg=0, M=Mm @ TR((0, 0.03, 0)))
    box_bm(R.bm("metal_dark"), 1.18, 0.01, 0.8, seg=0, M=Mm @ TR((0, -0.012, 0)))
    R.screen("main", 1.1, 0.72, P(Mm, 0, -0.02, 0), (0, 0, 0))
    for k in range(3):
        crt_unit(R, A, TR((-0.42 + k * 0.42, yw, 2.38)), (0, 0, 0), 0.4, 0.3, depth=0.25)
    console_desk(R, A, 0, yw - 0.95, 4.6, (0, 0, 0), depth=0.8, seed=33, screens=6)
    # --- west wall: more monitors + gauge board
    monitor_wall(R, A, X0 + 0.45, -0.1, 1.0, 2.5, 2.4, (0, 0, H_PI), seed=34, rows=[0.4, 0.36, 0.42, 0.3])
    console_desk(R, A, X0 + 0.95, -0.1, 2.2, (0, 0, H_PI), depth=0.7, seed=35, screens=3, tilt=0.5)
    # --- east wall: surveillance CRT at eye level + panels
    own = monitor_wall(R, A, X1 - 0.45, 0.0, 1.0, 2.5, 2.6, (0, 0, -H_PI), seed=36, rows=[0.32, 0.5, 0.36, 0.3], own={(1, 1): "sec"})
    console_desk(R, A, X1 - 0.95, 0.0, 2.4, (0, 0, -H_PI), depth=0.7, seed=37, screens=3, tilt=0.5)
    # --- ceiling: beacons + strip lamps + pipes
    for i, (bx, by) in enumerate(((-1.8, 1.2), (0.0, 1.4), (1.8, 1.2), (-1.8, -1.2), (1.8, -1.2), (0.0, -0.9))):
        R.cyl("metal_dark", 0.11, 0.06, (bx, by, H - 0.03), segs=8)
        R.dyn(f"DYN_bcn{i}", em(("EMIT_bcn", (0.35, 0.03, 0.02), (1.0, 0.1, 0.05))), lambda bm: tube_bm(bm, [(0, 0, -0.12), (0, 0, 0)], 0.08, 8), loc=(bx, by, H - 0.06))
        R.light(f"bcn{i}", (bx, by, H - 0.45), (1.0, 0.1, 0.06), 1.0, 5.5)
    ceiling_lamp(R, "k1", (-0.9, -0.2, H), 1.2, (0.7, 0.9, 0.75), 0.6)
    ceiling_lamp(R, "k2", (0.9, -0.2, H), 1.2, (0.7, 0.9, 0.75), 0.6)
    for y in (-1.4, 0.0, 1.4):
        R.box("metal_dark", (X1 - X0, 0.2, 0.15), (0, y, H - 0.075))
    pipe_run(R, [(X0, Y1 - 0.2, H - 0.12), (X1, Y1 - 0.2, H - 0.12)], r=0.07)
    pipe_run(R, [(X0 + 0.2, Y0, H - 0.25), (X0 + 0.2, Y1, H - 0.25)], r=0.05, m="metal_orange")
    for k in range(8):
        cable(R, (-2.0 + k * 0.5, Y1 - 0.4, 0.9), (-1.8 + k * 0.45, 0.6, 0.02), sag=0.0, r=0.025)
    # chair + junk
    chair(R, (0.15, 0.25, 0), PI + 0.25, name="DYN_chair_ctrl")
    R.box("metal_dark", (0.5, 0.5, 0.9), (X0 + 0.3, Y0 + 0.35, 0.45))
    R.box("plastic_beige", (0.4, 0.3, 0.3), (X0 + 0.3, Y0 + 0.35, 1.05), rot=(0, 0, 0.2))
    sec_camera(R, (X1 - 0.2, Y0 + 0.25, H - 0.2), PI * 0.78, tilt=-0.45)
    R.anchor("CAM_sec", (X1 - 0.35, Y0 + 0.4, H - 0.3))
    R.decal("sg_ctrl", 0.8, 0.32, (-0.9, Y0 + 0.01, 2.25), (0, 0, PI))
    R.light("fill", (0, -0.6, 1.8), (0.5, 0.8, 0.6), 0.25, 6)
    R.light("mainscr", (0, yw - 0.8, 1.5), (0.4, 1.0, 0.5), 0.7, 4)
    print("ctrl atlas cells", A.i)
    return R


# =====================================================================  LIFE SUPPORT RING (scene D)
def ring_geo(bm, rad, tube=0.16, segs=24, plates=True, spokes=8):
    pts = [Vector((math.cos(2 * PI * k / segs) * rad, 0, math.sin(2 * PI * k / segs) * rad)) for k in range(segs + 1)]
    tube_bm(bm, pts, tube, 8, caps=False, ring_step=10)


def ring():
    R = Room("ring"); A = Atlas()
    X0, X1, Y0, Y1, H = -4.0, 4.0, -4.0, 4.0, 4.2
    floor_ceiling(R, X0, X1, Y0, Y1, H)
    wall_seg(R, "y", Y0, X0, X1, H, +1, gaps=[(0.0, 1.2, 2.1)], m="wall_teal")
    wall_seg(R, "y", Y1, X0, X1, H, -1, m="wall_teal")
    wall_seg(R, "x", X0, Y0, Y1, H, +1, m="wall_teal")
    wall_seg(R, "x", X1, Y0, Y1, H, -1, m="wall_teal")
    doorway(R, 0.0, Y0, 1.2, 2.1, PI, depth=1.2)
    # sunken pit + hazard ring on the floor
    R.box("hazard", (4.2, 4.2, 0.02), (0, 0.6, 0.006), faces="Z", seg=0.5)
    R.box("floor_grate", (3.8, 3.8, 0.03), (0, 0.6, 0.015), faces="Z", seg=0.5)
    cy, cz, RAD = 0.6, 2.05, 1.55
    # support towers either side, axle along Y
    for sx in (-1, 1):
        R.box("metal_orange", (0.35, 0.6, 3.6), (sx * (RAD + 0.55), cy, 1.8))
        R.box("metal_dark", (0.5, 0.8, 0.3), (sx * (RAD + 0.55), cy, 0.15))
        R.box("metal_dark", (0.6, 0.7, 0.5), (sx * (RAD + 0.45), cy, cz))
        R.tube("metal_dark", [(sx * (RAD + 0.3), cy, cz), (sx * 0.3, cy, cz)], 0.07, 8)
        R.decal("hazard", 0.3, 0.6, (sx * (RAD + 0.55), cy - 0.31, 0.8), (0, 0, 0))
    R.box("metal_orange", (2 * RAD + 1.45, 0.6, 0.35), (0, cy, 3.75))
    R.box("metal_dark", (0.6, 1.6, 0.6), (0, cy + 1.2, cz))
    R.tube("metal_dark", [(0, cy + 0.3, cz), (0, cy + 1.2, cz)], 0.2, 10)
    # the ring itself (rotates about Blender Y)
    def ring_main(bm):
        ring_geo(bm, RAD, 0.17, 28)
        for k in range(8):
            a = 2 * PI * k / 8
            tube_bm(bm, [Vector((math.cos(a) * 0.32, 0, math.sin(a) * 0.32)), Vector((math.cos(a) * (RAD - 0.1), 0, math.sin(a) * (RAD - 0.1)))], 0.045, 6)
        tube_bm(bm, [Vector((0, -0.25, 0)), Vector((0, 0.25, 0))], 0.32, 10)
        for k in range(12):
            a = 2 * PI * (k + 0.5) / 12
            box_bm(bm, 0.36, 0.42, 0.14, seg=0, M=TR((math.cos(a) * RAD, 0, math.sin(a) * RAD), (0, -a + H_PI, 0)))
    rg = R.dyn("DYN_ring", "metal_orange", ring_main, loc=(0, cy, cz))
    def ring_lights(bm):
        for k in range(12):
            a = 2 * PI * k / 12
            box_bm(bm, 0.07, 0.05, 0.07, seg=0, M=TR((math.cos(a) * (RAD + 0.17), -0.12, math.sin(a) * (RAD + 0.17))))
    R.dyn("DYN_ring_led", em(E_AMB), ring_lights, parent=rg)
    # nested "impossible" rings (hidden until the loop breaks)
    for nm, rad, m in (("DYN_ringB", 1.12, "metal_bare"), ("DYN_ringC", 0.78, "metal_red"), ("DYN_ringD", 2.15, "flesh")):
        def bb(bm, rad=rad):
            ring_geo(bm, rad, 0.11 if rad < 2 else 0.22, 24)
            for k in range(8):
                a = 2 * PI * (k + 0.5) / 8
                box_bm(bm, 0.24, 0.3, 0.1, seg=0, M=TR((math.cos(a) * rad, 0, math.sin(a) * rad), (0, -a + H_PI, 0)))
        R.dyn(nm, m, bb, loc=(0, cy, cz))
    # flesh growths for the surreal beat
    rnd = random.Random(9)
    spots = [(X0 + 0.1, rnd.uniform(-3, 3), rnd.uniform(0.6, 3.6)) for _ in range(6)] + [(X1 - 0.1, rnd.uniform(-3, 3), rnd.uniform(0.6, 3.6)) for _ in range(6)] + \
            [(rnd.uniform(-3, 3), Y1 - 0.1, rnd.uniform(0.6, 3.6)) for _ in range(6)] + [(rnd.uniform(-3, 3), rnd.uniform(-3, 3), H - 0.1) for _ in range(6)]
    for i, (fx, fy, fz) in enumerate(spots):
        rr = rnd.uniform(0.45, 1.0)
        def blob(bm, rr=rr, seed=i):
            res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rr)
            rr2 = random.Random(seed)
            for v in bm.verts:
                n = v.co.normalized()
                v.co *= 0.75 + 0.4 * rr2.random() + 0.25 * math.sin(n.x * 5 + seed) * math.sin(n.z * 4)
        R.dyn(f"FLESH_{i}", "flesh", blob, loc=(fx, fy, fz))
    # tanks + pipes to the machine
    for i, (tx, ty) in enumerate(((-3.2, 3.1), (3.2, 3.1), (-3.2, -2.4), (3.2, -2.4), (-3.2, 1.5))):
        tank(R, (tx, ty, 0), 0.5, 2.6 if i < 2 else 2.0, m="metal_teal" if i % 2 else "metal_bare", label="sg_n2", rot=(H_PI if tx < 0 else -H_PI))
        R.tube("pipe", [(tx, ty, 2.7 if i < 2 else 2.1), (tx, ty, 3.4), (tx * 0.62, cy, 3.4), (tx * 0.62, cy, 3.9)], 0.07, 8)
    # railing around the pit (octagon)
    oct_pts = [(math.cos(2 * PI * k / 8 + PI / 8) * 2.7, cy + math.sin(2 * PI * k / 8 + PI / 8) * 2.7, 0) for k in range(9)]
    railing(R, oct_pts[3:9] + [oct_pts[0], oct_pts[1]], h=1.05)
    # control pedestal near the entrance with a marquee screen
    Mp = TR((-1.1, -2.2, 0), (0, 0, 0.35))
    box_bm(R.bm("metal_dark"), 0.6, 0.5, 1.0, seg=0, M=Mp @ TR((0, 0, 0.5)))
    box_bm(R.bm("console_top"), 0.66, 0.5, 0.06, seg=0, M=Mp @ TR((0, -0.05, 1.05), (0.4, 0, 0)))
    box_bm(R.bm("crt_shell"), 0.5, 0.3, 0.38, seg=0, M=Mp @ TR((0, 0.12, 1.32)))
    R.screen("ring", 0.4, 0.28, P(Mp, 0, -0.035, 1.33), (0, 0, 0.35))
    # lights
    cage_lamp(R, "r1", (X0 + 0.12, -1.0, 3.0), (1, 0, 0), (1.0, 0.7, 0.4), 1.4, 9)
    cage_lamp(R, "r2", (X1 - 0.12, -1.0, 3.0), (-1, 0, 0), (1.0, 0.7, 0.4), 1.4, 9)
    cage_lamp(R, "r3", (0, Y1 - 0.12, 3.6), (0, -1, 0), (0.6, 1.0, 0.8), 1.0, 9)
    R.light("ringglow", (0, cy - 0.8, cz), (1.0, 0.6, 0.25), 0.8, 4)
    for y in (-2.5, -1.0, 2.2):
        R.box("metal_dark", (X1 - X0, 0.25, 0.25), (0, y, H - 0.12))
    R.decal("sg_lifesup", 0.96, 0.32, (2.0, Y0 + 0.01, 2.6), (0, 0, PI))
    R.decal("sg_hiP", 0.6, 0.3, (X0 + 0.01, -0.5, 1.6), (0, 0, H_PI))
    return R


# =====================================================================  CREW QUARTERS (scenes E, F)
def quarters():
    R = Room("quarters"); A = Atlas()
    X0, X1, Y0, Y1, H = -2.6, 2.6, -2.3, 2.3, 2.45
    floor_ceiling(R, X0, X1, Y0, Y1, H, mf="floor_rubber")
    wall_seg(R, "y", Y0, X0, X1, H, +1, gaps=[(-1.4, 1.0, 2.05)])
    wall_seg(R, "y", Y1, X0, X1, H, -1)
    wall_seg(R, "x", X0, Y0, Y1, H, +1)
    wall_seg(R, "x", X1, Y0, Y1, H, -1)
    doorway(R, -1.4, Y0, 1.0, 2.05, PI, depth=1.2)
    # chronometer on the north wall
    Mc = TR((0.3, Y1 - 0.02, 1.75), (0, 0, 0))
    box_bm(R.bm("metal_dark"), 1.2, 0.2, 0.62, seg=0, M=Mc @ TR((0, -0.1, 0)))
    box_bm(R.bm("crt_shell"), 1.06, 0.06, 0.46, seg=0, M=Mc @ TR((0, -0.22, 0)))
    box_bm(R.bm("metal_dark"), 0.94, 0.01, 0.36, seg=0, M=Mc @ TR((0, -0.255, 0)))
    R.screen("clock", 0.9, 0.34, P(Mc, 0, -0.262, 0), (0, 0, 0))
    ind = em(("EMIT_ind", (0.3, 0.03, 0.02), (1.0, 0.1, 0.06)))
    k = 0
    for xx in (-0.5, -0.3, -0.1, 0.1, 0.3, 0.5):
        for zz in (0.42, -0.42):
            R.dyn(f"DYN_ind{k}", ind, lambda bm: tube_bm(bm, [(0, 0, 0), (0, -0.05, 0)], 0.035, 8), loc=P(Mc, xx, -0.2, zz))
            R.cyl("metal_dark", 0.05, 0.04, P(Mc, xx, -0.18, zz), (H_PI, 0, 0), segs=8)
            k += 1
    R.box("metal_dark", (0.06, 0.06, 0.8), (0.3, Y1 - 0.05, 2.45 - 0.4 + 0.12))
    R.light("clock", P(Mc, 0, -0.7, 0), (1.0, 0.15, 0.08), 0.6, 3.5)
    R.decal("sg_deck", 0.48, 0.12, P(Mc, 0, -0.205, -0.6), (0, 0, 0))
    gauge_cluster(R, TR((-0.9, Y1 - 0.01, 1.75)), (0, 0, 0), 2, pitch=0.14, r=0.05)
    # lockers on the east wall (faces -X); locker 2 holds the phone
    locker_row(R, X1 - 0.5, 0.5, 5, -H_PI)
    # the phone on the locker shelf
    def phone(bm):
        box_bm(bm, 0.075, 0.155, 0.01, seg=0, M=TR((0, 0, 0)))
    ph = R.dyn("DYN_phone_lk", "rubber", phone, loc=(X1 - 0.28, -0.5, 1.52), rot=(0.0, 0, 0.3))
    R.screen("phone_lk", 0.066, 0.14, (0, 0, 0.0055), (-H_PI, 0, 0), parent=ph)
    R.light("phone", (X1 - 0.45, -0.5, 1.6), (0.6, 0.8, 1.0), 0.25, 1.5)
    # bunk + porthole on the west wall
    bunk(R, (X0 + 0.5, 0.8, 0), 0)
    porthole(R, (X0 + 0.01, -0.8, 1.55), H_PI)
    # table, chairs, pendant
    table(R, (0.3, 0.0, 0), 0.1)
    chair(R, (-0.1, -0.65, 0), 0.4, name="DYN_chairA", m_seat="fabric_blue")
    chair(R, (0.85, 0.55, 0), PI - 0.3, name="DYN_chairB", m_seat="fabric_blue")
    def items(bm):
        box_bm(bm, 0.3, 0.22, 0.02, seg=0, M=TR((0, 0, 0.01)))
        tube_bm(bm, [Vector((0.25, 0.1, 0)), Vector((0.25, 0.1, 0.1))], 0.04, 8)
        tube_bm(bm, [Vector((-0.3, -0.05, 0)), Vector((-0.3, -0.05, 0.13))], 0.035, 8)
        box_bm(bm, 0.12, 0.08, 0.16, seg=0, M=TR((0.05, -0.2, 0.08), (0, 0, 0.4)))
    R.dyn("DYN_items", "plastic_beige", items, loc=(0.3, 0.0, 0.765), rot=(0, 0, 0.1))
    pendant_lamp(R, "pend", (0.3, 0.0, 1.75), (1.0, 0.45, 0.25), 1.2, 5)
    # shelf + posters
    shelf(R, (-0.9, Y1 - 0.02, 0), PI, w=1.0, levels=(1.1, 1.5), seed=41)
    R.decal("poster_sun", 0.48, 0.64, (1.6, Y1 - 0.01, 1.55), (0, 0, 0))
    R.decal("poster_ship", 0.48, 0.64, (X0 + 0.01, -1.7, 1.5), (0, 0, H_PI))
    R.decal("sg_quarters", 0.8, 0.32, (0.6, Y0 + 0.01, 2.0), (0, 0, PI))
    for y in (-1.2, 0.0, 1.2):
        R.box("metal_dark", (X1 - X0, 0.16, 0.12), (0, y, H - 0.06))
    pipe_run(R, [(X0 + 0.12, Y0, H - 0.15), (X0 + 0.12, Y1, H - 0.15)], r=0.05)
    pipe_run(R, [(X0, Y1 - 0.12, H - 0.25), (X1, Y1 - 0.12, H - 0.25)], r=0.05, m="metal_orange")
    ceiling_lamp(R, "q1", (-1.2, -1.2, H - 0.12), 0.8, (1.0, 0.85, 0.65), 0.5)
    junction_box(R, (X1 - 0.08, 1.6, 1.6), -H_PI)
    R.light("fill", (0, -0.5, 1.6), (0.7, 0.55, 0.45), 0.2, 6)
    return R


# =====================================================================  CREW (figure, patient, FP hand + phone)
def person(R, name, M, lying=False, face_tex="face_closed"):
    """low-poly crew member in an orange-grey jumpsuit, built standing at local origin (feet), facing local -Y"""
    S = "suit"
    def part(m, sx, sy, sz, loc, rot=(0, 0, 0)):
        box_bm(R.bm(m), sx, sy, sz, seg=0.25, M=M @ TR(loc, rot))
    # legs
    for sx in (-1, 1):
        part("rubber", 0.13, 0.26, 0.1, (sx * 0.1, -0.04, 0.05))
        R.tube(S, [M @ Vector((sx * 0.1, 0, 0.1)), M @ Vector((sx * 0.1, 0.01, 0.5)), M @ Vector((sx * 0.11, 0, 0.92))], 0.075, 6, r2=0.095)
    # torso (tapered), belt, collar
    R.tube(S, [M @ Vector((0, 0, 0.88)), M @ Vector((0, 0.0, 1.15)), M @ Vector((0, 0.01, 1.45))], 0.17, 8, r2=0.2)
    part("suit_orange", 0.36, 0.25, 0.06, (0, 0, 0.95))
    part("suit_orange", 0.08, 0.02, 0.1, (0.1, -0.18, 1.3))
    R.tube(S, [M @ Vector((0, 0, 1.44)), M @ Vector((0, 0, 1.5))], 0.2, 8, r2=0.1)
    # arms
    for sx in (-1, 1):
        R.tube(S, [M @ Vector((sx * 0.24, 0, 1.42)), M @ Vector((sx * 0.27, 0.02, 1.15)), M @ Vector((sx * 0.28, -0.03, 0.88))], 0.065, 6, r2=0.05)
        part("skin", 0.07, 0.09, 0.14, (sx * 0.28, -0.04, 0.8))
    # neck + head
    R.tube("skin", [M @ Vector((0, 0, 1.48)), M @ Vector((0, 0, 1.58))], 0.055, 6)
    part("skin", 0.19, 0.22, 0.25, (0, -0.01, 1.7))
    # hair: cap + jagged fringe
    part("hair", 0.21, 0.24, 0.1, (0, 0.0, 1.83))
    part("hair", 0.21, 0.1, 0.2, (0, 0.08, 1.74))
    for k in range(5):
        part("hair", 0.05, 0.04, 0.09 + 0.03 * (k % 2), (-0.09 + k * 0.045, -0.12, 1.77), (0.2, 0, 0.1 * (k - 2)))
    for sx in (-1, 1):
        part("hair", 0.03, 0.18, 0.16, (sx * 0.105, 0.0, 1.73))
    face = R.quad(f"FACE_{name}", face_tex, 0.17, 0.2, tuple(M @ Vector((0, -0.124, 1.69))), tuple(M.to_euler()))
    return face


def crew():
    import characters
    R = Room("crew")
    characters.build(R)
    return R


ROOMS = {"med": med, "corr": corr, "ctrl": ctrl, "ring": ring, "quarters": quarters, "crew": crew}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1]
    random.seed(1)
    lib.reset()
    R = ROOMS[which]()
    R.finish()
    lib.all_uvs(R.coll)
    lib.bake_ao(R.coll, samples=40, distance=0.8 if which != "crew" else 0.15)
    lib.export(R.coll, which + ".glb")
    lib.save_blend(which + ".blend")
