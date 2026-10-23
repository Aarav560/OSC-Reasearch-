"""Quantitative OSC experiments on Paper (run after osc_tests.py; reuses its helpers).

Writes one JSON with every series so the book's charts can be regenerated:
  python3 osc_lab.py lab-results.json
Assumes spigot max-tnt-per-tick is raised (see config-snapshot/), so every
propellant TNT explodes on the tick it is meant to.
"""
import json
import sys
import time

import osc_tests as T

r = T.r
OUT = {}


def knockback_sweep():
    """Knockback received by a lazy payload vs. distance to one propellant TNT."""
    T.reset()
    c = T.CX + 300
    T.forceload(c, 0)
    px = T.bx(c + 1, 0.5)
    rows = []
    for d10 in range(5, 90, 5):
        d = d10 / 10
        r.cmd("kill @e[type=tnt]")
        T.tnt(px, 100.0, 8.5, fuse=200, tag="payload")
        T.tnt(px - d, 100.0, 8.5, fuse=1)
        T.r.step(2)
        m = r.vec("@e[tag=payload,limit=1]", "Motion")
        rows.append({"distance": d, "motion_x": m[0] if m else None, "motion_y": m[1] if m else None})
    OUT["knockback_vs_distance"] = rows


def linearity():
    """Displacement after one released tick vs. number of propellant TNT."""
    rows = []
    for i, n in enumerate([1, 5, 10, 25, 50, 100, 200, 400, 800]):
        T.reset()
        c = T.CX + 340 + i * 40
        px = T.lazy_launch(c, n, payload_fuse=400, y=200.0)
        m = r.vec("@e[tag=payload,limit=1]", "Motion")
        rows.append({"tnt": n, "motion_x": m[0], "motion_y": m[1], "per_tnt": m[0] / n})
    OUT["linearity"] = rows


def two_axis(n_x, n_z, c):
    """Payload 0.5 into the lazy corner chunk (c+1, 1); propellant west (chunk c,1) and north (chunk c+1,0)."""
    T.reset()
    r.cmd(f"forceload add {c*16} 16 {c*16+15} 31")      # west neighbour, entity-ticking
    r.cmd(f"forceload add {(c+1)*16} 0 {(c+1)*16+15} 15")  # north neighbour, entity-ticking
    T.wait_loaded(c * 16 + 8, 100, 24)
    T.wait_loaded((c + 1) * 16 + 8, 100, 8)
    r.step(2)
    time.sleep(0.5)
    px, py, pz = T.bx(c + 1, 0.5), 200.0, 16.5
    T.tnt(px, py, pz, fuse=400, tag="payload")
    for n, (x, z) in [(n_x, (px - 1, pz)), (n_z, (px, pz - 1))]:
        left = n
        while left > 0:
            k = min(100, left)
            for _ in range(k):
                r.cmd(f"summon tnt {x} {py} {z} {{fuse:1,NoGravity:1b}}")
            r.step(1)
            left -= k
    r.step(1)
    m = r.vec("@e[tag=payload,limit=1]", "Motion")
    return (px, pz), m


def calibration():
    """Recreate the spreadsheet method: fire each axis alone, build the 2x2 matrix, predict a mixed shot."""
    c = T.CX + 800
    _, mx = two_axis(200, 0, c)
    _, mz = two_axis(0, 200, c + 10)
    # columns = displacement per TNT for each axis
    M = [[mx[0] / 200, mz[0] / 200], [mx[2] / 200, mz[2] / 200]]
    target = (150.0, 90.0)  # wanted (dx, dz) on the first tick
    det = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    nx = (target[0] * M[1][1] - target[1] * M[0][1]) / det
    nz = (-target[0] * M[1][0] + target[1] * M[0][0]) / det
    nx_i, nz_i = round(nx), round(nz)
    _, mm = two_axis(nx_i, nz_i, c + 20)
    OUT["calibration"] = {
        "single_axis_motion": {"x_only_200": mx, "z_only_200": mz},
        "matrix_blocks_per_tnt": M,
        "target_first_tick_displacement": target,
        "solved_tnt": {"x": nx, "z": nz, "rounded": [nx_i, nz_i]},
        "fired_motion": mm,
        "error_blocks": [mm[0] - target[0], mm[2] - target[1]],
    }


def free_flight():
    """Trajectory of a lit TNT with an initial kick: checks gravity -0.04 and drag 0.98 per tick."""
    T.reset()
    c = T.CX + 900
    T.forceload(c - 1, -1, c + 3, 1)
    T.tnt(T.bx(c, 0.5), 250.0, 8.5, fuse=79, motion=(1.0, 0.5, 0.0), nograv=False)
    rows = []
    for t in range(1, 41):
        r.step(1)
        p = r.vec("@e[type=tnt,limit=1]", "Pos")
        m = r.vec("@e[type=tnt,limit=1]", "Motion")
        rows.append({"tick": t, "pos": p, "motion": m})
    OUT["free_flight"] = rows


def range_cost():
    """Server tick cost of the release tick vs. flight length."""
    rows = []
    for i, n in enumerate([100, 1000, 3000, 6000]):
        T.reset()
        c = T.CX + 1000 + i * 600
        px = T.lazy_launch(c, n, payload_fuse=400, y=300.0)
        m = r.vec("@e[tag=payload,limit=1]", "Motion")
        T.release(c)
        time.sleep(6)  # let /mspt's 5 s window forget the acceleration ticks
        r.step(1)
        time.sleep(0.5)
        rows.append({"tnt": n, "flight_blocks": m[0], "mspt": " ".join(r.cmd("mspt").split())})
    OUT["range_cost"] = rows


if __name__ == "__main__":
    for f in [knockback_sweep, linearity, calibration, free_flight, range_cost]:
        try:
            f()
            print("done", f.__name__, flush=True)
        except Exception as e:
            OUT[f.__name__] = {"error": repr(e)}
            print("FAIL", f.__name__, repr(e), flush=True)
    T.reset()
    r.cmd("tick unfreeze")
    with open(sys.argv[1] if len(sys.argv) > 1 else "lab-results.json", "w") as fh:
        json.dump(OUT, fh, indent=2)
