"""Read Litematica .litematic schematics into plain block / tile-entity / entity lists.

    from litematic import load
    sch = load("cannon.litematic")
    for (x, y, z), state in sch.blocks.items(): ...        # placement-relative coords
    sch.tiles[(x, y, z)] -> nbtlib Compound (without x/y/z/id)
    sch.entities -> list of (pos tuple, nbtlib Compound)

Coordinates are relative to the schematic placement origin, i.e. region Position plus the
index inside the region, with negative region sizes handled the way Litematica does.
"""
import math

import nbtlib


def _state_string(entry):
    name = str(entry["Name"])
    props = entry.get("Properties")
    if props:
        name += "[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]"
    return name


def _unpack(longs, bits, count):
    """Litematica packs indices tightly across long boundaries (no padding)."""
    mask = (1 << bits) - 1
    vals = [int(v) & 0xFFFFFFFFFFFFFFFF for v in longs]
    out = []
    for i in range(count):
        start = i * bits
        li, off = divmod(start, 64)
        v = vals[li] >> off
        if off + bits > 64:
            v |= vals[li + 1] << (64 - off)
        out.append(v & mask)
    return out


class Schematic:
    def __init__(self, name, regions, blocks, tiles, entities, data_version):
        self.name, self.regions, self.blocks = name, regions, blocks
        self.tiles, self.entities, self.data_version = tiles, entities, data_version

    def bounds(self):
        xs, ys, zs = zip(*self.blocks)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def load(path, keep_air=False):
    root = nbtlib.load(path)
    blocks, tiles, entities, regions = {}, {}, [], {}
    for rname, r in root["Regions"].items():
        pos = {k: int(v) for k, v in r["Position"].items()}
        size = {k: int(v) for k, v in r["Size"].items()}
        # a negative size extends towards -axis from Position
        mins = {a: pos[a] + (size[a] + 1 if size[a] < 0 else 0) for a in "xyz"}
        sx, sy, sz = (abs(size[a]) for a in "xyz")
        palette = [_state_string(e) for e in r["BlockStatePalette"]]
        bits = max(2, math.ceil(math.log2(len(palette))))
        idx = _unpack(r["BlockStates"], bits, sx * sy * sz)
        regions[rname] = {"min": (mins["x"], mins["y"], mins["z"]), "size": (sx, sy, sz)}
        for i, p in enumerate(idx):
            st = palette[p]
            if not keep_air and st == "minecraft:air":
                continue
            x = i % sx
            z = (i // sx) % sz
            y = i // (sx * sz)
            blocks[(mins["x"] + x, mins["y"] + y, mins["z"] + z)] = st
        for te in r.get("TileEntities", []):
            p = (mins["x"] + int(te["x"]), mins["y"] + int(te["y"]), mins["z"] + int(te["z"]))
            t = nbtlib.Compound({k: v for k, v in te.items() if k not in ("x", "y", "z", "id")})
            tiles[p] = t
        for en in r.get("Entities", []):
            ep = en["Pos"]
            # entity positions are relative to the region's Position corner (not its minimum),
            # which differs from the block origin when a region has a negative size
            p = (pos["x"] + float(ep[0]), pos["y"] + float(ep[1]), pos["z"] + float(ep[2]))
            e = nbtlib.Compound({k: v for k, v in en.items() if k not in ("Pos", "UUID")})
            entities.append((p, e))
    return Schematic(str(root["Metadata"]["Name"]), regions, blocks, tiles, entities,
                     int(root.get("MinecraftDataVersion", 0)))


if __name__ == "__main__":
    import collections
    import sys
    s = load(sys.argv[1])
    print(s.name, "data", s.data_version, "blocks", len(s.blocks), "tiles", len(s.tiles),
          "entities", len(s.entities), "bounds", s.bounds())
    c = collections.Counter(b.split("[")[0] for b in s.blocks.values())
    for k, v in c.most_common():
        print(f"{v:6d}  {k}")
    for p, e in s.entities:
        print("entity", str(e.get("id")), tuple(round(v, 4) for v in p))
