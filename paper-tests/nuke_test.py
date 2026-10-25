"""Ring-nuke physics test (no cannon): how far an expansion charge throws a ring of TNT.

    python3 nuke_test.py <x> <z> <height y> <ring TNT> <expansion TNT> [offset] [mode] [ring dy]

Expansion modes: same = all fuse 1 at the exact centre; seq = fuses 1, 2, 3, ... (one per
tick); spread = all fuse 1, each 0.001 from the centre in a random direction; pre<n> = n of
them with fuse 1, the rest fuse 2 (cubicmetre's "9 TNT one tick before expansion"); pairs =
two per tick, the second 0.0625 above the first (its blast centre), so it is not pushed.

Summons <ring TNT> TNT (fuse 80) at random directions <offset> blocks from a centre point,
plus <expansion TNT> TNT (fuse 1) exactly at the centre, all motionless, then steps tick by
tick and records each ring TNT's position on its last tick (where it detonates). The area
around the centre is force-loaded. Writes nuke-<ring>x<exp>.json and prints the radii.
"""
import json
import math
import random
import re
import sys
import time

import zephyr as Z

r = Z.r
cx, cz, cy, N, K = (int(v) for v in sys.argv[1:6])
# offset: one value, or a comma list of ring-group offsets (N TNT per group, evenly spaced)
# each group may carry its own fuse as offset:fuse (a short-fuse group is a booster ring)
specs = [v.split(":") for v in (sys.argv[6] if len(sys.argv) > 6 else "0.01").split(",")]
offs = [float(v[0]) for v in specs]
gfuse = [int(v[1]) if len(v) > 1 else 80 for v in specs]
off = offs[0]
mode = sys.argv[7] if len(sys.argv) > 7 else "same"
dv = float(sys.argv[8]) if len(sys.argv) > 8 else 0.0      # ring height relative to the centre
R = int(sys.argv[9]) if len(sys.argv) > 9 else 224
r.cmd("tick unfreeze")
for x in range(cx - R, cx + R + 1, 16 * 15):
    for z in range(cz - R, cz + R + 1, 16 * 15):
        r.cmd(f"forceload add {x} {z} {min(x + 16 * 15 - 1, cx + R)} {min(z + 16 * 15 - 1, cz + R)}")
time.sleep(8)
r.cmd("kill @e[type=tnt]")
r.cmd("tick freeze")
rng = random.Random(N * 100 + K)
for g, o in enumerate(offs):
    for i in range(N):
        a = 2 * math.pi * (i + 0.5 * g) / N          # evenly spaced, groups staggered
        r.cmd(f"summon tnt {cx + 0.5 + o * math.cos(a)} {cy + dv} {cz + 0.5 + o * math.sin(a)} "
              f"{{fuse:{gfuse[g]},Motion:[0d,0d,0d],Tags:[\"{'ring' if gfuse[g] == 80 else 'boost'}\",\"g{g}\"]}}")
for i in range(K):
    if mode == "seq":
        fuse = i + 1
    elif mode == "pairs":                 # two per tick, the second at the first's blast centre
        fuse = i // 2 + 1
    elif mode.startswith("pre"):          # pre<n>: n TNT go off one tick before the rest
        fuse = 1 if i < int(mode[3:]) else 2
    else:
        fuse = 1
    a = rng.uniform(0, 2 * math.pi)
    ex, ez = (0.001 * math.cos(a), 0.001 * math.sin(a)) if mode == "spread" else (0, 0)
    # an explosion is centred 0.0625 above its TNT: sink the expansion charge by that much so
    # its blast is level with the ring and pushes it outward, not down
    ey = 0.0625 if (mode == "pairs" and i % 2) else 0.0
    r.cmd(f"summon tnt {cx + 0.5 + ex} {cy - 0.0625 + ey} {cz + 0.5 + ez} {{fuse:{fuse},Motion:[0d,0d,0d],Tags:[\"exp\"]}}")
last = {}
for t in range(82):
    r.step(1)
    o = r.cmd("execute as @e[type=tnt,tag=ring] run data get entity @s Pos")
    ps = re.findall(r"\[(-?[\d.E-]+)d, (-?[\d.E-]+)d, (-?[\d.E-]+)d\]", o)
    if not ps:
        break
    last = {"t": t + 1, "pos": [[float(a), float(b), float(c)] for a, b, c in ps]}
radii = sorted(math.hypot(p[0] - cx - 0.5, p[2] - cz - 0.5) for p in last["pos"])
groups = sorted(set(round(v) for v in radii))
ys = [p[1] for p in last["pos"]]
print(f"ring {N} exp {K} {mode} dy {dv:+g}: detonate t={last['t']} radius min {radii[0]:.1f} median {radii[len(radii)//2]:.1f} "
      f"max {radii[-1]:.1f}  y {min(ys):.1f}..{max(ys):.1f}  ring radii {groups}")
json.dump({"centre": [cx, cy, cz], "ring": N, "exp": K, "mode": mode, "offset": off, "last": last, "radii": radii},
          open(f"nuke-{N}x{K}-{mode}{dv:+g}.json", "w"))
r.cmd("tick unfreeze")
