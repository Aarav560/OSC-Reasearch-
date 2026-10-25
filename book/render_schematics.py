"""Render every schematic for the book: one isometric view and four orthographic elevations.

    python3 render_schematics.py <schematic dir> <assets dir> <blocks.json> <out dir> [view root]

Each .litematic under <schematic dir> is meshed with tools/mcmesh.py into <view root>/bk/<slug>/
and photographed with render/mcview.html (served from <view root> on port 8766) by
render/shoot.js. Writes <out dir>/<slug>-{iso,north,south,east,west}.png and catalog.json
(name, source, size, block counts). Zephyr designs are added from paper-tests/zephyr.py.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "paper-tests"))
import litematic             # noqa: E402
from mcmesh import Mesher    # noqa: E402

src, assets, report, out = sys.argv[1:5]
view = sys.argv[5] if len(sys.argv) > 5 else os.path.join(HERE, "..", "render", "..")
os.makedirs(out, exist_ok=True)
SKIP = ("no colors version", "Instruction Manual", "Smart_Arty_Envelope")   # duplicates / not builds
MAX_BLOCKS = 60000


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def zephyr_designs():
    # layouts only (no server needed): import the module without connecting
    os.environ.setdefault("RCON_LAZY", "1")
    src_txt = open(os.path.join(HERE, "..", "paper-tests", "zephyr.py")).read()
    ns = {}
    code = src_txt.replace("r = Rcon()", "r = None")
    exec(compile(code, "zephyr.py", "exec"), ns)
    out_ = {}
    for name, fn in [("Zephyr Mk1-A", "auto_layout"), ("Zephyr Mk2", "mk2_layout"), ("Zephyr Mk3 Drill", "mk3_layout")]:
        out_[name] = {(x, y, z): "minecraft:" + b for x, y, z, b in ns[fn]()}
    return out_


items = []
for root, _, files in os.walk(src):
    for f in sorted(files):
        if f.endswith(".litematic") and not any(k in f for k in SKIP):
            items.append((os.path.join(root, f), os.path.relpath(os.path.join(root, f), src)))
m = Mesher(assets, report)
catalog = []
jobs = []
for name, blocks in list(zephyr_designs().items()) + [(None, p) for p in items]:
    if name is None:
        path, rel = blocks
        sch = litematic.load(path)
        blocks = {k: v for k, v in sch.blocks.items() if "air" not in v.split("[")[0]}
        name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").replace(" --- White Mc", "")
        creator = rel.split("/")[0]
    else:
        rel, creator = "paper-tests/zephyr.py", "this book"
    if not blocks:
        continue
    xs, ys, zs = zip(*blocks)
    lo = (min(xs), min(ys), min(zs)); hi = (max(xs), max(ys), max(zs))
    blocks = {(x - lo[0], y - lo[1], z - lo[2]): v for (x, y, z), v in blocks.items()}
    size = [hi[i] - lo[i] + 1 for i in range(3)]
    counts = {}
    for v in blocks.values():
        n = v.split("[")[0].replace("minecraft:", "")
        counts[n] = counts.get(n, 0) + 1
    sl = slug(name)
    entry = {"slug": sl, "name": name, "creator": creator, "source": rel, "size": size,
             "blocks": len(blocks), "counts": dict(sorted(counts.items(), key=lambda kv: -kv[1]))}
    catalog.append(entry)
    with open(os.path.join(out, sl + ".blocks.json"), "w") as fh:
        json.dump([[x, y, z, v] for (x, y, z), v in blocks.items()], fh)
    if len(blocks) > MAX_BLOCKS:
        print("skip render (too big)", name, len(blocks))
        continue
    scene = os.path.join(view, "bk", sl)
    m.write(m.mesh(blocks), scene)
    cx, cy, cz = size[0] / 2, size[1] / 2, size[2] / 2
    R = max(size) * 1.25 + 4
    span = max(size)
    z_iso = 1000 / (span * 1.55 + 4)
    shots = [
        {"mode": "ortho", "pos": [cx + R, cy + R * .82, cz + R], "look": [cx, cy, cz], "zoom": z_iso},
        {"mode": "ortho", "pos": [cx, cy, cz - R * 3], "look": [cx, cy, cz], "zoom": 1000 / (max(size[0], size[1]) * 1.15 + 2)},
        {"mode": "ortho", "pos": [cx, cy, cz + R * 3], "look": [cx, cy, cz], "zoom": 1000 / (max(size[0], size[1]) * 1.15 + 2)},
        {"mode": "ortho", "pos": [cx + R * 3, cy, cz], "look": [cx, cy, cz], "zoom": 1000 / (max(size[2], size[1]) * 1.15 + 2)},
        {"mode": "ortho", "pos": [cx - R * 3, cy, cz], "look": [cx, cy, cz], "zoom": 1000 / (max(size[2], size[1]) * 1.15 + 2)},
    ]
    jobs.append((sl, shots))
    print("meshed", name, size, len(blocks))
json.dump(catalog, open(os.path.join(out, "catalog.json"), "w"), indent=1)
json.dump([{"scene": "bk/" + sl, "out": os.path.abspath(os.path.join(out, sl + ".png")), "shots": sh} for sl, sh in jobs],
          open(os.path.join(out, "jobs.json"), "w"))
subprocess.run(["node", os.path.join(HERE, "shoot.js"), os.path.join(out, "jobs.json")], check=True,
               env=dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()))
for sl, _ in jobs:
    for i, side in enumerate(["iso", "north", "south", "east", "west"]):
        a = os.path.join(out, f"{sl}-{i}.png")
        if os.path.exists(a):
            os.replace(a, os.path.join(out, f"{sl}-{side}.png"))
print(len(catalog), "designs,", len(jobs), "rendered")
