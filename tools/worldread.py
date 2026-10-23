"""Read blocks and entities straight from a Minecraft (1.18+ / 26.x) world save.

    from worldread import World
    w = World("<server>/world")   # overworld; World(path, "dimensions/minecraft/the_nether")
    blocks = w.box((x0, y0, z0), (x1, y1, z1))  # {(x, y, z): "minecraft:name[props]"} without air
    ents = w.entities((x0, y0, z0), (x1, y1, z1))

Run `save-all flush` on the server first. Chunk sections store a block-state palette and a
long array with indices packed per long (no spanning since 1.16), bits = max(4, ceil(log2 n)).
"""
import io
import math
import os
import struct
import zlib

import nbtlib


def _state(entry):
    # 26.x palettes hold either a bare name (block default state, shown by nbtlib as {"": name})
    # or {id, properties}; older saves use {Name, Properties}
    if isinstance(entry, str):
        return entry
    if "" in entry:
        return str(entry[""])
    name = str(entry.get("id", entry.get("Name")))
    props = entry.get("properties", entry.get("Properties"))
    if props:
        name += "[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]"
    return name


class World:
    def __init__(self, path, dim="dimensions/minecraft/overworld"):
        self.path = path
        self.dim = dim
        self._chunks = {}

    def _region_file(self, kind, rx, rz):
        base = os.path.join(self.path, self.dim) if self.dim else self.path
        return os.path.join(base, kind, f"r.{rx}.{rz}.mca")

    def _read_chunk(self, kind, cx, cz):
        key = (kind, cx, cz)
        if key in self._chunks:
            return self._chunks[key]
        fn = self._region_file(kind, cx >> 5, cz >> 5)
        nbt = None
        if os.path.exists(fn):
            with open(fn, "rb") as f:
                f.seek(4 * ((cx & 31) + (cz & 31) * 32))
                loc = struct.unpack(">I", f.read(4))[0]
                off, cnt = loc >> 8, loc & 0xFF
                if off and cnt:
                    f.seek(off * 4096)
                    length, comp = struct.unpack(">IB", f.read(5))
                    raw = f.read(length - 1)
                    if comp == 2:
                        raw = zlib.decompress(raw)
                    elif comp == 1:
                        import gzip
                        raw = gzip.decompress(raw)
                    nbt = nbtlib.File.parse(io.BytesIO(raw))
        self._chunks[key] = nbt
        return nbt

    def section_blocks(self, cx, cz):
        """Yield (x, y, z, state) for every non-air block of chunk (cx, cz)."""
        ch = self._read_chunk("region", cx, cz)
        if ch is None:
            return
        for sec in ch.get("sections", []):
            bs = sec.get("block_states")
            if bs is None:
                continue
            pal = [_state(p) for p in bs["palette"]]
            sy = int(sec["Y"]) * 16
            if len(pal) == 1:
                if pal[0] in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air"):
                    continue
                for i in range(4096):
                    yield cx * 16 + (i & 15), sy + (i >> 8), cz * 16 + ((i >> 4) & 15), pal[0]
                continue
            bits = max(4, math.ceil(math.log2(len(pal))))
            per = 64 // bits
            mask = (1 << bits) - 1
            data = [int(v) & 0xFFFFFFFFFFFFFFFF for v in bs["data"]]
            for i in range(4096):
                v = (data[i // per] >> ((i % per) * bits)) & mask
                st = pal[v]
                if st.startswith(("minecraft:air", "minecraft:cave_air", "minecraft:void_air")):
                    continue
                yield cx * 16 + (i & 15), sy + (i >> 8), cz * 16 + ((i >> 4) & 15), st

    def box(self, a, b):
        (x0, y0, z0), (x1, y1, z1) = a, b
        out = {}
        for cx in range(x0 >> 4, (x1 >> 4) + 1):
            for cz in range(z0 >> 4, (z1 >> 4) + 1):
                for x, y, z, st in self.section_blocks(cx, cz):
                    if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1:
                        out[(x, y, z)] = st
        return out

    def entities(self, a, b):
        (x0, y0, z0), (x1, y1, z1) = a, b
        out = []
        for cx in range(x0 >> 4, (x1 >> 4) + 1):
            for cz in range(z0 >> 4, (z1 >> 4) + 1):
                ch = self._read_chunk("entities", cx, cz)
                if ch is None:
                    continue
                for e in ch.get("Entities", []):
                    p = tuple(float(v) for v in e["Pos"])
                    if x0 <= p[0] <= x1 + 1 and y0 <= p[1] <= y1 + 1 and z0 <= p[2] <= z1 + 1:
                        out.append((str(e["id"]), p, e))
        return out


if __name__ == "__main__":
    import collections
    import sys
    w = World(sys.argv[1])
    a = tuple(map(int, sys.argv[2:5]))
    b = tuple(map(int, sys.argv[5:8]))
    bl = w.box(a, b)
    print(len(bl), "blocks")
    for k, v in collections.Counter(s.split("[")[0] for s in bl.values()).most_common(15):
        print(f"{v:6d} {k}")
    for e in w.entities(a, b):
        print(e[0], e[1])
