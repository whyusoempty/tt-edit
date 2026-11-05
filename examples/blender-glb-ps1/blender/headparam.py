"""Shared head parameterisation for the mesh (characters.py, Blender) and the painted face (faces.py, plain Python).

A head point is given by (a, nz): a = angle around the vertical axis (0 = front, which is -Y),
nz = sin(latitude). Texture: u = g(a) packs much more of the 512 px atlas into the front of the face,
v = (nz + 1) / 2 (image top = top of the head).  Physical face-plane coordinates are
X = AX * nx, Z = AZ * nz in metres, so features drawn here land on the bumps sculpted there.
"""
import math

AX, AY, AZ = 0.075, 0.095, 0.115   # head half width / half depth / half height (m)
P = 0.6                             # u packing exponent (<1 = more texels in front)

# face layout in metres (face plane, origin = head centre)
EYE_X, EYE_Z = 0.031, 0.004
BROW_Z = 0.021
NOSE_TIP_Z = -0.028
NOSTRIL_Z = -0.034
MOUTH_Z = -0.058
CHIN_Z = -0.104


def g(a):
    """angle (-pi..pi) -> u (0..1)"""
    s = 1.0 if a >= 0 else -1.0
    return 0.5 + 0.5 * s * (abs(a) / math.pi) ** P


def ginv(u):
    t = u - 0.5
    s = 1.0 if t >= 0 else -1.0
    return s * math.pi * (abs(t) / 0.5) ** (1.0 / P)
