"""Painted head textures for the crew man (python blender/faces.py).

One 512x512 wrap-around texture per state (face_closed / face_open), laid out by headparam:
tired semi-realistic face, heavy lids, bags under the eyes, stubble, dark messy hair at the back.
Everything is computed per pixel in face-plane metres so it sits on the sculpted bumps.
"""
import math
import numpy as np
from textures import rng, fbm, hexc, save
import headparam as HP

N = 512


def coords():
    v = 1.0 - (np.arange(N) + 0.5) / N           # image row -> v (top row = top of head)
    u = (np.arange(N) + 0.5) / N
    t = u - 0.5
    a = np.sign(t) * math.pi * (np.abs(t) / 0.5) ** (1.0 / HP.P)
    nz = 2 * v - 1
    A, NZ = np.meshgrid(a, nz)
    cl = np.sqrt(np.clip(1 - NZ ** 2, 0, 1))
    nx = np.sin(A) * cl
    f = np.cos(A) * cl                          # 1 = facing front
    return A, NZ, HP.AX * nx, HP.AZ * NZ, f


def gauss(X, Z, cx, cz, sx, sz):
    return np.exp(-(((X - cx) / sx) ** 2 + ((Z - cz) / sz) ** 2))


def mulc(img, m, col):
    """blend towards colour col by mask m"""
    img[:] = img * (1 - m[..., None]) + hexc(col) * m[..., None]


def shade(img, m, k):
    img[:] = img * (1 - m[..., None] * (1 - np.asarray(k, dtype=float)))


def seg_dist(X, Z, p, q):
    px, pz = p; qx, qz = q
    dx, dz = qx - px, qz - pz
    t = np.clip(((X - px) * dx + (Z - pz) * dz) / (dx * dx + dz * dz), 0, 1)
    return np.hypot(X - (px + t * dx), Z - (pz + t * dz))


def paint(open_eyes):
    r = rng(91)
    A, NZ, X, Z, f = coords()
    front = np.clip(f, 0, 1)
    n1 = fbm(N, N, r, (64, 32, 16, 8))
    n2 = r.random((N, N))

    # ---- skin: sallow, warm in the middle, cooler and darker towards the sides and under the jaw
    img = np.zeros((N, N, 3)) + hexc("#b8907a")
    img *= (0.94 + 0.12 * n1)[..., None]
    img *= (0.62 + 0.38 * front ** 0.6)[..., None]
    shade(img, np.clip((-Z - 0.085) / 0.03, 0, 1) * (front > 0.2), 0.55)       # under-chin shadow
    mulc(img, 0.22 * gauss(X, Z, 0, HP.NOSE_TIP_Z, 0.008, 0.008), "#c46a5a")    # red nose tip
    for s in (-1, 1):
        mulc(img, 0.16 * gauss(X, Z, s * 0.045, -0.02, 0.014, 0.012), "#b8665a")  # blotchy cheeks
        shade(img, 0.30 * gauss(X, Z, s * 0.046, -0.045, 0.012, 0.016), 0.72)    # hollow under the cheekbone
        shade(img, 0.35 * gauss(X, Z, s * 0.062, 0.03, 0.012, 0.03), 0.8)        # temples
    # forehead light, painted key from above-left (the PS1 way: light lives in the texture)
    img *= (1 + 0.08 * gauss(X, Z, -0.012, 0.045, 0.03, 0.02))[..., None]

    # ---- sockets, bags, brows
    for s in (-1, 1):
        cx = s * HP.EYE_X
        shade(img, 0.55 * gauss(X, Z, cx, HP.EYE_Z + 0.002, 0.017, 0.010), 0.62)  # deep socket
        shade(img, 0.55 * gauss(X, Z, cx + s * 0.001, HP.EYE_Z - 0.0105, 0.013, 0.0035), 0.70)  # bag
        mulc(img, 0.30 * gauss(X, Z, cx, HP.EYE_Z - 0.010, 0.013, 0.004), "#7a4c58")  # bruised tint
        shade(img, 0.22 * gauss(X, Z, cx, HP.EYE_Z - 0.0155, 0.014, 0.0012), 0.7)  # lower bag crease
        # brow: thick, inner end lower (worried), strands from noise
        ex = (X - cx) / 0.015
        bz = HP.BROW_Z + 0.0035 * (1 - ex ** 2) - 0.0025 * (s * ex < 0) * np.abs(ex) * 0.0  # arch
        bz = bz - 0.003 * np.clip(-s * ex, 0, 1)                                     # inner end down
        thick = 0.0028 * (1 - 0.5 * np.clip(s * ex, 0, 1))
        brow = (np.abs(Z - bz) < thick) & (np.abs(ex) < 1.05) & (front > 0.3)
        brow &= n2 > 0.12
        shade(img, ((np.abs(Z - (bz - thick - 0.0018)) < 0.0018) & (np.abs(ex) < 1)) * 1.0, 0.75)  # shadow under the brow
        mulc(img, brow * 1.0, "#2a1d17")

        # ---- the eye itself
        ex = (X - cx) / 0.0125
        ez = (Z - (HP.EYE_Z - 0.0012 * s * ex)) / 0.0058   # outer corner droops a bit
        w = np.clip(1 - ex ** 2, 0, 1)
        up, lo = 0.62, 0.78                                  # heavy upper lid
        inside = (ez < up * w) & (ez > -lo * w) & (np.abs(ex) < 1) & (front > 0.3)
        crease = (np.abs(ez - (up * w + 0.75)) < 0.17) & (np.abs(ex) < 0.95) & (front > 0.3)
        shade(img, crease * 1.0, 0.8)
        if open_eyes:
            mulc(img, inside * 1.0, "#c9bba7")
            shade(img, inside * np.clip((ez - 0.1) / 0.6, 0, 1), 0.65)              # lid shadow on the white
            mulc(img, inside * gauss(X, Z, cx + s * 0.009, HP.EYE_Z, 0.003, 0.004) * 0.5, "#c98a80")  # bloodshot corner
            ir = np.hypot(X - cx, (Z - HP.EYE_Z + 0.0004) * 1.0)
            iris = inside & (ir < 0.0049)
            mulc(img, iris * 1.0, "#4a3426")
            mulc(img, (inside & (ir < 0.0049) & (ir > 0.0036)) * 1.0, "#2a1c14")
            mulc(img, (inside & (ir < 0.0021)) * 1.0, "#0a0706")
            hl = (np.abs(X - (cx - 0.0016)) < 0.0007) & (np.abs(Z - (HP.EYE_Z + 0.0013)) < 0.0007)
            mulc(img, (hl & inside) * 1.0, "#efe6d6")
            lash = (ez >= up * w) & (ez < up * w + 0.36) & (np.abs(ex) < 1.08) & (front > 0.3)
            mulc(img, lash * 1.0, "#160d0a")
            low = (ez <= -lo * w) & (ez > -lo * w - 0.2) & (np.abs(ex) < 1.0) & (front > 0.3)
            mulc(img, low * 0.8, "#5a3428")
        else:
            lid = inside
            mulc(img, lid * 0.65, "#a87a66")
            shade(img, lid * np.clip((up * w - ez) / 1.0, 0, 1) * 0.6, 0.8)
            lash = (np.abs(ez - (-0.28 * w)) < 0.2) & (np.abs(ex) < 1.05) & (front > 0.3)
            mulc(img, lash * 1.0, "#1a100c")
            mulc(img, ((np.abs(ez - (-0.28 * w) + 0.25) < 0.1) & (np.abs(ex) < 0.9)) * 0.5, "#6a4034")

    # ---- nose
    for s in (-1, 1):
        shade(img, gauss(X, Z, s * 0.0085, -0.012, 0.0035, 0.012) * 0.5, 0.75)   # bridge sides
        wing = seg_dist(X, Z, (s * 0.0105, -0.024), (s * 0.0075, -0.033)) < 0.0012
        shade(img, wing * 0.8, 0.6)
        nos = (((X - s * 0.0052) / 0.0029) ** 2 + ((Z - HP.NOSTRIL_Z) / 0.0015) ** 2) < 1
        mulc(img, nos * 1.0, "#3a1e18")
        # nasolabial fold, mouth corners
        fold = seg_dist(X, Z, (s * 0.0125, -0.031), (s * 0.026, -0.062)) < 0.0011
        shade(img, fold * 0.8, 0.72)
        shade(img, (seg_dist(X, Z, (s * 0.0125, -0.031), (s * 0.026, -0.062)) < 0.0035) * 0.25, 0.85)
    mulc(img, gauss(X, Z, -0.0012, NOSE_HL := HP.NOSE_TIP_Z + 0.004, 0.0022, 0.003) * 0.35, "#e2b8a0")
    shade(img, gauss(X, Z, 0, HP.NOSTRIL_Z - 0.004, 0.009, 0.0025) * 0.7, 0.65)  # under the nose
    shade(img, gauss(X, Z, 0, (HP.NOSTRIL_Z + HP.MOUTH_Z) / 2, 0.0025, 0.008) * 0.35, 0.82)  # philtrum

    # ---- mouth: thin, corners turned down
    lx = np.abs(X) / 0.021
    lz = HP.MOUTH_Z - 0.0032 * lx ** 2
    m_in = lx < 1
    upper = m_in & (Z > lz) & (Z < lz + 0.0042 * (1 - lx ** 2) + 0.0006)
    lower = m_in & (Z < lz) & (Z > lz - 0.0055 * (1 - lx ** 2))
    mulc(img, upper * 0.75, "#8a4a40")
    mulc(img, lower * 0.5, "#a45e52")
    mulc(img, (m_in & (np.abs(Z - lz) < 0.0011)) * 1.0, "#3a1a16")
    shade(img, ((np.abs(Z - (lz - 0.0075)) < 0.0018) & (lx < 0.7)) * 0.7, 0.72)   # under the lower lip
    shade(img, (np.abs(Z - (HP.CHIN_Z + 0.022)) < 0.004) * (np.abs(X) < 0.012) * 0.25, 0.85)  # chin dimple

    # ---- stubble on jaw, chin and upper lip
    dens = np.clip((-Z - 0.034) / 0.02, 0, 1) * np.clip((front - 0.05) / 0.3, 0, 1)
    dens = np.maximum(dens, np.clip((-Z - 0.036) / 0.01, 0, 1) * gauss(X, Z, 0, -0.045, 0.02, 0.008) * 0.8)
    dens = dens * (1 - (upper | lower)) * (0.7 + 0.6 * n1)
    st = n2 > 1 - 0.38 * dens
    shade(img, st * 0.5, 0.72)
    mulc(img, dens * 0.12, "#5a5458")

    # ---- ear zone (the ear mesh sits here; paint its shadow)
    for s in (-1, 1):
        shade(img, np.exp(-(((A - s * math.pi / 2) / 0.16) ** 2 + ((Z + 0.008) / 0.02) ** 2)) * 0.6, 0.6)

    # ---- hair: dark, greasy, ragged hairline
    jag = 0.006 * np.sin(A * 23 + 1.3) + 0.004 * np.sin(A * 57) + 0.004 * (n1 - 0.5)
    absa = np.abs(A)
    hl = np.where(absa < 0.9, 0.052 + 0.01 * (absa / 0.9) ** 2,
                  np.where(absa < 1.75, 0.062 - 0.05 * (absa - 0.9) / 0.85, 0.012 - 0.085 * np.clip((absa - 1.75) / 1.2, 0, 1)))
    hl = hl + jag
    sideburn = (absa > 1.2) & (absa < 1.45) & (Z > -0.02)
    hair = (Z > hl) | sideburn
    strands = 0.5 + 0.5 * np.sin(A * 140 + n1 * 9)
    hcol = np.zeros_like(img) + hexc("#1d1612")
    hcol *= (0.75 + 0.5 * strands * (0.6 + 0.4 * n2))[..., None]
    hcol += hexc("#3a2a20") * (0.25 * (strands > 0.92))[..., None]
    img[hair] = hcol[hair]
    shade(img, ((~hair) & (Z > hl - 0.006) & (Z < hl)) * 1.0, 0.6)    # hairline shadow on the forehead

    # ---- grime, pores, final crunch
    shade(img, (n2 > 0.985) * 1.0, 0.85)
    return img


if __name__ == "__main__":
    save("face_closed", paint(False), lv=40)
    save("face_open", paint(True), lv=40)
    print("ok")
