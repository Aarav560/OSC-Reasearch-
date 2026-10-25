"""Layer-by-layer blueprint plans for the book.

    python3 blueprints.py <art dir> <assets dir>

Reads <art dir>/<slug>.blocks.json (written by render_schematics.py) and draws one PNG per
non-empty layer into <art dir>/layers/<slug>/y<NN>.png: navy blueprint ground, a block grid,
each block in the average colour of its texture, arrows on directional parts (signal flow for
repeaters and comparators, facing for pistons, dispensers, droppers and observers), dots for dust.
Also writes <art dir>/layers/<slug>/layers.json with per-layer block counts and the palette.
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

art, assets = sys.argv[1:3]
TEX = os.path.join(assets, "assets", "minecraft", "textures", "block")
BG, GRID, GRID5 = (11, 42, 74), (30, 70, 112), (52, 98, 146)
_cache = {}


def avg_color(name):
    if name in _cache:
        return _cache[name]
    base = name
    for suf in ("_stairs", "_slab", "_wall", "_fence_gate", "_fence", "_pressure_plate", "_button", "_trapdoor", "_door"):
        if base.endswith(suf):
            base = base[: -len(suf)]
    cands = [name, name + "_top", name + "_side", name + "_front", base, base + "_planks", base + "s",
             base.replace("waxed_", ""), base.replace("polished_", ""), base + "_block"]
    if "wire" in name:
        col = (205, 30, 30)
    elif "water" in name:
        col = (52, 96, 210)
    elif "lava" in name:
        col = (222, 110, 20)
    else:
        col = None
        for c in cands:
            p = os.path.join(TEX, c + ".png")
            if os.path.exists(p):
                im = Image.open(p).convert("RGBA")
                im = im.crop((0, 0, im.width, im.width))           # animated strips: first frame
                px = [q for q in im.getdata() if q[3] > 40]
                if px:
                    col = tuple(int(sum(q[i] for q in px) / len(px)) for i in range(3))
                    if c.startswith(("grass_block", "oak_leaves", "vine")) or "leaves" in c:
                        col = (int(col[0] * .55), int(col[1] * .85), int(col[2] * .45))
                break
        if col is None:                                            # stable fallback hue
            h = sum(map(ord, name)) % 360
            col = tuple(int(150 + 80 * math.cos(math.radians(h + k * 120))) for k in range(3))
    _cache[name] = col
    return col


def props(state):
    if "[" not in state:
        return {}
    return dict(kv.split("=") for kv in state[state.index("[") + 1:-1].split(",") if "=" in kv)


DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def arrow(d, x0, y0, s, direction, col):
    dx, dy = DIRS[direction]
    cx, cy = x0 + s / 2, y0 + s / 2
    tip = (cx + dx * s * .38, cy + dy * s * .38)
    tail = (cx - dx * s * .32, cy - dy * s * .32)
    d.line([tail, tip], fill=col, width=max(1, int(s / 8)))
    px, py = -dy, dx
    d.polygon([tip, (tip[0] - dx * s * .22 + px * s * .18, tip[1] - dy * s * .22 + py * s * .18),
               (tip[0] - dx * s * .22 - px * s * .18, tip[1] - dy * s * .22 - py * s * .18)], fill=col)


def draw_layer(cells, dx, dz, s):
    W, H = dx * s + 1, dz * s + 1
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for i in range(dx + 1):
        d.line([(i * s, 0), (i * s, H)], fill=GRID5 if i % 5 == 0 else GRID)
    for j in range(dz + 1):
        d.line([(0, j * s), (W, j * s)], fill=GRID5 if j % 5 == 0 else GRID)
    for (x, z), state in cells.items():
        n = state.split("[")[0].replace("minecraft:", "")
        x0, y0 = x * s, z * s
        p = props(state)
        if n == "redstone_wire":
            r = max(1.5, s * .22)
            d.ellipse([x0 + s / 2 - r, y0 + s / 2 - r, x0 + s / 2 + r, y0 + s / 2 + r], fill=(230, 40, 35))
            for k, v in DIRS.items():
                if p.get(k, "none") != "none":
                    d.line([(x0 + s / 2, y0 + s / 2), (x0 + s / 2 + v[0] * s / 2, y0 + s / 2 + v[1] * s / 2)], fill=(230, 40, 35), width=max(1, int(s / 6)))
            continue
        col = avg_color(n)
        pad = 0 if s < 6 else 1
        d.rectangle([x0 + pad, y0 + pad, x0 + s - pad, y0 + s - pad], fill=col)
        if s >= 8:
            f = p.get("facing")
            light = (255, 255, 255) if sum(col) < 380 else (20, 20, 20)
            if n in ("repeater", "comparator") and f in OPP:
                arrow(d, x0, y0, s, OPP[f], light)                 # facing = input side
            elif f in DIRS and any(k in n for k in ("piston", "dispenser", "dropper", "observer", "hopper", "crafter")):
                arrow(d, x0, y0, s, f, light)
            elif f in ("up", "down"):
                c = (x0 + s / 2, y0 + s / 2); r = s * .25
                if f == "up":
                    d.polygon([(c[0], c[1] - r), (c[0] - r, c[1] + r * .8), (c[0] + r, c[1] + r * .8)], outline=light, width=max(1, int(s / 10)))
                else:
                    d.polygon([(c[0], c[1] + r), (c[0] - r, c[1] - r * .8), (c[0] + r, c[1] - r * .8)], outline=light, width=max(1, int(s / 10)))
    return im


out_root = os.path.join(art, "layers")
for f in sorted(os.listdir(art)):
    if not f.endswith(".blocks.json"):
        continue
    slug = f[: -len(".blocks.json")]
    blocks = json.load(open(os.path.join(art, f)))
    if not blocks:
        continue
    dx = max(b[0] for b in blocks) + 1; dy = max(b[1] for b in blocks) + 1; dz = max(b[2] for b in blocks) + 1
    s = max(2, min(40, int(1400 / max(dx, dz))))
    od = os.path.join(out_root, slug)
    os.makedirs(od, exist_ok=True)
    meta = {"size": [dx, dy, dz], "cell": s, "layers": []}
    for y in range(dy):
        cells = {(b[0], b[2]): b[3] for b in blocks if b[1] == y}
        if not cells:
            continue
        draw_layer(cells, dx, dz, s).save(os.path.join(od, f"y{y:03d}.png"), optimize=True)
        cnt = {}
        for v in cells.values():
            n = v.split("[")[0].replace("minecraft:", "")
            cnt[n] = cnt.get(n, 0) + 1
        meta["layers"].append({"y": y, "file": f"y{y:03d}.png", "blocks": len(cells),
                               "counts": dict(sorted(cnt.items(), key=lambda kv: -kv[1]))})
    meta["palette"] = {n: "#%02x%02x%02x" % avg_color(n) for L in meta["layers"] for n in L["counts"]}
    json.dump(meta, open(os.path.join(od, "layers.json"), "w"))
    print(slug, len(meta["layers"]), "layers")
