"""Mesh Minecraft blocks the way the game does: blockstate -> model -> textured quads.

    from mcmesh import Mesher
    m = Mesher(assets_dir, blocks_report_json)
    scene = m.mesh(blocks)          # blocks: {(x, y, z): "minecraft:name[k=v,...]"}
    m.write(scene, out_dir)         # atlas.png + mesh.bin + mesh.json for render/mcview.html

assets_dir is the extracted client jar (contains assets/minecraft/...). blocks_report_json is
reports/blocks.json from the vanilla data generator; it supplies default properties, which 26.x
saves omit for default states. Supported: variants + multipart blockstates, parent chains,
element rotation (with rescale), face uv/rotation, x/y model rotation, uvlock (box projection),
cullface against full opaque neighbours, MC's directional face shading, grass/foliage/water/
redstone tints. Block entities (chests, signs, ...) without block models get simple stand-ins.
"""
import json
import math
import os
import struct

import numpy as np
from PIL import Image

FACE_NORMALS = {"down": (0, -1, 0), "up": (0, 1, 0), "north": (0, 0, -1), "south": (0, 0, 1),
                "west": (-1, 0, 0), "east": (1, 0, 0)}
FACE_SHADE = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "west": 0.6, "east": 0.6}
TRANSLUCENT = ("water", "glass", "ice", "nether_portal", "slime_block", "honey_block", "tinted_glass")
GRASS = (0.49, 0.74, 0.35)
FOLIAGE = (0.36, 0.67, 0.22)
WATER = (0.25, 0.46, 0.89)
GRASS_TINTED = ("grass_block", "short_grass", "tall_grass", "fern", "large_fern", "sugar_cane")
FOLIAGE_TINTED = ("oak_leaves", "jungle_leaves", "acacia_leaves", "dark_oak_leaves", "mangrove_leaves", "vine")
# stand-in textures for blocks rendered by block-entity renderers in the real game
STANDIN = {
    "chest": "oak_planks", "trapped_chest": "oak_planks", "ender_chest": "obsidian",
    "oak_wall_sign": "oak_planks", "oak_sign": "oak_planks", "dark_oak_wall_sign": "dark_oak_planks",
    "spruce_wall_sign": "spruce_planks", "barrier": None, "light": None, "structure_void": None,
    "moving_piston": None, "bubble_column": "water_still",
}


def parse_state(s):
    if "[" in s:
        name, props = s[:-1].split("[", 1)
        kv = dict(p.split("=", 1) for p in props.split(",") if p)
    else:
        name, kv = s, {}
    return name.replace("minecraft:", ""), kv


def rot_point(p, axis, ang, origin, rescale=False):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    x, y, z = p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]
    if axis == "x":
        y, z = y * c - z * s, y * s + z * c
    elif axis == "y":
        x, z = x * c + z * s, -x * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    if rescale and ang % 90:
        k = 1 / math.cos(math.radians(abs(ang) % 90 if abs(ang) % 90 <= 45 else 90 - abs(ang) % 90))
        if axis == "x":
            y, z = y * k, z * k
        elif axis == "y":
            x, z = x * k, z * k
        else:
            x, y = x * k, y * k
    return (x + origin[0], y + origin[1], z + origin[2])


class Mesher:
    def __init__(self, assets, report):
        self.root = os.path.join(assets, "assets", "minecraft")
        with open(report) as f:
            rep = json.load(f)
        self.defaults = {}
        for name, b in rep.items():
            for st in b.get("states", []):
                if st.get("default"):
                    self.defaults[name.replace("minecraft:", "")] = st.get("properties", {})
        self._bs, self._models, self._tex, self._full = {}, {}, {}, {}
        self.tex_index = {}

    # ---------------- resources ----------------
    def blockstate(self, name):
        if name not in self._bs:
            fn = os.path.join(self.root, "blockstates", name + ".json")
            self._bs[name] = json.load(open(fn)) if os.path.exists(fn) else None
        return self._bs[name]

    def model(self, ref):
        ref = ref.replace("minecraft:", "")
        if ref in self._models:
            return self._models[ref]
        fn = os.path.join(self.root, "models", ref + ".json")
        if not os.path.exists(fn):
            self._models[ref] = None
            return None
        m = json.load(open(fn))
        tex, elements = {}, None
        chain = [m]
        while "parent" in chain[-1] and not chain[-1]["parent"].startswith("builtin/"):
            pf = os.path.join(self.root, "models", chain[-1]["parent"].replace("minecraft:", "") + ".json")
            if not os.path.exists(pf):
                break
            chain.append(json.load(open(pf)))
        for c in reversed(chain):
            tex.update(c.get("textures", {}))
            if "elements" in c:
                elements = c["elements"]
        res = {"textures": tex, "elements": elements or [], "ao": m.get("ambientocclusion", True)}
        self._models[ref] = res
        return res

    def resolve_tex(self, tex, ref, depth=0):
        # 26.x allows {"sprite": ..., "force_translucent": ...} in place of a texture string
        if isinstance(ref, dict):
            ref = ref.get("sprite")
        while ref and ref.startswith("#") and depth < 10:
            ref = tex.get(ref[1:])
            if isinstance(ref, dict):
                ref = ref.get("sprite")
            depth += 1
        if not ref:
            return None
        return ref.replace("minecraft:", "").replace("block/", "", 1) if ref.replace("minecraft:", "").startswith("block/") else ref.replace("minecraft:", "")

    def tex_id(self, name):
        if name not in self.tex_index:
            self.tex_index[name] = len(self.tex_index)
        return self.tex_index[name]

    def tex_alpha(self, name):
        if name not in self._tex:
            fn = os.path.join(self.root, "textures", "block", name + ".png")
            if not os.path.exists(fn):
                fn = os.path.join(self.root, "textures", name + ".png")
            if os.path.exists(fn):
                im = Image.open(fn).convert("RGBA")
                w = im.width
                im = im.crop((0, 0, w, w))  # first frame of animated strips
                a = np.array(im)[:, :, 3]
                self._tex[name] = (im, int(a.min()) < 255)
            else:
                self._tex[name] = (None, False)
        return self._tex[name]

    # ---------------- state -> models ----------------
    def models_for(self, state):
        name, props = parse_state(state)
        full = dict(self.defaults.get(name, {}))
        full.update(props)
        bs = self.blockstate(name)
        out = []
        if bs is None:
            return name, full, out
        if "variants" in bs:
            best = None
            for key, v in bs["variants"].items():
                conds = dict(c.split("=", 1) for c in key.split(",") if c)
                if all(full.get(k) == val for k, val in conds.items()):
                    best = v
                    break
            if best is not None:
                out.append(best[0] if isinstance(best, list) else best)
        for part in bs.get("multipart", []):
            if self._when(part.get("when"), full):
                a = part["apply"]
                out.append(a[0] if isinstance(a, list) else a)
        return name, full, out

    def _when(self, w, props):
        if w is None:
            return True
        if "OR" in w:
            return any(self._when(x, props) for x in w["OR"])
        if "AND" in w:
            return all(self._when(x, props) for x in w["AND"])
        for k, v in w.items():
            if str(props.get(k)) not in str(v).split("|"):
                return False
        return True

    def is_full_opaque(self, state):
        if state in self._full:
            return self._full[state]
        name, _, models = self.models_for(state)
        ok = False
        if len(models) == 1 and not name.endswith(TRANSLUCENT) and name not in TRANSLUCENT:
            m = self.model(models[0]["model"])
            if m and len(m["elements"]) == 1:
                e = m["elements"][0]
                if e["from"] == [0, 0, 0] and e["to"] == [16, 16, 16] and len(e.get("faces", {})) == 6:
                    texs = [self.resolve_tex(m["textures"], f["texture"]) for f in e["faces"].values()]
                    ok = all(t and not self.tex_alpha(t)[1] for t in texs)
        self._full[state] = ok
        return ok

    def tint(self, name, props, idx):
        if idx is None or idx < 0:
            return (1, 1, 1)
        if name == "redstone_wire":
            p = int(props.get("power", 0)) / 15
            return (p * 0.6 + (0.4 if p > 0 else 0.3), max(0, min(1, p * p * 0.7 - 0.5)), max(0, min(1, p * p * 0.6 - 0.7)))
        if name in GRASS_TINTED:
            return GRASS
        if name in FOLIAGE_TINTED:
            return FOLIAGE
        if "water" in name:
            return WATER
        return (1, 1, 1)

    # ---------------- meshing ----------------
    def mesh(self, blocks, entities=()):
        buf = {"opaque": [], "translucent": []}
        full = {p: self.is_full_opaque(s) for p, s in blocks.items()}
        for (bx, by, bz), state in blocks.items():
            name, props, models = self.models_for(state)
            if name in ("water", "bubble_column") or (name == "lava"):
                self._fluid(buf, (bx, by, bz), name, props, blocks)
                continue
            if not models:
                stand = STANDIN.get(name, "oak_planks" if "sign" in name or "banner" in name else None)
                if stand:
                    self._box(buf["opaque"], (bx, by, bz), (1, 1, 1), (15, 14, 15), stand, (1, 1, 1))
                continue
            layer = "translucent" if name in TRANSLUCENT or name.endswith("glass") or name.endswith("glass_pane") else "opaque"
            if props.get("waterlogged") == "true":
                self._fluid(buf, (bx, by, bz), "water", {"level": "0"}, blocks)
            for mv in models:
                m = self.model(mv["model"])
                if not m:
                    continue
                rx, ry, uvlock = mv.get("x", 0), mv.get("y", 0), mv.get("uvlock", False)
                for el in m["elements"]:
                    self._element(buf[layer], (bx, by, bz), el, m["textures"], rx, ry, uvlock, name, props, full)
        for kind, pos in entities:
            if kind == "tnt":
                self._box(buf["opaque"], None, (pos[0] - 0.49, pos[1], pos[2] - 0.49), (pos[0] + 0.49, pos[1] + 0.98, pos[2] + 0.49),
                          ("tnt_side", "tnt_top", "tnt_bottom"), (1, 1, 1), absolute=True)
        return buf

    def _element(self, out, base, el, tex, rx, ry, uvlock, name, props, full):
        f0, t0 = el["from"], el["to"]
        r = el.get("rotation")
        for face, fd in el.get("faces", {}).items():
            tname = self.resolve_tex(tex, fd.get("texture"))
            if not tname:
                continue
            # cull against the neighbour in the rotated direction
            cf = fd.get("cullface")
            if cf:
                n = self._rot_dir(FACE_NORMALS[cf], rx, ry)
                nb = (base[0] + n[0], base[1] + n[1], base[2] + n[2])
                if full.get(nb):
                    continue
            quad = self._face_quad(f0, t0, face)
            uv = fd.get("uv") or self._default_uv(f0, t0, face)
            if r:
                quad = [rot_point(p, r["axis"], r["angle"], r["origin"], r.get("rescale", False)) for p in quad]
            quad = [self._rot_block(p, rx, ry) for p in quad]
            if uvlock and not r:
                uv = None
            normal = self._rot_dir(FACE_NORMALS[face], rx, ry)
            if r:
                normal = self._rot_dir(normal, 0, 0)
            shade_face = min(FACE_NORMALS, key=lambda k: -sum(a * b for a, b in zip(FACE_NORMALS[k], normal)))
            shade = FACE_SHADE[shade_face] if el.get("shade", True) else 1.0
            tint = self.tint(name, props, fd.get("tintindex"))
            col = tuple(c * shade for c in tint)
            pts = [(base[0] + p[0] / 16, base[1] + p[1] / 16, base[2] + p[2] / 16) for p in quad]
            if uv is None:
                uv = self._project_uv(pts, shade_face)
                uvs = uv
            else:
                uvs = self._uv_corners(uv, fd.get("rotation", 0))
            out.append((pts, uvs, self.tex_id(tname), col))
            self.tex_alpha(tname)

    @staticmethod
    def _face_quad(f, t, face):
        x0, y0, z0 = f
        x1, y1, z1 = t
        return {
            "down": [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
            "up": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
            "north": [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
            "south": [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
            "west": [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
            "east": [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
        }[face]

    @staticmethod
    def _default_uv(f, t, face):
        x0, y0, z0 = f
        x1, y1, z1 = t
        return {
            "down": [x0, 16 - z1, x1, 16 - z0], "up": [x0, z0, x1, z1],
            "north": [16 - x1, 16 - y1, 16 - x0, 16 - y0], "south": [x0, 16 - y1, x1, 16 - y0],
            "west": [z0, 16 - y1, z1, 16 - y0], "east": [16 - z1, 16 - y1, 16 - z0, 16 - y0],
        }[face]

    @staticmethod
    def _uv_corners(uv, rot):
        u0, v0, u1, v1 = [c / 16 for c in uv]
        c = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        k = (rot // 90) % 4
        return c[k:] + c[:k]

    @staticmethod
    def _project_uv(pts, face):
        out = []
        for x, y, z in pts:
            fx, fy, fz = x % 1 if x % 1 else (1.0 if face in ("east",) else 0.0), y % 1, z % 1
            if face in ("up", "down"):
                u, v = x - math.floor(x + 1e-6 * 0), z - math.floor(z)
            elif face in ("north", "south"):
                u, v = x - math.floor(x), 1 - (y - math.floor(y))
            else:
                u, v = z - math.floor(z), 1 - (y - math.floor(y))
            out.append((min(max(u, 0), 1), min(max(v, 0), 1)))
        return out

    @staticmethod
    def _rot_block(p, rx, ry):
        if rx:
            p = rot_point(p, "x", -rx, (8, 8, 8))
        if ry:
            p = rot_point(p, "y", -ry, (8, 8, 8))
        return p

    @staticmethod
    def _rot_dir(d, rx, ry):
        p = (d[0] * 8 + 8, d[1] * 8 + 8, d[2] * 8 + 8)
        p = Mesher._rot_block(p, rx, ry)
        return tuple(int(round((c - 8) / 8)) for c in p)

    def _fluid(self, buf, pos, name, props, blocks):
        lvl = int(props.get("level", 0))
        h = 14.2 / 16 if lvl == 0 else max(2, 14 - lvl * 2) / 16
        above = blocks.get((pos[0], pos[1] + 1, pos[2]), "")
        if "water" in above or "waterlogged=true" in above:
            h = 1.0
        tex = "water_still" if name != "lava" else "lava_still"
        col = WATER if name != "lava" else (1, 1, 1)
        for face in FACE_NORMALS:
            n = FACE_NORMALS[face]
            nb = blocks.get((pos[0] + n[0], pos[1] + n[1], pos[2] + n[2]), "")
            if "water" in nb or "waterlogged=true" in nb or self.is_full_opaque(nb) if nb else False:
                continue
            q = self._face_quad((0, 0, 0), (16, h * 16, 16), face)
            pts = [(pos[0] + p[0] / 16, pos[1] + p[1] / 16, pos[2] + p[2] / 16) for p in q]
            buf["translucent" if name != "lava" else "opaque"].append(
                (pts, self._uv_corners(self._default_uv((0, 0, 0), (16, 16, 16), face), 0), self.tex_id(tex),
                 tuple(c * FACE_SHADE[face] for c in col)))
            self.tex_alpha(tex)

    def _box(self, out, base, a, b, tex, col, absolute=False):
        if isinstance(tex, str):
            tex = (tex, tex, tex)
        side, top, bottom = tex
        for face in FACE_NORMALS:
            t = top if face == "up" else bottom if face == "down" else side
            if absolute:
                q = self._face_quad(a, b, face)
                pts = q
            else:
                q = self._face_quad(a, b, face)
                pts = [(base[0] + p[0] / 16, base[1] + p[1] / 16, base[2] + p[2] / 16) for p in q]
            out.append((pts, self._uv_corners([0, 0, 16, 16], 0), self.tex_id(t),
                        tuple(c * FACE_SHADE[face] for c in col)))
            self.tex_alpha(t)

    # ---------------- output ----------------
    def write(self, buf, out_dir, origin=(0, 0, 0)):
        os.makedirs(out_dir, exist_ok=True)
        names = sorted(self.tex_index, key=self.tex_index.get)
        n = len(names)
        cols = int(math.ceil(math.sqrt(n)))
        size = 16
        atlas = Image.new("RGBA", (cols * size, cols * size), (0, 0, 0, 0))
        for i, nm in enumerate(names):
            im = self.tex_alpha(nm)[0]
            if im is None:
                im = Image.new("RGBA", (16, 16), (255, 0, 255, 255))
            atlas.paste(im.resize((size, size), Image.NEAREST), ((i % cols) * size, (i // cols) * size))
        atlas.save(os.path.join(out_dir, "atlas.png"))
        meta = {"origin": origin, "layers": {}}
        with open(os.path.join(out_dir, "mesh.bin"), "wb") as f:
            for layer, quads in buf.items():
                pos, uv, col = [], [], []
                for pts, uvs, tid, c in quads:
                    tu, tv = (tid % cols) / cols, (tid // cols) / cols
                    for tri in ((0, 1, 2), (0, 2, 3)):
                        for k in tri:
                            p = pts[k]
                            pos += [p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]]
                            u, v = uvs[k]
                            # inset half a texel to avoid atlas bleeding
                            u = min(max(u, 0.5 / 16), 1 - 0.5 / 16)
                            v = min(max(v, 0.5 / 16), 1 - 0.5 / 16)
                            uv += [tu + u / cols, 1 - (tv + v / cols)]
                            col += [int(min(1, c[0]) * 255), int(min(1, c[1]) * 255), int(min(1, c[2]) * 255)]
                start = f.tell()
                f.write(np.asarray(pos, dtype=np.float32).tobytes())
                f.write(np.asarray(uv, dtype=np.float32).tobytes())
                f.write(np.asarray(col, dtype=np.uint8).tobytes())
                pad = (-f.tell()) % 4
                f.write(b"\0" * pad)
                meta["layers"][layer] = {"offset": start, "vertices": len(pos) // 3}
        with open(os.path.join(out_dir, "mesh.json"), "w") as f:
            json.dump(meta, f)
        return meta
