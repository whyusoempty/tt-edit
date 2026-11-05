"""Crew man for crew.glb: organic low-poly body (skin modifier + one subdivision), a sculpted head
with a painted wrap-around face (faces.py / headparam.py), ragged hair strands, and the
first-person hand holding the phone.  Called from build_rooms.crew().

Object names are what world.html keys on:
  STAND_* + FACE_stand   standing man (the figure / the hero on CCTV)
  LIE_*   + FACE_lie     the patient in the capsule (eyes closed texture, swapped to open at the end)
  HAND_*  + SCR_phone    first-person hand
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix
import lib
from lib import mat, box_bm, TR
import headparam as HP

PI = math.pi


def G(X, Z, cx, cz, sx, sz):
    return math.exp(-(((X - cx) / sx) ** 2 + ((Z - cz) / sz) ** 2))


# ------------------------------------------------------------------ head
def head_point(a, nz):
    """surface point (head centre = origin, front = -Y) for parameter (a, nz)"""
    cl = math.sqrt(max(0.0, 1 - nz * nz))
    nx, f = math.sin(a) * cl, math.cos(a) * cl
    X, Z = HP.AX * nx, HP.AZ * nz
    x, y, z = X, -HP.AY * f, Z
    if nz < 0:
        x *= 1 - 0.30 * (-nz) ** 1.6                       # jaw narrows to the chin
        if f < 0:
            y *= 1 - 0.38 * (-nz) ** 1.3                   # back of the head tucks into the neck
    elif f < 0:
        y *= 1.07                                          # fuller skull at the back
    if f > 0:
        y *= 1 - 0.10 * f ** 6                             # flatter face plane
    ax = abs(X)
    d = 0.0
    d += 0.016 * G(X, Z, 0, HP.NOSE_TIP_Z + 0.003, 0.0075, 0.0085)    # nose tip
    d += 0.008 * G(X, Z, 0, -0.008, 0.0055, 0.015)                    # nose bridge
    d += 0.0045 * G(ax, Z, HP.EYE_X, HP.BROW_Z - 0.002, 0.015, 0.006)  # brow ridge
    d -= 0.0055 * G(ax, Z, HP.EYE_X, HP.EYE_Z, 0.011, 0.0075)          # sockets
    d += 0.0028 * G(ax, Z, HP.EYE_X, HP.EYE_Z, 0.009, 0.0035)          # eyeball under the lid
    d += 0.0035 * G(ax, Z, 0.044, -0.016, 0.014, 0.012)                # cheekbones
    d += 0.0045 * G(X, Z, 0, HP.MOUTH_Z, 0.016, 0.008)                 # mouth
    d += 0.007 * G(X, Z, 0, HP.CHIN_Z + 0.008, 0.015, 0.012)           # chin
    d -= 0.002 * G(ax, Z, 0.045, -0.045, 0.012, 0.014)                 # hollow cheeks
    fw = min(1.0, max(0.0, (f - 0.3) / 0.4))
    y -= d * fw
    return Vector((x, y, z))


def head_rows():
    rows = [-0.975, -0.94, -0.89, -0.83, -0.765]
    z = -0.70
    while z < 0.33:
        rows.append(round(z, 4)); z += 0.035
    rows += [0.39, 0.47, 0.56, 0.65, 0.74, 0.83, 0.905, 0.96, 0.99]
    return rows


def build_head(name, material, M, NA=48):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rows = head_rows()
    us = [i / NA for i in range(NA)]
    as_ = [HP.ginv(u) if 0 < i else -PI for i, u in enumerate(us)]
    grid = [[bm.verts.new(M @ head_point(a, nz)) for a in as_] for nz in rows]
    bot = bm.verts.new(M @ head_point(0, -1.0) + Vector((0, 0, 0)))
    top = bm.verts.new(M @ head_point(0, 1.0))
    vv = [(nz + 1) / 2 for nz in rows]

    def U(i):
        return 1.0 if i == NA else us[i]

    for r in range(len(rows) - 1):
        for i in range(NA):
            j = (i + 1) % NA
            f = bm.faces.new((grid[r][i], grid[r][j], grid[r + 1][j], grid[r + 1][i]))
            for lp, (uu, v) in zip(f.loops, ((U(i), vv[r]), (U(i + 1), vv[r]), (U(i + 1), vv[r + 1]), (U(i), vv[r + 1]))):
                lp[uvl].uv = (uu, v)
    for i in range(NA):
        j = (i + 1) % NA
        f = bm.faces.new((grid[0][j], grid[0][i], bot))
        for lp, uv in zip(f.loops, ((U(i + 1), vv[0]), (U(i), vv[0]), ((U(i) + U(i + 1)) / 2, 0.0))):
            lp[uvl].uv = uv
        f = bm.faces.new((grid[-1][i], grid[-1][j], top))
        for lp, uv in zip(f.loops, ((U(i), vv[-1]), (U(i + 1), vv[-1]), ((U(i) + U(i + 1)) / 2, 1.0))):
            lp[uvl].uv = uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    ob = lib.obj_from_bm(name, bm, mat(material), COLL[0])
    ob["uv_own"] = 1
    return ob


def build_hair(name, M, seed):
    """ragged greasy strands rooted on the scalp, lying along the head"""
    rnd = random.Random(seed)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")

    def strand(a0, nz0, a1, nz1, w0, lift0=1.02, lift1=1.07, th=0.006, n=5):
        pts, nrm = [], []
        for k in range(n + 1):
            s = k / n
            e = s * s * (3 - 2 * s)
            a = a0 + (a1 - a0) * e
            nz = nz0 + (nz1 - nz0) * s
            p = head_point(a, nz)
            lift = lift0 + (lift1 - lift0) * s + 0.025 * math.sin(PI * s)
            pts.append(p * lift)
            nrm.append(p.normalized())
        ring = []
        for k, (p, nn) in enumerate(zip(pts, nrm)):
            t = (pts[min(k + 1, n)] - pts[max(k - 1, 0)]).normalized()
            side = t.cross(nn).normalized()
            w = w0 * (1 - k / n) ** 0.8 + 0.0008
            tt = th * (1 - 0.7 * k / n)
            ring.append([bm.verts.new(M @ (p + side * w / 2)), bm.verts.new(M @ (p + nn * tt)), bm.verts.new(M @ (p - side * w / 2))])
        for k in range(n):
            a, b = ring[k], ring[k + 1]
            v0, v1 = k / n, (k + 1) / n
            for (i, j), (u0, u1) in zip(((0, 1), (1, 2), (2, 0)), ((0, 0.5), (0.5, 1), (0, 1))):
                f = bm.faces.new((a[i], b[i], b[j], a[j]))
                for lp, uv in zip(f.loops, ((u0, v0), (u0, v1), (u1, v1), (u1, v0))):
                    lp[uvl].uv = uv

    j = lambda s: rnd.uniform(-s, s)
    # crown: spokes from the top outwards
    for k in range(12):
        a = -PI + 2 * PI * k / 12 + j(0.15)
        strand(a + j(0.3), 0.995, a + j(0.2), 0.5 + j(0.08), 0.06 + j(0.01))
    # mid layer: fringe over the forehead, sides over the ears, back down to the nape
    for k in range(22):
        a = -PI + 2 * PI * (k + 0.5) / 22 + j(0.08)
        aa = abs(a)
        if aa < 0.95:
            nz1 = 0.30 + j(0.05) + 0.06 * aa
            a1 = a + j(0.25)
        elif aa < 1.9:
            nz1 = 0.12 + j(0.07)
            a1 = a + 0.1 * math.copysign(1, a)
        else:
            nz1 = -0.38 + j(0.1)
            a1 = a + j(0.12)
        strand(a + j(0.1), 0.8, a1, nz1, 0.045 + j(0.008))
    # extra fringe clumps, messy
    for k in range(9):
        a = -0.85 + 1.7 * k / 8 + j(0.07)
        strand(a, 0.66, a + j(0.3), 0.27 + j(0.05), 0.032 + j(0.006), lift0=1.03, lift1=1.08)
    # lower back and side tufts
    for k in range(12):
        a = math.copysign(1.55 + (PI - 1.55) * (k // 2) / 5, 1 if k % 2 else -1) + j(0.1)
        strand(a, 0.45, a + j(0.1), -0.5 + j(0.08), 0.05, lift0=1.02, lift1=1.05)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    ob = lib.obj_from_bm(name, bm, mat("hair"), COLL[0])
    ob["uv_own"] = 1
    return ob


def add_ears(bm, M):
    for s in (-1, 1):
        p = head_point(s * PI / 2, -0.07)
        e = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=1.0)["verts"]
        bmesh.ops.transform(bm, matrix=M @ TR((p.x + s * 0.004, p.y + 0.008, p.z), (0, 0, s * -0.35)) @ Matrix.Diagonal((0.008, 0.016, 0.027, 1)), verts=e)


# ------------------------------------------------------------------ skin-modifier bodies
def skin_obj(name, verts, edges, radii, material, M, subsurf=1, squash=None):
    me = bpy.data.meshes.new(name + "_src")
    me.from_pydata([tuple(v) for v in verts], edges, [])
    ob = bpy.data.objects.new(name, me)
    COLL[0].objects.link(ob)
    sk = ob.modifiers.new("skin", "SKIN")
    sk.branch_smoothing = 0.6
    sk.use_smooth_shade = True
    for i, r in enumerate(radii):
        rr = r if isinstance(r, tuple) else (r, r)
        me.skin_vertices[0].data[i].radius = rr
    me.skin_vertices[0].data[0].use_root = True
    if subsurf:
        ss = ob.modifiers.new("sub", "SUBSURF")
        ss.levels = ss.render_levels = subsurf
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    ob.data = new
    new.name = name
    bpy.data.meshes.remove(me)
    if squash:
        squash(new)
    new.transform(M)
    for p in new.polygons:
        p.use_smooth = True
    new.materials.append(mat(material))
    return ob


def ring_bm(bm, z0, z1, rx0, ry0, rx1, ry1, segs, M, yoff=0.0):
    a = [bm.verts.new(M @ Vector((rx0 * math.cos(2 * PI * k / segs), yoff + ry0 * math.sin(2 * PI * k / segs), z0))) for k in range(segs)]
    b = [bm.verts.new(M @ Vector((rx1 * math.cos(2 * PI * k / segs), yoff + ry1 * math.sin(2 * PI * k / segs), z1))) for k in range(segs)]
    for k in range(segs):
        bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))


def torso_squash(me):
    for v in me.vertices:
        x, y, z = v.co
        w = min(1.0, max(0.0, (0.21 - abs(x)) / 0.07)) * min(1.0, max(0.0, (z - 0.82) / 0.1)) * min(1.0, max(0.0, (1.5 - z) / 0.06))
        v.co.y = y * (1 - 0.3 * w)


def person(prefix, face_name, face_mat, M, head_pitch=0.12, seed=3):
    # body: torso, arms, legs in one skin
    V = [(0, 0.0, 0.95), (0, -0.005, 1.1), (0, -0.01, 1.27), (0, 0.0, 1.39), (0, 0.005, 1.47),
         (-0.185, 0.01, 1.4), (-0.235, 0.025, 1.13), (-0.255, -0.005, 0.88),
         (0.185, 0.01, 1.4), (0.235, 0.025, 1.13), (0.255, -0.005, 0.88),
         (-0.09, 0, 0.9), (-0.1, -0.015, 0.5), (-0.1, 0.01, 0.12),
         (0.09, 0, 0.9), (0.1, -0.015, 0.5), (0.1, 0.01, 0.12)]
    E = [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5), (5, 6), (6, 7), (3, 8), (8, 9), (9, 10),
         (0, 11), (11, 12), (12, 13), (0, 14), (14, 15), (15, 16)]
    Rr = [0.145, 0.135, 0.16, 0.15, 0.062, 0.068, 0.052, 0.04, 0.068, 0.052, 0.04, 0.095, 0.068, 0.056, 0.095, 0.068, 0.056]
    skin_obj(prefix + "suit", V, E, Rr, "suit", M, squash=torso_squash)
    # hands (mitten + thumb), neck, boots
    HV, HE, HR = [], [], []
    for s in (-1, 1):
        b = len(HV)
        HV += [(s * 0.255, -0.005, 0.89), (s * 0.262, -0.015, 0.8), (s * 0.258, -0.03, 0.72), (s * 0.24, -0.055, 0.79)]
        HE += [(b, b + 1), (b + 1, b + 2), (b + 1, b + 3)]
        HR += [0.03, (0.036, 0.022), 0.02, 0.013]
    b = len(HV)
    HV += [(0, 0.008, 1.43), (0, 0.0, 1.6)]
    HE += [(b, b + 1)]
    HR += [0.05, 0.047]
    skin_obj(prefix + "skin", HV, HE, HR, "skin", M)
    BV, BE, BR = [], [], []
    for s in (-1, 1):
        b = len(BV)
        BV += [(s * 0.1, 0.02, 0.11), (s * 0.1, -0.05, 0.055), (s * 0.1, -0.13, 0.045)]
        BE += [(b, b + 1), (b + 1, b + 2)]
        BR += [0.062, 0.052, 0.042]
    skin_obj(prefix + "boots", BV, BE, BR, "rubber", M)
    # collar, belt, chest patch
    bm = bmesh.new()
    ring_bm(bm, 1.43, 1.5, 0.095, 0.075, 0.068, 0.06, 16, M)
    ring_bm(bm, 0.93, 0.99, 0.148, 0.108, 0.15, 0.11, 16, M)
    box_bm(bm, 0.06, 0.012, 0.07, seg=0, M=M @ TR((0.075, -0.112, 1.29)))
    lib.obj_from_bm(prefix + "orange", bm, mat("suit_orange"), COLL[0])
    # head + hair + ears, bowed a little forward around the neck
    Mh = M @ TR((0, 0, 1.56)) @ Matrix.Rotation(head_pitch, 4, "X") @ TR((0, 0.01, 0.13))
    build_head(face_name, face_mat, Mh)
    build_hair(prefix + "hair", Mh, seed)
    bm = bmesh.new()
    add_ears(bm, Mh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    lib.obj_from_bm(prefix + "ears", bm, mat("skin"), COLL[0])


def hand(R, Mh):
    """first-person right hand holding the phone: palm behind, thumb on the right edge, fingertips round the left"""
    V = [(0.035, 0.045, -0.125), (0.02, 0.027, -0.075), (0.0, 0.023, -0.035)]
    E = [(0, 1), (1, 2)]
    Rr = [0.025, (0.03, 0.02), (0.03, 0.018)]
    for z, r in ((0.016, 0.0105), (-0.008, 0.011), (-0.031, 0.0105), (-0.052, 0.0092)):
        b = len(V)
        V += [(-0.028, 0.02, z), (-0.046, 0.008, z - 0.002), (-0.043, -0.008, z - 0.006)]
        E += [(2, b), (b, b + 1), (b + 1, b + 2)]
        Rr += [r * 1.05, r * 0.85, r * 0.68]
    b = len(V)
    V += [(0.03, 0.022, -0.062), (0.049, 0.008, -0.036), (0.044, -0.01, -0.012)]
    E += [(1, b), (b, b + 1), (b + 1, b + 2)]
    Rr += [0.016, 0.0115, 0.0095]
    skin_obj("HAND_skin", V, E, Rr, "skin", Mh)
    skin_obj("HAND_sleeve", [(0.042, 0.075, -0.16), (0.075, 0.24, -0.44)], [(0, 1)], [0.043, 0.052], "suit", Mh, subsurf=1)
    bm = bmesh.new()
    box_bm(bm, 0.078, 0.012, 0.16, seg=0, M=Mh)
    lib.obj_from_bm("HAND_phone", bm, mat("rubber"), COLL[0])
    bm = bmesh.new()
    d = Vector((0.075, 0.24, -0.44)) - Vector((0.042, 0.075, -0.16))
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    ring_bm(bm, 0.0, 0.035, 0.047, 0.047, 0.047, 0.047, 12, Mh @ TR((0.042, 0.075, -0.16)) @ rot)
    lib.obj_from_bm("HAND_cuff", bm, mat("suit_orange"), COLL[0])
    R.screen("phone", 0.07, 0.15, tuple(Mh @ Vector((0, -0.0065, 0))), (0, 0, 0))
    R.anchor("PHONE_center", tuple(Mh @ Vector((0, 0, 0))))


COLL = [None]


def build(R):
    COLL[0] = R.coll
    person("STAND_", "FACE_stand", "face_open", TR((0, 0, 0)), head_pitch=0.14, seed=3)
    rotm = Matrix(((0, 0, 1), (-1, 0, 0), (0, -1, 0))).to_4x4()
    person("LIE_", "FACE_lie", "face_closed", TR((5, 0, 0.2)) @ rotm, head_pitch=0.0, seed=5)
    hand(R, TR((10, 0, 0.05)))
