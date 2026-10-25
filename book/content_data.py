"""Volume V, Data & Index: tables of every test, a glossary, a materials index and the full video list."""
import csv
import glob
import html
import json
import os

import svgfig as F

E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
PT = os.path.join(HERE, "..", "paper-tests")
RS = os.path.join(HERE, "..", "research")

GLOSSARY = [
    ("Axis order", "An entity moves Y first, then the larger of X and Z (X on a tie), then the other; each step stops at the first block."),
    ("Border drift", "Arming the powder-snow brake by pushing a payload across a chunk border into snow in a lazy chunk."),
    ("Booster ring", "Short-fuse TNT that follows a nuke's ring outward and kicks it again mid-flight."),
    ("Brake", "Powder snow's one-time slowing (0.9 X/Z, 1.5 Y) followed by zero velocity: how a payload stops at its target."),
    ("Calibration", "Measuring the push of one unit of propellant per axis, so aiming becomes division."),
    ("Chunk ticket", "A reason for a chunk to be loaded, with a level that falls off with distance."),
    ("Copper bulb divider", "A copper bulb toggled by every clock pulse, read by a comparator, to halve a clock into a square wave."),
    ("Drill payload", "TNT stacked on one point with fuses a few ticks apart, so each explodes in the hole left by the last."),
    ("Duper", "A machine that duplicates TNT with pistons (disabled by default on Paper)."),
    ("Entity-processing chunk", "A chunk at ticket level 31 or lower: entities move and tick."),
    ("Expansion charge", "TNT at a nuke's centre whose blast throws the ring outward."),
    ("Fire control", "Turning a target into propellant counts and settings."),
    ("Forceload", "The /forceload command: a level-31 ticket on one chunk."),
    ("Fuse", "Ticks until primed TNT explodes; 80 when dispensed; frozen in lazy chunks."),
    ("Lazy chunk", "A loaded chunk at level 32: blocks tick, entities do not. The payload's home."),
    ("Lazy acceleration", "Adding velocity to an entity frozen in a lazy chunk."),
    ("Lock (repeater)", "A repeater whose side is powered by another diode holds its state."),
    ("max-tnt-per-tick", "Spigot setting limiting TNT explosions per tick (100 by default); -1 removes it."),
    ("Nuke", "A payload that spreads TNT over a ring or disk instead of one point."),
    ("Observer clock", "Two observers facing each other: a 2-tick pulse every 6 ticks on 26.3."),
    ("Payload", "Whatever the cannon throws: TNT, anvils, withers, pearls."),
    ("Portal ticket", "The ticket left by an entity passing a nether portal: 3×3 entity-processing chunks."),
    ("Propellant", "What pushes the payload: TNT explosions or wind-charge bursts."),
    ("Quasi-connectivity", "Pistons, dispensers and droppers count as powered when the block above them is; they only check on update."),
    ("Release", "Loading the payload's chunk so it moves its stored velocity."),
    ("Ring clock", "Two repeaters in a loop carrying one pulse: a 4-tick clock."),
    ("Stab charge", "cubicmetre's penetrating payload: kick, bulk and penetrator stages."),
    ("Staging", "Moving TNT from the loading cell into the frozen payload cell."),
    ("Stasis", "Being frozen in a lazy chunk."),
    ("Wind charge", "A projectile whose burst (0.25 above the surface it hits) knocks entities away."),
    ("Zephyr", "This book's own cannon series: Mk1-A, Mk2, Mk3."),
]


def nuke_rows():
    rows = []
    for f in sorted(glob.glob(os.path.join(PT, "nuke-*.json"))):
        d = json.load(open(f))
        r = d.get("radii") or [0]
        rows.append([os.path.basename(f)[5:-5], d.get("ring"), d.get("exp"), d.get("mode", "same"), d["centre"][1],
                     f"{min(r):.1f}", f"{r[len(r) // 2]:.1f}", f"{max(r):.1f}"])
    return rows


def video_rows():
    rows = list(csv.DictReader(open(os.path.join(RS, "manifest.tsv")), delimiter="\t"))
    out = []
    for r in rows:
        mp = os.path.join(RS, "videos", r["id"], "meta.json")
        m = json.load(open(mp)) if os.path.exists(mp) else {}
        d = m.get("upload_date") or ""
        out.append([d[:4] + "-" + d[4:6] + "-" + d[6:] if len(d) == 8 else "", m.get("channel") or r["creator"],
                    (m.get("title") or r["title"])[:70], r["id"]])
    return sorted(out)


def chapters(catalog):
    C = []

    def ch(id_, title, short, color, blocks, dek=""):
        C.append({"id": id_, "no": len(C) + 1, "title": title, "short": short, "color": color, "blocks": blocks, "dek": dek,
                  "kicker": "Reference", "facts": []})

    t8 = json.load(open(os.path.join(PT, "mk1a-test-8x100.json")))
    m2 = json.load(open(os.path.join(PT, "mk2-test.json"))) if os.path.exists(os.path.join(PT, "mk2-test.json")) else None
    blocks = ['<h2>Zephyr <em>payload tests</em></h2>',
              '<p>Stored motion of every TNT after charging, frozen before release. Mk1-A: 8 TNT, 100 + 100 charges.</p>',
              F.table(["TNT", "X", "Y", "Z"], [[i + 1, f"{m[0]:.4f}", f"{m[1]:.4f}", f"{m[2]:.4f}"] for i, m in enumerate(t8["motions"])])]
    if m2:
        blocks += [f'<p>Mk2 functional test: {len(m2["motions"])} TNT, {m2["nx"]} + {m2["nz"]} charges, fuses {sorted(set(m2["fuses"]))}.</p>',
                   F.table(["TNT", "X", "Y", "Z"], [[i + 1, f"{m[0]:.4f}", f"{m[1]:.4f}", f"{m[2]:.4f}"] for i, m in enumerate(m2["motions"])])]
    for key, f in [("Mk1-A", "livefire-8x150x120.json"), ("Mk2", "livefire-mk2-64x150x120.json"), ("Mk3", "livefire-mk3-12x150x120.json")]:
        d = json.load(open(os.path.join(PT, f)))
        blocks += [f'<h3>{key} live fire: flight log</h3>',
                   F.table(["tick", "TNT alive", "mean x", "mean y", "mean z"],
                           [[t + 1, len(fr), f"{sum(q[0] for q in fr) / len(fr) - d['S'][0]:.2f}", f"{sum(q[1] for q in fr) / len(fr) - d['S'][1]:.2f}",
                             f"{sum(q[2] for q in fr) / len(fr) - d['S'][2]:.2f}"] for t, fr in enumerate(d["flight"]) if fr and (t < 5 or t % 5 == 0)])]
    ch("d1", "Zephyr test data", "Zephyr data", "#e9b23a", blocks, "Per-TNT motion and flight logs")
    ch("d2", "Ring nuke runs", "Nuke data", "#be185d",
       ['<h2>Every <em>ring test</em></h2>',
        '<p>Each row is one summoned ring payload: ring TNT, expansion TNT, how they were timed, the start height, and '
        'the radius of the ring TNT at detonation (min, median, max). Runs with a booster ring or several groups show a '
        'spread of radii.</p>', F.table(["run", "ring", "exp.", "mode", "start y", "r min", "r med", "r max"], nuke_rows())],
       "All nuke_test.py runs")
    mats = []
    for c in sorted(catalog.values(), key=lambda c: (c["creator"], c["name"])):
        top = ", ".join(f"{k} {v}" for k, v in list(c["counts"].items())[:6])
        mats.append([c["name"][:34], c["creator"], f"{c['blocks']:,}", top])
    ch("d3", "Materials index", "Materials", "#3f9ad6",
       ['<h2>What every <em>cannon is made of</em></h2>',
        '<p>The six most-used blocks of every design in Volume II, from the schematics.</p>',
        F.table(["design", "creator", "blocks", "top materials"], mats)], "Top blocks per design")
    ch("d4", "Glossary", "Glossary", "#4fae6a",
       ['<h2><em>Glossary</em></h2>'] + [f'<p><b>{E(a)}.</b> {E(b)}</p>' for a, b in GLOSSARY], "Terms used in this book")
    vids = video_rows()
    ch("d5", "Every video, in date order", "Video list", "#b88ad9",
       ['<h2>The <em>reading list</em></h2>', f'<p>All {len(vids)} videos in Volume IV, oldest first.</p>',
        F.table(["date", "channel", "title", "id"], vids)], "260 sources")
    ch("d6", "Colophon", "Colophon", "#475569",
       ['<h2>How this book <em>was made</em></h2>',
        '<p>Every page is generated from data. The videos were harvested with yt-dlp (metadata, captions, storyboard frames). '
        'The schematics were fetched from their creators\' links and read with a Litematica parser; renders use my mesher '
        'with Minecraft 26.3\'s own block models and textures, drawn with three.js in headless Chromium; layer plans are '
        'drawn with Pillow. The tests ran on a Paper 26.3 (build 214) server driven over RCON, with a vanilla 26.3 server for '
        'A/B checks. The pages are HTML, paginated in the browser and printed to PDF.</p>',
        '<p>Type: Anton, Instrument Serif, Inter and JetBrains Mono. Everything needed to rebuild it is in the repository: '
        '<code>book/</code>, <code>paper-tests/</code>, <code>tools/</code> and <code>research/</code>.</p>'], "Tools and sources")
    return C
