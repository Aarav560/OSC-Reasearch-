"""Build the meshes for livefire.html from the saved Paper world and the live-fire record.

    python3 build_livefire_scene.py <world dir> <assets dir> <blocks.json> <livefire json> <out dir>

Writes three scenes under <out dir> (coordinates relative to the payload cell S):
  base/     the Mk1-A cannon as built in the world, plus the superflat ground around the range
  before/   the target block as placed before the shot
  after/    the target block read back from the world after the shot (with the crater)
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from mcmesh import Mesher      # noqa: E402
from worldread import World    # noqa: E402

world_dir, assets, report, rec_path, out = sys.argv[1:6]
rec = json.load(open(rec_path))
sx, sy, sz = rec["S"]
tx, ty, tz = rec["target"]          # ty = first air above the target block
GROUND = -61
W = World(world_dir)


def rel(blocks):
    return {(x - sx, y - sy, z - sz): b for (x, y, z), b in blocks.items()}


cannon = rel(W.box((sx - 14, sy - 3, sz - 7), (sx + 3, sy + 3, sz + 8)))
cannon = {p: b for p, b in cannon.items() if "tnt" not in b}
base = dict(cannon)
for x in range(sx - 14, tx + 16):
    for z in range(sz - 10, tz + 16):
        if abs(x - tx) <= 10 and abs(z - tz) <= 10:
            continue
        base[(x - sx, GROUND - sy, z - sz)] = "minecraft:grass_block[snowy=false]"

before = {}
for x in range(tx - 10, tx + 11):
    for z in range(tz - 10, tz + 11):
        before[(x - sx, GROUND - sy, z - sz)] = "minecraft:grass_block[snowy=false]"
        for y in range(GROUND + 1, ty):
            before[(x - sx, y - sy, z - sz)] = "minecraft:stone"
for rad, col in [(9, "white"), (7, "red"), (5, "white"), (3, "red"), (1, "white")]:
    for x in range(tx - rad, tx + rad + 1):
        for z in range(tz - rad, tz + rad + 1):
            before[(x - sx, ty - 1 - sy, z - sz)] = f"minecraft:{col}_concrete"

after = rel(W.box((tx - 10, GROUND, tz - 10), (tx + 10, ty - 1, tz + 10)))

m = Mesher(assets, report)
for name, blocks in [("base", base), ("before", before), ("after", after)]:
    meta = m.write(m.mesh(blocks), os.path.join(out, name))
    print(name, len(blocks), "blocks", {k: v["vertices"] for k, v in meta["layers"].items()})
