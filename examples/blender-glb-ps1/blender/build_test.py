"""Pipeline test: a short tech corridor ending in the EMERGENCY EXIT hatch."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib, kit
from lib import Room, mat
from kit import *

lib.reset()
R = Room("test")
H = 2.5
floor_ceiling(R, -1.2, 1.2, 0, 6, H)
wall_x(R, -1.2, 0, 6, H, +1)
wall_x(R, 1.2, 0, 6, H, -1)
heavy_door(R, "exit", 0, 6, wall_h=H)
for y in (1.4, 3.0, 4.6):
    rib_y(R, y, -1.2, 1.2, H)
cage_lamp(R, "lampA", (-1.08, 2.2, 2.05), face=(1, 0, 0), color=(1.0, 0.85, 0.6), power=1.0)
pipe_run(R, [(1.0, -0.2, 2.3), (1.0, 6.0, 2.3)], r=0.07)
pipe_run(R, [(0.82, -0.2, 2.36), (0.82, 6.0, 2.36)], r=0.05, m="metal_orange")
pipe_run(R, [(-0.95, -0.2, 2.34), (-0.95, 5.2, 2.34), (-0.95, 5.2, 0.4), (-0.95, 5.9, 0.4)], r=0.05, m="metal_teal")
tech_panel(R, "panel", (1.06, 5.0, 1.35), (0, 0, math.pi / 2))
for i in range(4):
    cable(R, (1.1, 0.3 + i * 0.12, 2.2), (1.1, 2.6 + i * 0.1, 2.2), sag=0.35 + 0.08 * i)
R.decal("sg_arrow", 0.32, 0.16, (-1.07, 4.0, 1.5), (0, 0, -math.pi / 2))
R.decal("sg_deck", 0.48, 0.12, (1.07, 2.2, 1.7), (0, 0, math.pi / 2))
R.decal("sg_poster", 0.32, 0.48, (-1.07, 0.8, 1.4), (0, 0, -math.pi / 2))
# compartment behind the hatch
floor_ceiling(R, -2, 2, 6, 10, H)
wall_y(R, 10, -2, 2, H, -1, m="wall_teal")
wall_x(R, -2, 6, 10, H, +1, m="wall_teal")
wall_x(R, 2, 6, 10, H, -1, m="wall_teal")
R.box("metal_orange", (0.8, 0.6, 0.9), (1.3, 9.4, 0.45))
R.box("metal_dark", (0.6, 0.6, 0.6), (1.3, 9.4, 1.2), rot=(0, 0, 0.3))
ceiling_lamp(R, "far", (0, 8.2, H), color=(0.8, 0.9, 1.0), power=0.6)
R.anchor("CAM_start", (0, 0.6, 1.6))
R.anchor("FIG_spot", (-0.4, 9.2, 0))
R.finish()
lib.all_uvs(R.coll)
lib.bake_ao(R.coll, samples=32)
lib.export(R.coll, "test.glb")
lib.save_blend("test.blend")
