"""Build The Orbital Strike Codex: five volumes of HTML, printed to PDF by print.js.

    python3 build.py <art dir> <out dir> [volumes, e.g. 1,2,3,4,5]

<art dir> holds the renders and layer plans (render_schematics.py, blueprints.py) and
catalog.json. Text comes from content_*.py in this directory, data from ../paper-tests and
../research. Untrusted text (video titles, descriptions, transcripts) is always escaped.
"""
import csv
import html
import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
ART, OUT = sys.argv[1], sys.argv[2]
VOLS = [int(v) for v in (sys.argv[3] if len(sys.argv) > 3 else "1,2,3,4,5").split(",")]
E = html.escape
os.makedirs(OUT, exist_ok=True)
for f in ("book.css", "paginate.js"):
    shutil.copy(os.path.join(HERE, f), OUT)
os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
if True:
    shutil.copytree(os.path.join(ROOT, "showcase", "assets"), os.path.join(OUT, "assets"),
                    ignore=shutil.ignore_patterns("thumbs", "data.json", "manifest.json", "three.min.js"), dirs_exist_ok=True)
if not os.path.exists(os.path.join(OUT, "assets", "grain.png")):
    import random
    g = Image.new("LA", (64, 64)); rnd = random.Random(7)
    g.putdata([(rnd.choice((60, 90, 120)), rnd.choice((0, 0, 0, 10, 18))) for _ in range(64 * 64)])
    g.save(os.path.join(OUT, "assets", "grain.png"))
for name, target in [("art", os.path.abspath(ART))]:
    link = os.path.join(OUT, name)
    if not os.path.exists(link):
        os.symlink(target, link)
CATALOG = {c["slug"]: c for c in json.load(open(os.path.join(ART, "catalog.json")))}


# ----------------------------------------------------------------------------- page helpers
def fixed(html_, chapter=None, cls="", dark=False, nofurn=False):
    return {"type": "fixed", "html": html_, "chapter": chapter, "cls": cls, "dark": dark, "nofurn": nofurn}


def flow(chapter, blocks):
    return {"type": "flow", "chapter": chapter, "blocks": blocks}


def trimmed(src, dst, pad=12):
    """Copy a transparent render with its empty margins cropped."""
    if not os.path.exists(dst):
        im = Image.open(src)
        bb = im.getbbox()
        if bb:
            im = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))
        im.save(dst)
    return dst


def render(slug, view):
    src = os.path.join(ART, f"{slug}-{view}.png")
    if not os.path.exists(src):
        return None
    os.makedirs(os.path.join(ART, "trim"), exist_ok=True)
    trimmed(src, os.path.join(ART, "trim", f"{slug}-{view}.png"))
    return f"art/trim/{slug}-{view}.png"


def cover(numeral, title_html, sub, art=None, color="var(--coral)"):
    img = f'<div class="art"><img src="{art}"></div>' if art else ""
    return fixed(f'''<div class="vol">The Orbital Strike Codex · Volume {numeral}</div>
      <div class="big">{title_html}</div>{img}<div class="sub">{sub}</div>
      <div class="numeral" style="color:{color}">{numeral}</div><div class="stripe"></div>''', cls="cover", nofurn=True)


def opener(ch, kicker, title, dek, facts=(), bg=None):
    f = "".join(f"<div><b>{E(str(v))}</b>{E(k)}</div>" for k, v in facts)
    return fixed(f'''<div class="num">{ch["no"]}</div><div class="kick">{kicker}</div>
      <div class="title">{title}</div><div class="dek">{dek}</div><div class="facts">{f}</div>''',
                 chapter=ch["id"], cls="opener", dark=True) | {"bg": bg or ch.get("color")}


def toc_page(title, chapters, compact=False):
    rows = "".join(f'<div class="row"><span class="n">{E(str(c["no"]))}</span><span class="t">{E(c["title"])}'
                   f'{"<small>" + E(c.get("dek", "")) + "</small>" if c.get("dek") and not compact else ""}</span>'
                   f'<span class="p" data-toc="{c["id"]}"></span></div>' for c in chapters)
    return fixed(f'<div class="body"><h1>{title}</h1>{rows}</div>', cls="toc" + (" compact" if compact else ""))


def write_volume(vol, seq, chapters):
    data = json.dumps(seq)
    chaps = json.dumps({c["id"]: c for c in chapters})
    bgcss = "".join(f'.page[data-chapter="{c["id"]}"].opener {{ background: {c.get("color", "var(--ink)")}; }}\n' for c in chapters)
    doc = f'''<!doctype html><html><head><meta charset="utf-8"><title>{E(vol["title"])}</title>
<link rel="stylesheet" href="assets/fonts.css"><link rel="stylesheet" href="book.css">
<style>{bgcss}</style></head><body><div id="book"></div>
<script>window.VOLUME = {json.dumps(vol)}; window.CHAPTERS = {chaps}; window.SEQ = {data}; window.START_PAGE = {vol.get("start", 1)};</script>
<script>document.fonts.ready.then(() => {{ const s = document.createElement('script'); s.src = 'paginate.js'; document.body.appendChild(s); }});</script>
</body></html>'''
    path = os.path.join(OUT, f"vol{vol['numeral_n']}.html")
    open(path, "w").write(doc)
    return path


# ----------------------------------------------------------------------------- shared bits
CHAN_COL = {"cubicmetre": "#e5673b", "tkparmaa": "#3f9ad6", "wmc": "#4fae6a", "dumbrock": "#b88ad9", "hogan": "#e9b23a",
            "table": "#d0457a", "this book": "#e9b23a"}


def mats_bar(counts, palette, n=10):
    tot = sum(counts.values())
    items = list(counts.items())[:n]
    rest = tot - sum(v for _, v in items)
    bar = "".join(f'<i style="width:{v / tot * 100:.2f}%;background:{palette.get(k, "#888")}"></i>' for k, v in items)
    if rest > 0:
        bar += f'<i style="width:{rest / tot * 100:.2f}%;background:#555"></i>'
    key = "".join(f'<span><i style="background:{palette.get(k, "#888")}"></i>{E(k)} {v}</span>' for k, v in items)
    return f'<div class="bar">{bar}</div><div class="barkey">{key}{"<span>+ " + str(rest) + " other</span>" if rest else ""}</div>'


def layers_meta(slug):
    p = os.path.join(ART, "layers", slug, "layers.json")
    return json.load(open(p)) if os.path.exists(p) else None


ITEM = {"redstone_wire": "redstone dust", "wall_torch": "torch", "redstone_wall_torch": "redstone torch", "tripwire": "string",
        "water": "water bucket", "lava": "lava bucket", "powder_snow": "powder snow bucket", "bubble_column": "water bucket"}
SKIP_ITEMS = ("piston_head", "moving_piston", "nether_portal", "fire", "air", "cave_air", "void_air", "light", "barrier", "structure_void")
STACK16 = ("sign", "banner", "ender_pearl", "snowball", "egg", "bucket")
STACK1 = ("bed", "bucket", "shulker_box", "minecart", "boat")


def bom_blocks(slug, chapter):
    """Bill of materials: every block as the item you would gather, with stacks and shulker boxes."""
    c = CATALOG[slug]
    pal = (layers_meta(slug) or {}).get("palette", {})
    items = {}
    for n, v in c["counts"].items():
        if n in SKIP_ITEMS:
            continue
        base = n
        for half in ("_head", "_foot"):
            pass
        name = ITEM.get(n, n.replace("_", " "))
        items.setdefault(name, [0, pal.get(n, "#888")])[0] += v
    rows = []
    tot_stacks = 0
    for name, (cnt, col) in sorted(items.items(), key=lambda kv: -kv[1][0]):
        size = 1 if any(k in name for k in ("bed", "bucket", "minecart", "boat")) else 16 if any(k in name for k in ("sign", "banner", "pearl")) else 64
        st, rest = divmod(cnt, size)
        stacks = st + (1 if rest else 0)
        tot_stacks += stacks
        stack_txt = (f"{st} × {size}" if st else "") + (" + " if st and rest else "") + (str(rest) if rest else "")
        rows.append(f'<tr><td><span style="display:inline-block;width:3mm;height:3mm;background:{col};border:.2mm solid #15120f;vertical-align:middle;margin-right:1.6mm"></span>{E(name)}</td>'
                    f'<td>{cnt:,}</td><td>{stack_txt}</td><td>{stacks}</td></tr>')
    shulkers = (tot_stacks + 26) // 27
    head = (f'<h2>{E(c["name"])}: <em>bill of materials</em></h2>'
            f'<div class="stats"><div><b>{sum(v[0] for v in items.values()):,}</b><span>items to gather</span></div>'
            f'<div><b>{tot_stacks}</b><span>inventory stacks</span></div><div><b>{shulkers}</b><span>shulker boxes (27 stacks)</span></div></div>'
            f'<p>Every block in the schematic, as the item you would collect: dust counts as redstone, fluids as buckets, '
            f'and technical blocks (piston heads, portals, fire) are left out. Entities the build needs (boats, minecarts, the '
            f'payload) are not in the schematic and not in this list.</p>')
    table = ('<table class="data"><thead><tr><th>item</th><th>count</th><th>stacks</th><th>slots</th></tr></thead><tbody>'
             + "".join(rows) + "</tbody></table>")
    return flow(chapter, [head, table])


def design_pages(slug, chapter, blurb, per_page=None, sheet_name=None):
    """Overview, elevations and layer sheets for one design."""
    c = CATALOG[slug]
    meta = layers_meta(slug)
    pal = meta["palette"] if meta else {}
    name = sheet_name or c["name"]
    pages = []
    iso = render(slug, "iso")
    sx, sy, sz = c["size"]
    redstone = sum(v for k, v in c["counts"].items() if any(t in k for t in ("redstone", "repeater", "comparator", "observer", "piston", "dispenser", "dropper", "hopper", "bulb", "lever", "button", "rail")))
    pages.append(fixed(f'''<div class="frame"></div>
      <div class="render" style="left:10mm;right:10mm;top:20mm;height:142mm">{f'<img src="{iso}">' if iso else ''}</div>
      <div class="by">{E(c["creator"])} · {E(c["source"].split("/")[-1])}</div>
      <div class="name">{E(name)}</div>
      <div class="specs"><div><b>{sx}×{sy}×{sz}</b>footprint × height</div><div><b>{c["blocks"]:,}</b>blocks</div>
        <div><b>{len(c["counts"])}</b>block types</div><div><b>{redstone:,}</b>redstone parts</div></div>
      <div class="blurb">{blurb}</div>
      <div class="mats">{mats_bar(c["counts"], pal)}</div>''', chapter=chapter, cls="bp ov", dark=True))
    pages.append(bom_blocks(slug, chapter))
    views = [(v, render(slug, v)) for v in ("north", "south", "east", "west")]
    if any(p for _, p in views):
        figs = "".join(f'<figure><figcaption>{v} elevation</figcaption>{f"<img src={chr(34)}{p}{chr(34)}>" if p else ""}</figure>' for v, p in views)
        pages.append(fixed(f'''<div class="frame"></div><div class="hdr"><div class="t">{E(name)} · <em>side pictures</em></div>
          <div class="s">orthographic · real 26.3 textures</div></div><div class="elev">{figs}</div>''', chapter=chapter, cls="bp", dark=True))
    if not meta:
        return pages
    L = meta["layers"]
    dx, dy, dz = meta["size"]
    k = per_page or (1 if max(dx, dz) > 64 else 2 if max(dx, dz) > 22 else 4)
    total = (len(L) + k - 1) // k
    for i in range(0, len(L), k):
        grp = L[i:i + k]
        if k == 1:
            plan = f'<div class="plan"><img src="art/layers/{slug}/{grp[0]["file"]}"></div>'
        else:
            cols = 1 if k == 2 and dx > dz * 1.3 else 2
            rows = (k + cols - 1) // cols
            figs = "".join(f'<figure><img src="art/layers/{slug}/{g["file"]}"><figcaption>LAYER Y+{g["y"]} · {g["blocks"]} blocks</figcaption></figure>' for g in grp)
            plan = f'<div class="plan multi" style="grid-template-columns:repeat({cols},1fr);grid-template-rows:repeat({rows},1fr)">{figs}</div>'
        cnt = {}
        for g in grp:
            for n, v in g["counts"].items():
                cnt[n] = cnt.get(n, 0) + v
        leg = "".join(f'<div><i style="background:{pal.get(n, "#888")}"></i>{E(n)} ×{v}</div>' for n, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:22])
        ys = f'Y+{grp[0]["y"]}' + (f'–{grp[-1]["y"]}' if len(grp) > 1 else "")
        pages.append(fixed(f'''<div class="frame"></div>
          <div class="hdr"><div class="t">{E(name)} · <em>layer {ys}</em></div><div class="s">plan view · north up · 1 square = 1 block</div></div>
          {plan}
          <svg class="north" viewBox="0 0 24 24"><polygon points="12,1 18,22 12,17 6,22" fill="#e9b23a"/><text x="12" y="15" font-size="7" text-anchor="middle" fill="#0b2a4a" font-family="Anton">N</text></svg>
          <div class="legend"><div class="lt">Materials on this sheet</div>{leg}</div>
          <div class="tblock"><div class="wide">{E(name)}</div>
            <div><i>sheet</i>{i // k + 1} / {total}</div><div><i>layers</i>{ys} of {dy}</div>
            <div><i>size</i>{dx} × {dy} × {dz}</div><div><i>source</i>{E(c["creator"])}</div>
            <div><i>arrows</i>signal / facing</div><div><i>drawn</i>Codex · 26.3</div></div>''', chapter=chapter, cls="bp", dark=True))
    return pages


# ----------------------------------------------------------------------------- volumes
VOLDEF = {
    1: {"numeral": "I", "numeral_n": 1, "title": "The Science", "short": "Science", "color": "#e5673b"},
    2: {"numeral": "II", "numeral_n": 2, "title": "The Cannons", "short": "Cannons", "color": "#3f9ad6"},
    3: {"numeral": "III", "numeral_n": 3, "title": "Zephyr", "short": "Zephyr", "color": "#e9b23a"},
    4: {"numeral": "IV", "numeral_n": 4, "title": "The Video Atlas", "short": "Atlas", "color": "#4fae6a"},
    5: {"numeral": "V", "numeral_n": 5, "title": "Data & Index", "short": "Data", "color": "#b88ad9"},
}


def build_vol2():
    import content_cannons as CC
    vol = VOLDEF[2]
    chapters, seq = [], []
    seq.append(cover("II", "The<br><em>Cannons</em>", "Every orbital strike cannon I could download, drawn layer by layer: "
                     "side pictures, materials, and a plan of every block.", render("the-orbital-strike-cannon-mk-6-1", "iso"), "#3f9ad6"))
    for i, grp in enumerate(CC.GROUPS, 1):
        ch = {"id": f"c{i}", "no": i, "title": grp["title"], "short": grp["short"], "color": grp["color"], "dek": grp["dek"]}
        chapters.append(ch)
    seq.append(toc_page("Contents", chapters))
    seq.append(flow(None, CC.INTRO))
    for ch, grp in zip(chapters, CC.GROUPS):
        n_blocks = sum(CATALOG[s]["blocks"] for s, *_ in grp["designs"] if s in CATALOG)
        seq.append(opener(ch, grp["kicker"], E(grp["title"]), grp["dek"],
                          [("designs", len(grp["designs"])), ("blocks drawn", f"{n_blocks:,}"), ("creator", grp["short"])]))
        seq.append(flow(ch["id"], grp["essay"]))
        for spec in grp["designs"]:
            slug, blurb = spec[0], spec[1]
            opts = spec[2] if len(spec) > 2 else {}
            if slug not in CATALOG:
                continue
            if opts.get("summary_only"):
                seq.extend(design_pages(slug, ch["id"], blurb)[:3])
            else:
                seq.extend(design_pages(slug, ch["id"], blurb, per_page=opts.get("per_page")))
    return vol, seq, chapters


def build_vol4():
    import content_atlas as CA
    vol = VOLDEF[4] | {"start": 1}
    rows = list(csv.DictReader(open(os.path.join(ROOT, "research", "manifest.tsv")), delimiter="\t"))
    sheets = os.path.join(OUT, "vsheets")
    os.makedirs(sheets, exist_ok=True)
    order = CA.ORDER
    groups = {}
    for r in rows:
        key = CA.group_of(r)
        groups.setdefault(key, []).append(r)
    chapters, seq = [], []
    seq.append(cover("IV", "The<br><em>Video</em><br>Atlas", "260 videos watched for this book: every cubicmetre, WMC, TK.Paarmaa and "
                     "TheeDumbRock upload, and every other orbital strike video I could find.", None, "#4fae6a"))
    for i, key in enumerate(order, 1):
        if key in groups:
            chapters.append({"id": f"a{i}", "no": i, "title": CA.TITLES[key], "short": CA.SHORT[key], "color": CA.COLORS[key],
                             "dek": f"{len(groups[key])} videos"})
    seq.append(toc_page("Contents", chapters))
    seq.append(flow(None, CA.INTRO))
    no = 0
    for ch, key in zip(chapters, [k for k in order if k in groups]):
        vids = sorted(groups[key], key=lambda r: CA.meta(r["id"]).get("upload_date") or "")
        seq.append(opener(ch, "Channel / theme", E(ch["title"]), CA.DEKS[key],
                          [("videos", len(vids)), ("hours watched", round(sum(int(CA.meta(r["id"]).get("duration") or 0) for r in vids) / 3600, 1)),
                           ("first upload", (CA.meta(vids[0]["id"]).get("upload_date") or "")[:4])]))
        for r in vids:
            no += 1
            seq.append(fixed(CA.video_page(r, no, sheets, CA.COLORS[key]), chapter=ch["id"], cls="vid"))
    return vol, seq, chapters


def img_ref(name):
    """Image reference for chapter figures: '<slug>-iso' renders or research/notes/img/<name>.png."""
    if name.endswith("-iso"):
        return render(name[:-4], "iso")
    src = os.path.join(ROOT, "research", "notes", "img", name + ".png")
    os.makedirs(os.path.join(ART, "extra"), exist_ok=True)
    dst = os.path.join(ART, "extra", name + ".png")
    if not os.path.exists(dst):
        shutil.copy(src, dst)
    return f"art/extra/{name}.png"


def prose_volume(vno, cover_html, chapters_list, design_blurbs=None):
    vol = VOLDEF[vno]
    seq = [cover_html]
    chs = [{k: v for k, v in c.items() if k not in ("blocks", "facts", "design")} for c in chapters_list]
    seq.append(toc_page("Contents", chs))
    for c in chapters_list:
        seq.append(opener(c, c.get("kicker", ""), E(c["title"]), E(c.get("dek", "")), c.get("facts", [])))
        if c["blocks"]:
            seq.append(flow(c["id"], c["blocks"]))
        for k, t in c.get("stills", []):          # one portrait frame per page
            seq.append(fixed(f'<div style="position:absolute;left:14mm;right:14mm;top:20mm;bottom:22mm;display:flex;flex-direction:column;align-items:center;justify-content:center">'
                             f'<img src="art/stills/{k}.jpg" style="height:236mm;border:.8mm solid #dfe9f5;box-shadow:0 4mm 10mm rgba(0,0,0,.5)">'
                             f'<div style="font-family:JetBrains Mono,monospace;font-size:8pt;color:#e9b23a;margin-top:3mm;letter-spacing:1px">{E(t)}</div></div>',
                             chapter=c["id"], cls="bp", dark=True))
        if c.get("design") and c["design"] in CATALOG:
            seq.extend(design_pages(c["design"], c["id"], (design_blurbs or {}).get(c["design"], "")))
    return vol, seq, chs


def build_vol1():
    import content_science as CS
    return prose_volume(1, cover("I", "The<br><em>Science</em>", "How an orbital strike cannon works, measured: chunk tickets, "
                                 "stasis, axis order, explosions, wind charges, the powder-snow brake, and the redstone around them.",
                                 render("the-orbital-strike-cannon-mk-6-1", "iso"), "#e5673b"), CS.chapters())


def build_vol3():
    import content_zephyr as CZ
    chs = CZ.chapters(img_ref)
    for c in chs:
        if c["id"] == "z3":
            c["design"] = "zephyr-mk1-a"
    blurbs = {"zephyr-mk1-a": "Mk1-A: the Zephyr core with a self-contained controller: observer clock and copper-bulb "
                              "divider, arming plate, per-feed stager, 50-tick launch lock, and a launch loop round the west "
                              "and north. 8 TNT live-fired 0.85 blocks from the prediction.",
              "zephyr-mk2": "Mk2: the same core, controller cut to a four-block clock column and one locked repeater. "
                            "102 blocks. 64 TNT live-fired 0.79 blocks from the prediction; 650-block crater.",
              "zephyr-mk3-drill": "Mk3 Drill: Mk2 with a 4-tick ring clock and end-of-feed staging, giving fuses 4 ticks apart. "
                                  "Live-fired 0.55 blocks from the prediction; its payload still lands half a block wide."}
    return prose_volume(3, cover("III", "<em>Zephyr</em>", "My own cannons: a seven-block core, three controllers, three live "
                                 "shots, and a ring warhead wider than 372 blocks.", render("zephyr-mk2", "iso"), "#e9b23a"), chs, blurbs)


def build_vol5():
    import content_data as CD
    return prose_volume(5, cover("V", "Data<br>&amp; <em>Index</em>", "The numbers behind the other four volumes, a glossary, a "
                                 "materials index and the full list of sources.", None, "#b88ad9"), CD.chapters(CATALOG))


def main():
    built = []
    for v in VOLS:
        fn = globals().get(f"build_vol{v}")
        if not fn:
            continue
        vol, seq, chapters = fn()
        built.append(write_volume(vol, seq, chapters))
        print("vol", v, "items", len(seq))
    json.dump(built, open(os.path.join(OUT, "built.json"), "w"))


if __name__ == "__main__":
    main()
