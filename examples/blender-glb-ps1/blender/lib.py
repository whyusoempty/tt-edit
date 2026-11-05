"""Low-poly kit for ПОСЛЕДНЯЯ СМЕНА, run inside Blender (blender -b --python <room>.py).

Conventions (Blender space, Z up, metres):
  * static geometry is written with identity object transforms, so world-space
    box-projected UVs line up across pieces (consistent ~32 px / m texel density);
  * dynamic pieces are named DYN_*, their origin is the pivot, UVs are local;
  * screens are SCR_* quads with 0..1 UVs (Three.js swaps in a canvas texture);
  * decals are DEC_* quads with 0..1 UVs;
  * emissive materials are EMIT_*; glass is GLASS;
  * light anchors are empties L_* with extras {color, power, dist};
  * camera anchors are empties CAM_* (just positions, read by Three.js).
After building: bake AO into vertex colours (Cycles), join static meshes, export GLB.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
TEX = os.path.join(ROOT, "assets", "tex")
MODELS = os.path.join(ROOT, "assets", "models")

# texture tile size in metres (u, v)
TILE = {
    "wall_panel": (2, 2), "wall_teal": (2, 2), "wall_lower": (2, 1), "ceiling": (2, 2),
    "floor_grate": (2, 2), "floor_rubber": (2, 2), "floor_lino": (2, 2),
    "hazard": (0.5, 0.25), "locker": (0.5, 1.0), "pipe": (1, 0.5), "console_top": (0.6, 0.6),
    "vent": (0.5, 0.5), "door_heavy": (1, 1),
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


# ------------------------------------------------------------------ materials
_M = {}


def mat(name, color=None, emit=None, alpha=None):
    """name = texture basename (assets/tex/<name>.png) or EMIT_* / GLASS / FLAT_*"""
    if name in _M:
        return _M[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    path = os.path.join(TEX, name + ".png")
    if os.path.exists(path):
        img = bpy.data.images.load(path, check_existing=True)
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = img
        tn.interpolation = "Closest"
        nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
        if alpha:
            nt.links.new(tn.outputs["Alpha"], bsdf.inputs["Alpha"])
    elif color:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = 1.0
    if alpha:
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
        m.surface_render_method = "BLENDED"
    _M[name] = m
    return m


# ------------------------------------------------------------------ mesh building
def _grid_face(bm, o, u, v, nu, nv):
    vs = [[bm.verts.new(o + u * (i / nu) + v * (j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    return [x for row in vs for x in row]


def box_bm(bm, sx, sy, sz, seg=0.5, M=None, faces="xXyYzZ"):
    """box centred at origin, every face gridded at ~seg metres; faces selects which sides exist"""
    n = lambda s: max(1, round(s / seg)) if seg else 1
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    X, Y, Z = Vector((sx, 0, 0)), Vector((0, sy, 0)), Vector((0, 0, sz))
    made = []
    spec = {
        "X": (Vector((hx, -hy, -hz)), Y, Z, n(sy), n(sz)),
        "x": (Vector((-hx, -hy, -hz)), Z, Y, n(sz), n(sy)),
        "Y": (Vector((-hx, hy, -hz)), Z, X, n(sz), n(sx)),
        "y": (Vector((-hx, -hy, -hz)), X, Z, n(sx), n(sz)),
        "Z": (Vector((-hx, -hy, hz)), X, Y, n(sx), n(sy)),
        "z": (Vector((-hx, -hy, -hz)), Y, X, n(sy), n(sx)),
    }
    for k in faces:
        o, u, v, nu, nv = spec[k]
        made += _grid_face(bm, o, u, v, nu, nv)
    bmesh.ops.remove_doubles(bm, verts=made, dist=1e-5)
    made = [v for v in made if v.is_valid]
    if M is not None:
        bmesh.ops.transform(bm, matrix=M, verts=made)
    return made


def _tail(bm, start):
    bm.verts.ensure_lookup_table()
    return [bm.verts[i] for i in range(start, len(bm.verts))]


def tube_bm(bm, pts, r, segs=8, caps=True, ring_step=0.6, r2=None):
    """tube along polyline pts (list of Vector); radius r (optionally tapering to r2)"""
    pts = [Vector(p) for p in pts]
    dense = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        k = max(1, math.ceil((b - a).length / ring_step))
        for i in range(1, k + 1):
            dense.append(a.lerp(b, i / k))
    rings = []
    total = len(dense)
    for i, p in enumerate(dense):
        if i == 0:
            d = dense[1] - dense[0]
        elif i == total - 1:
            d = dense[-1] - dense[-2]
        else:
            d = (dense[i + 1] - dense[i - 1])
        d.normalize()
        ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        a = d.cross(ref).normalized()
        b = d.cross(a).normalized()
        rr = r if r2 is None else r + (r2 - r) * i / (total - 1)
        rings.append([bm.verts.new(p + (a * math.cos(t) + b * math.sin(t)) * rr)
                      for t in [2 * math.pi * s / segs for s in range(segs)]])
    for r0, r1 in zip(rings, rings[1:]):
        for s in range(segs):
            bm.faces.new((r0[s], r0[(s + 1) % segs], r1[(s + 1) % segs], r1[s]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return rings


def obj_from_bm(name, bm, m, coll):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    if isinstance(m, (list, tuple)):
        for mm in m:
            me.materials.append(mm)
    else:
        me.materials.append(m)
    coll.objects.link(ob)
    return ob


def TR(loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    return Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Scale(scale, 4)


class Room:
    """collects static geometry per material into one bmesh each (fast, few objects)"""

    def __init__(self, name):
        self.name = name
        self.coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(self.coll)
        self.static = {}  # matname -> bmesh
        self.n = 0

    def bm(self, matname):
        if matname not in self.static:
            self.static[matname] = bmesh.new()
        return self.static[matname]

    # --- static primitives
    def box(self, m, size, loc, rot=(0, 0, 0), seg=0.5, faces="xXyYzZ"):
        box_bm(self.bm(m), *size, seg=seg, M=TR(loc, rot), faces=faces)

    def tube(self, m, pts, r, segs=8, caps=True, r2=None):
        tube_bm(self.bm(m), pts, r, segs, caps, r2=r2)

    def cyl(self, m, r, h, loc, rot=(0, 0, 0), segs=10, r2=None, caps=True):
        M = TR(loc, rot)
        bm = self.bm(m)
        rings = tube_bm(bm, [Vector((0, 0, -h / 2)), Vector((0, 0, h / 2))], r, segs, caps, r2=r2)
        bmesh.ops.transform(bm, matrix=M, verts=[v for rg in rings for v in rg])

    # --- separate objects
    def dyn(self, name, m, build, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
        """build(bm) writes local geometry; object origin = pivot at loc"""
        bm = bmesh.new()
        build(bm)
        ob = obj_from_bm(name, bm, mat(m) if isinstance(m, str) else m, self.coll)
        ob.location = loc
        ob.rotation_euler = rot
        if parent:
            ob.parent = parent
        ob["uv_local"] = 1
        return ob

    def quad(self, name, m, w, h, loc, rot=(0, 0, 0), parent=None, uv=(0, 0, 1, 1)):
        """vertical quad facing -Y (towards a viewer standing at -Y) before rotation"""
        bm = bmesh.new()
        a = [bm.verts.new(p) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
        f = bm.faces.new(a)
        lay = bm.loops.layers.uv.new("UVMap")
        u0, v0, u1, v1 = uv
        for lp, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
            lp[lay].uv = (u, v)
        ob = obj_from_bm(name, bm, mat(m) if isinstance(m, str) else m, self.coll)
        ob.location = loc
        ob.rotation_euler = rot
        if parent:
            ob.parent = parent
        ob["uv_fixed"] = 1
        return ob

    def decal(self, texname, w, h, loc, rot=(0, 0, 0), parent=None):
        self.n += 1
        return self.quad(f"DEC_{texname}_{self.n}", texname, w, h, loc, rot, parent)

    def screen(self, name, w, h, loc, rot=(0, 0, 0), parent=None):
        return self.quad("SCR_" + name, mat("EMIT_screen", color=(0.1, 0.2, 0.1), emit=(0.2, 0.5, 0.2)), w, h, loc, rot, parent)

    def light(self, name, loc, color=(1, 0.9, 0.7), power=1.0, dist=6.0):
        e = bpy.data.objects.new("L_" + name, None)
        e.location = loc
        e["color"] = list(color)
        e["power"] = power
        e["dist"] = dist
        self.coll.objects.link(e)
        return e

    def anchor(self, name, loc, parent=None):
        e = bpy.data.objects.new(name, None)
        e.location = loc
        if parent:
            e.parent = parent
        self.coll.objects.link(e)
        return e

    def finish(self):
        """turn the per-material bmeshes into objects"""
        out = []
        for m, bm in self.static.items():
            ob = obj_from_bm(f"ST_{self.name}_{m}", bm, mat(m), self.coll)
            out.append(ob)
        self.static = {}
        return out


# ------------------------------------------------------------------ UVs
def uv_box(ob, tile=None):
    me = ob.data
    t = tile or TILE.get(me.materials[0].name if me.materials else "", (1, 1))
    if isinstance(t, (int, float)):
        t = (t, t)
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for lp in f.loops:
            c = lp.vert.co
            if az >= ax and az >= ay:
                u, v = c.x, c.y * (1 if n.z > 0 else -1)
            elif ax >= ay:
                u, v = c.y * (1 if n.x > 0 else -1), c.z
            else:
                u, v = -c.x * (1 if n.y > 0 else -1), c.z
            lp[lay].uv = (u / t[0], v / t[1])
    bm.to_mesh(me)
    bm.free()


def tube_uv(ob, length_tile=1.0):
    """for tubes: u around, v along — approximated by box projection on the long axis"""
    uv_box(ob, (length_tile, length_tile))


def all_uvs(coll):
    for ob in coll.all_objects:
        if ob.type != "MESH" or ob.get("uv_fixed") or ob.get("uv_own"):
            continue
        uv_box(ob)


# ------------------------------------------------------------------ AO bake into vertex colours
def bake_ao(coll, samples=48, distance=0.7):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.device = "CPU"
    if not sc.world:
        sc.world = bpy.data.worlds.new("W")
    sc.world.light_settings.distance = distance
    bpy.ops.object.select_all(action="DESELECT")
    targets = []
    hidden = []
    for ob in coll.all_objects:
        if ob.type == "MESH" and ob.name.startswith(("FLESH_", "DYN_ringB", "DYN_ringC", "DYN_ringD")):
            ob.hide_render = True
            hidden.append(ob)
            continue
        if ob.type != "MESH" or ob.get("uv_fixed") or ob.name.startswith(("SCR_", "DEC_")):
            continue
        me = ob.data
        if "Col" not in me.color_attributes:
            me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        me.color_attributes.active_color = me.color_attributes["Col"]
        ob.select_set(True)
        targets.append(ob)
    if not targets:
        return
    bpy.context.view_layer.objects.active = targets[0]
    sc.render.bake.target = "VERTEX_COLORS"
    bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")
    bpy.ops.object.select_all(action="DESELECT")
    for ob in hidden:
        ob.hide_render = False


def export(coll, filename):
    os.makedirs(MODELS, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in coll.all_objects:
        ob.select_set(True)
    path = os.path.join(MODELS, filename)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_apply=True,
        export_yup=True, export_vertex_color="ACTIVE", export_all_vertex_colors=False,
        export_extras=True, export_lights=False, export_cameras=False,
        export_image_format="AUTO", export_materials="EXPORT",
    )
    print("EXPORTED", path, os.path.getsize(path))


def save_blend(filename):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, filename))
