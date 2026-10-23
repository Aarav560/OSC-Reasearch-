"""Python port of cubicmetre's OSC Mk.6 fire control (github.com/cubicmetre/osc-fire-control,
src/utils/calculations.ts, 'osc-mk6' variant) plus the physical panel mapping.

    python3 firecontrol.py <origin x y z> <target x y z> [--nuke N | --stab DEPTH] [--pass 940]

Panel mapping (OSC 6 Control Panel schematic): buttons on the x=9 wall, copper bulbs at x=7;
grid row r (0..4) sits at y = 5 + r, grid column c (0..12) at z = 20 - c.
"""
import argparse
import math

DV_PLUS_X = 8.755553287151535
DV_PLUS_Y = 8.816216069168268
DV_PLUS_Z = 8.755553287151535
DV_MINUS_X = -8.664591055789826
DV_MINUS_Z = -8.664591055789826
DV_YX = -0.596968396919667
DY_STAB = 106.92 + 44.4
DY_NUKE = 140
DX = 22.5000000095367
DZ = 0.9999999904633 - 1
SLOW_XZ = 0.900000035762786
SLOW_Y = 1.5


def bit(v, d):
    return int(math.floor(abs(v) / d)) % 2


def ibit(v, d):
    return 1 - bit(v, d)


def solve(origin, target, nuke=None, stab=50, passcode=940, slot=0):
    ox, oy, oz = origin
    tx, ty, tz = target
    dvx = DV_PLUS_X if tx > ox else DV_MINUS_X
    dvz = DV_PLUS_Z if tz > oz else DV_MINUS_Z
    dy = DY_NUKE if nuke is not None else DY_STAB
    ix, iy, iz = ox + DX + slot, oy + 2.1975, oz + DZ
    diff_y = max(50, (dy + ty) - iy)
    count_y = diff_y / (SLOW_Y * DV_PLUS_Y)
    cy = math.floor(count_y)
    fy = round((count_y - cy) * 10)
    diff_x = tx - (ix + (cy + fy / 10) * DV_YX)
    diff_z = tz - iz
    count_x = diff_x / (SLOW_XZ * dvx)
    count_z = diff_z / (SLOW_XZ * dvz)
    cx = math.floor(abs(count_x)); fx = round((abs(count_x) - cx) * 10)
    cz = math.floor(abs(count_z)); fz = round((abs(count_z) - cz) * 10)
    vx = dvx * (cx + fx / 10) + DV_YX * (cy + fy / 10)
    vy = DV_PLUS_Y * (cy + fy / 10)
    vz = dvz * (cz + fz / 10)
    exact = (ix + SLOW_XZ * vx, iy + SLOW_Y * vy, iz + SLOW_XZ * vz)
    size = nuke if nuke is not None else math.ceil(stab / (9 * 0.99))
    grid = [
        [bit(cz, 1), bit(cz, 32), bit(cz, 1024), ibit(fz, 8), ibit(fy, 8), bit(cy, 8), ibit(fx, 8),
         bit(cx, 8192), bit(cx, 256), bit(cx, 8), bit(size, 2), bit(passcode, 512), bit(passcode, 16)],
        [bit(cz, 2), bit(cz, 64), bit(cz, 2048), ibit(fz, 4), ibit(fy, 4), bit(cy, 4), ibit(fx, 4),
         bit(cx, 4096), bit(cx, 128), bit(cx, 4), bit(size, 4), bit(passcode, 256), bit(passcode, 8)],
        [bit(cz, 4), bit(cz, 128), bit(cz, 4096), ibit(fz, 2), ibit(fy, 2), bit(cy, 2), ibit(fx, 2),
         bit(cx, 2048), bit(cx, 64), bit(cx, 2), bit(size, 8), bit(passcode, 128), bit(passcode, 4)],
        [bit(cz, 8), bit(cz, 256), bit(cz, 8192), ibit(fz, 1), ibit(fy, 1), bit(cy, 1), ibit(fx, 1),
         bit(cx, 1024), bit(cx, 32), bit(cx, 1), bit(size, 16), bit(passcode, 64), bit(passcode, 2)],
        [bit(cz, 16), bit(cz, 512), bit(cz, 16384), 1 if diff_z < 0 else 0, bit(cy, 16),
         1 if diff_x < 0 else 0, bit(cx, 16384), bit(cx, 512), bit(cx, 16), bit(size, 1),
         1 if nuke is not None else 0, bit(passcode, 32), bit(passcode, 1)],
    ]
    return {"coarse": (cx, cy, cz), "fine": (fx, fy, fz), "initial": (ix, iy, iz),
            "motion": (vx, vy, vz), "exact": exact, "grid": grid,
            "nether": (math.floor(ox / 8), oy, math.floor(oz / 8))}


def panel_cells(grid):
    """(row, col, bit, y, z) for every cell of the 5x13 terminal."""
    for r, row in enumerate(grid):
        for c, b in enumerate(row):
            yield r, c, b, 5 + r, 20 - c


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("coords", nargs=6, type=float)
    ap.add_argument("--nuke", type=int)
    ap.add_argument("--stab", type=float, default=50)
    ap.add_argument("--pass", dest="passcode", type=int, default=940)
    a = ap.parse_args()
    s = solve(a.coords[:3], a.coords[3:], a.nuke, a.stab, a.passcode)
    for k, v in s.items():
        if k != "grid":
            print(f"{k:8s} {v}")
    print("terminal (top row = grid row 4):")
    for row in reversed(s["grid"]):
        print("   " + " ".join("#" if b else "." for b in row))
