"""Volume I, The Science. Every number comes from my tests on Paper 26.3 build 214 (and the vanilla
26.3 server used for A/B checks) unless it is credited to a video."""
import json
import math
import os

import svgfig as F
from svgfig import CORAL, CYAN, GOLD, GREEN, INK, MUTE, NAVY, PAPER, PLUM

PT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper-tests")
J = lambda f: json.load(open(os.path.join(PT, f)))
LAB = J("lab-results-paper-26.3-214.json")
RES = J("results-paper-26.3-214-default.json")
TUNED = J("results-paper-26.3-214-tuned.json")
LIN = J("zephyr-linearity.json")
HEI = J("zephyr-launcher-height.json")
CAL = J("zephyr-calibration.json")


def p(*xs):
    return [f"<p>{x}</p>" for x in xs]


# ----------------------------------------------------------------------------- figures
def fig_tickets():
    """Chunk ticket levels around one portal ticket."""
    cell, n = 44, 9
    body = []
    lv = lambda dx, dz: 30 + max(abs(dx), abs(dz))
    cols = {30: CORAL, 31: "#f08a5d", 32: CYAN, 33: "#c9dff2"}
    names = {30: "30 · ticket source", 31: "31 · entity-processing", 32: "32 · lazy: blocks tick, entities frozen", 33: "33 · border: loaded, nothing ticks"}
    for i in range(n):
        for j in range(n):
            l = min(34, lv(i - 4, j - 4))
            if l > 33:
                fill = "#efe6d2"
            else:
                fill = cols[l]
            body.append(F.rect(10 + i * cell, 10 + j * cell, cell, cell, fill, sw=1))
            if l <= 33:
                body.append(F.text(10 + i * cell + cell / 2, 10 + j * cell + cell / 2 + 4, str(l), 12, INK, "middle", 700))
    for k, (l, nm) in enumerate(names.items()):
        body.append(F.rect(430, 30 + k * 34, 22, 22, cols[l]) + F.text(460, 46 + k * 34, nm, 12))
    body.append(F.text(430, 200, "A nether-portal ticket (level 30) loads", 11, MUTE))
    body.append(F.text(430, 216, "a 3×3 entity-processing block; the ring", 11, MUTE))
    body.append(F.text(430, 232, "around it is lazy. /forceload gives 31:", 11, MUTE))
    body.append(F.text(430, 248, "the chunk itself processes, its", 11, MUTE))
    body.append(F.text(430, 264, "neighbours are lazy.", 11, MUTE))
    return F.svg(760, 420, "".join(body))


def fig_intersection():
    """Two loaders, the lazy intersection, payload and propellant."""
    c = 34
    b = []
    for i in range(12):
        for j in range(12):
            a = max(abs(i - 3), abs(j - 3)) <= 1
            bb = max(abs(i - 8), abs(j - 8)) <= 1
            la = max(abs(i - 3), abs(j - 3)) == 2
            lb = max(abs(i - 8), abs(j - 8)) == 2
            fill = "#efe6d2"
            if la or lb:
                fill = "#c9dff2"
            if a or bb:
                fill = "#f08a5d"
            b.append(F.rect(10 + i * c, 10 + j * c, c, c, fill, sw=.8))
    # the lazy intersection: chunks that are in both rings
    for i in range(12):
        for j in range(12):
            if max(abs(i - 3), abs(j - 3)) == 2 and max(abs(i - 8), abs(j - 8)) == 2:
                b.append(F.rect(10 + i * c, 10 + j * c, c, c, CYAN, sw=2.5))
    b.append(F.text(450, 40, "orange: entity-processing (two loaders)", 12))
    b.append(F.text(450, 60, "pale blue: lazy rings", 12))
    b.append(F.text(450, 80, "blue: lazy in BOTH rings: the payload's", 12))
    b.append(F.text(450, 96, "chunk, with processing chunks on its", 12))
    b.append(F.text(450, 112, "sides, where the propellant explodes", 12))
    return F.svg(760, 430, "".join(b))


def fig_knockback():
    pts = [(d["distance"], d["motion_x"]) for d in LAB["knockback_vs_distance"] if d["distance"] >= 1]
    th = [(x / 10, max(0, (1 - x / 10 / 8)) * pts[0][1] / (1 - pts[0][0] / 8)) for x in range(10, 81)]
    return F.chart([("measured, 1 TNT", pts, CORAL), ("(1 − d/8), scaled", th, INK)], "distance from TNT to payload (blocks)",
                   "payload motion added (b/t)", kind="line")


def fig_linearity():
    pts = [(d["tnt"], d["motion_x"]) for d in LAB["linearity"]]
    per = pts[-1][1] / pts[-1][0]
    fit = [(0, 0), (pts[-1][0], pts[-1][0] * per)]
    return F.chart([("measured", pts, CORAL), (f"linear, {per:.4f} b/t per TNT", fit, INK)], "TNT in one batch", "payload motion (b/t)", kind="scatter")


def fig_axis_order():
    W, H = 760, 330
    b = [F.arrowhead_defs(CORAL, "a1"), F.arrowhead_defs(CYAN, "a2")]
    gx, gy, s = 40, 40, 22

    def grid(ox, title, legs, block, caption):
        o = [F.text(ox, 26, title, 12, INK, "start", 700)]
        for i in range(12):
            for j in range(11):
                o.append(F.rect(ox + i * s, gy + j * s, s, s, "#fffaf0", "#d8ccb4", .6))
        if block:
            o.append(F.rect(ox + block[0] * s, gy + block[1] * s, s, s, INK))
        for (x1, y1, x2, y2, col, mk) in legs:
            o.append(F.line(ox + x1 * s + s / 2, gy + y1 * s + s / 2, ox + x2 * s + s / 2, gy + y2 * s + s / 2, col, 3.5, arrow=mk))
        o.append(F.text(ox, gy + 11 * s + 18, caption, 11, MUTE))
        return "".join(o)
    b.append(grid(20, "|X| = |Z| = 9: X moves first", [(1, 9, 5, 9, CORAL, "a1")], (6, 9), "a block on the X leg stops X at 4.01;"))
    b.append(F.text(20, gy + 11 * s + 32, "Z then moves its full 9 from there", 11, MUTE))
    b.append(F.line(20 + 5 * s + s / 2, gy + 9 * s + s / 2, 20 + 5 * s + s / 2, gy + 0 * s + s / 2, CYAN, 3.5, arrow="a2"))
    b.append(grid(400, "|Z| > |X|: Z moves first", [(1, 9, 1, 5, CYAN, "a2"), (1, 5, 9, 5, CORAL, "a1")], (1, 4), "a block on the Z leg stops Z at 4.01;"))
    b.append(F.text(400, gy + 11 * s + 32, "X still moves its full 8", 11, MUTE))
    return F.svg(W, H, "".join(b))


def fig_stasis():
    c = RES["lazy_stasis"]["charges"]
    pts = [(x["after_shot"], x["payload_motion"][0]) for x in c]
    rel = RES["lazy_stasis"]["release"]["pos_per_tick"]
    x0 = RES["lazy_stasis"]["release"]["pos_before"][0]
    pts2 = [(i + 1, q[0] - x0) for i, q in enumerate(rel)]
    a = F.chart([("stored motion while frozen", pts, CORAL)], "charges fired into the lazy chunk", "payload motion X (b/t)", w=360, h=300, kind="line")
    b2 = F.chart([("distance after release", pts2, CYAN)], "ticks after release", "blocks travelled", w=360, h=300, kind="line")
    return f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">{a}{b2}</div>'


def fig_brake():
    ctrl = RES["powder_snow"]["cases"]["control (no snow)"]
    snow = RES["powder_snow"]["cases"]["powder snow at +5"]
    x0 = ctrl[0]["pos"][0]
    s1 = [(i, q["pos"][0] - x0) for i, q in enumerate(ctrl)]
    s2 = [(i, q["pos"][0] - x0) for i, q in enumerate(snow)]
    return F.chart([("no snow: flies on", s1, INK), ("powder snow 5 blocks ahead: stops", s2, CYAN)], "tick", "distance (blocks)", kind="line", h=320)


def fig_windburst():
    W, H = 760, 300
    s = 70
    b = [F.arrowhead_defs(CORAL, "w1")]
    ox, oy = 120, 40
    # side view: W cell, S cell; launcher above W
    b.append(F.rect(ox, oy, s, s, "#9aa3ad"))                                     # launcher
    b.append(F.text(ox + s / 2, oy + s / 2 + 4, "X launcher", 10, "#fff", "middle", 700))
    b.append(F.rect(ox, oy + s, s, s, "#fffaf0", "#b9ad95", 1))                  # W cell
    b.append(F.rect(ox + s, oy + s, s, s, "#e7f3fb", "#b9ad95", 1))              # S cell (snow)
    b.append(F.rect(ox, oy + 2 * s, 2 * s, s * .25, "#7d7a74"))                  # floor
    b.append(F.text(ox + s * 1.5, oy + s + 14, "S: powder snow", 10, INK, "middle"))
    b.append(F.text(ox + s / 2, oy + s + 14, "W cell", 10, INK, "middle"))
    bx, by = ox + s / 2, oy + 2 * s - .25 * s
    b.append(F.line(bx, oy + s + 18, bx, by - 6, INK, 2, "4 3"))
    b.append(f'<circle cx="{bx}" cy="{by}" r="9" fill="{GOLD}" stroke="{INK}"/>')
    b.append(F.text(bx - 14, by + 4, "burst", 10, INK, "end", 700))
    px, py = ox + 1.5 * s, oy + 2 * s - s * .49
    b.append(F.rect(px - s * .49, py - s * .49, s * .98, s * .98, CORAL, INK, 1.5, .85))
    b.append(F.text(px, py + 4, "TNT", 11, "#fff", "middle", 700))
    b.append(F.line(bx + 12, by, px - s * .3, py, CORAL, 3, arrow="w1"))
    b.append(F.text(ox + 2 * s + 30, oy + 30, "The charge falls through the W cell and bursts", 12))
    b.append(F.text(ox + 2 * s + 30, oy + 48, "0.25 above the floor it hits. The push on the", 12))
    b.append(F.text(ox + 2 * s + 30, oy + 66, "frozen payload points from the burst centre to", 12))
    b.append(F.text(ox + 2 * s + 30, oy + 84, "the TNT's feet: mostly +X, a little down.", 12))
    b.append(F.text(ox + 2 * s + 30, oy + 118, "Zephyr core, measured per charge:", 12, INK, "start", 700))
    b.append(F.text(ox + 2 * s + 30, oy + 138, "X +0.6738   Y −0.1700   Z ≈ 0", 13, CORAL, "start", 700))
    return F.svg(W, H, "".join(b))


def fig_zlin():
    pts = [(int(k), v[0]) for k, v in LIN.items()]
    fit = [(0, 0), (300, 300 * pts[1][1] / 100)]
    return F.chart([("measured X motion", pts, CORAL), ("linear through 100", fit, INK)], "wind charges fired", "payload motion X (b/t)", kind="scatter", h=320)


def fig_height():
    items = []
    for k, runs in sorted(HEI.items()):
        xs = [r[0] for r in runs]
        m = sum(xs) / len(xs)
        sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** .5
        items.append((f"launcher at Y+{k}", sd / m * 100, CYAN if k == "1" else CORAL))
    return F.bars(items, "run-to-run spread of 100-charge motion (% of mean)", fmtv=lambda v: f"{v:.2f}%")


def fig_tnt_hop():
    ys = [0.0, 0.02, -0.02, -0.10, -0.22, -0.25, -0.25, -0.25]
    ys2 = [0.0, 0.02, 0.0, 0.0, 0.0, 0.0]
    return F.chart([("enchanting-table floor (top at −0.25)", list(enumerate(ys)), CORAL), ("full-block floor", list(enumerate(ys2)), CYAN)],
                   "ticks after the TNT is dispensed", "height (blocks)", kind="line", ylim=(-.3, .05), h=300)


def fig_drill():
    items = [("8 TNT, equal fuses", 236), ("64 TNT, equal fuses", 357), ("10 TNT, 4 ticks apart", 385), ("12 TNT, 4 ticks apart", 471),
             ("16 TNT, 4 ticks apart", 647), ("20 TNT, 4 ticks apart", 825), ("64 TNT, 1 tick apart", 1441)]
    return F.bars([(a, v, CYAN if "apart" in a else CORAL) for a, v in items], "stone blocks destroyed in a 31×31×20 block")


def fig_ring_radius():
    seq = [(1, 39.3), (3, 69.1), (5, 90.2), (7, 90.2), (9, 90.2)]
    pairs = [(4, 31.9), (6, 48.1), (10, 59.5)]
    pairs_h = [(10, 109.6), (14, 113.5), (20, 113.5)]
    return F.chart([("one per tick", seq, CORAL), ("pairs, 25 blocks up", pairs, MUTE), ("pairs, 70 blocks up", pairs_h, CYAN)],
                   "expansion TNT", "ring radius at detonation (blocks)", kind="line", h=320, hlines=[(186, "cubicmetre Mk.6 max (radius 186)", INK)])


def fig_free_flight():
    ff = LAB["free_flight"]
    x0 = ff[0]["pos"][0] - ff[0]["motion"][0] / .98
    pts = [(f["tick"], f["pos"][0] - x0) for f in ff]
    v = [(f["tick"], f["motion"][0]) for f in ff]
    a = F.chart([("distance", pts, CORAL)], "tick", "blocks", w=360, h=280)
    b = F.chart([("speed", v, CYAN)], "tick", "speed (b/t)", w=360, h=280)
    return f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">{a}{b}</div>'


def fig_range_cost():
    rc = LAB["range_cost"]
    return F.bars([(f"{r['tnt']:,} TNT", r["flight_blocks"], CORAL) for r in rc], "blocks flown in the single release tick", fmtv=lambda v: f"{v:,.0f}")


def fig_tnt_per_tick():
    d = RES["max_tnt_per_tick"]["tnt_alive_per_tick"]
    t = TUNED["max_tnt_per_tick"]["tnt_alive_per_tick"]
    return F.chart([("Paper default (max-tnt-per-tick 100)", list(enumerate(d)), CORAL), ("tuned (-1, unlimited)", list(enumerate(t)), CYAN)],
                   "tick", "primed TNT still alive (of 300, fuse 1)", kind="step", h=300)


def fig_qc():
    W, H, s = 760, 300, 64
    b = [F.arrowhead_defs(CORAL, "q1")]
    ox, oy = 60, 50
    cells = {(0, 1): ("piston\n(stager)", "#a58f6b"), (1, 1): ("W cell", "#fffaf0"), (1, 0): ("X\nlauncher", "#9aa3ad"),
             (0, 0): ("space above\nthe piston", "#ffe2d6"), (1, 2): ("floor", "#7d7a74"), (2, 1): ("payload", "#e7f3fb")}
    for (i, j), (lab, col) in cells.items():
        b.append(F.rect(ox + i * s, oy + j * s, s, s, col))
        for k, part in enumerate(lab.split("\n")):
            b.append(F.text(ox + i * s + s / 2, oy + j * s + s / 2 + k * 12 - 2, part, 10, INK, "middle", 700))
    b.append(F.line(ox + 2.6 * s, oy + .2 * s, ox + 1.9 * s, oy + .45 * s, CORAL, 3, arrow="q1"))
    b.append(F.text(ox + 2.65 * s, oy + .2 * s, "repeater powers the launcher", 11, CORAL, "start", 700))
    b.append(F.line(ox + 1 * s, oy + .5 * s, ox + .75 * s, oy + .5 * s, CORAL, 3, arrow="q1"))
    tx = 330
    for k, line in enumerate(["Quasi-connectivity: a piston also counts as powered",
                              "when the space ABOVE it is powered. A powered",
                              "dispenser beside that space powers it. The piston",
                              "only notices on its next block update, so it fired",
                              "at random-looking moments and held its head in the",
                              "W cell for the whole launch: every X charge burst",
                              "on it. Fix: fire the launcher by powering the air",
                              "above IT (its own quasi-connectivity), so the",
                              "dispenser itself is never a powered block."]):
        b.append(F.text(tx, 60 + k * 19, line, 12))
    return F.svg(W, H, "".join(b))


# ----------------------------------------------------------------------------- chapters
def chapters():
    C = []

    def ch(id_, title, short, color, kicker, dek, facts, blocks):
        C.append({"id": id_, "no": len(C) + 1, "title": title, "short": short, "color": color, "kicker": kicker,
                  "dek": dek, "facts": facts, "blocks": blocks})

    kb = LAB["knockback_vs_distance"]
    per_tnt = LAB["linearity"][-1]["per_tnt"]
    ch("s1", "What an orbital strike cannon is", "The idea", CORAL, "Chapter one",
       "A machine that stores velocity, then spends it all in one tick.",
       [("blocks in one tick (my test)", "4,436"), ("first OSC", "2023"), ("videos studied", "260")],
       ['<h2>Stored <em>velocity</em></h2>'] +
       ['<p class="lead">An orbital strike cannon throws a payload of TNT anywhere in a Minecraft world, thousands of '
        'blocks away, accurate to a block or two, and it does it in a single game tick. The trick is not a bigger '
        'explosion. It is a place in the world where an entity can be pushed without moving.</p>'] +
       p('That place is a <b>lazy chunk</b>: loaded, but too far from any chunk loader for its entities to be processed. '
         'An entity there keeps every push it receives in its velocity, frozen, the way a spring holds energy. An orbital '
         'strike cannon parks its payload in such a chunk and explodes propellant beside it, in a neighbouring chunk that '
         'is fully processed. Explosion after explosion, the payload\'s stored velocity grows. Then the cannon loads the '
         'payload\'s chunk, and the payload moves its whole velocity in one tick.',
         'That one tick is the whole flight. My Paper test moved a payload 4,436 blocks between one tick and the next, '
         'and nothing in between was simulated: the game swept the entity\'s box along its path, checked for collisions '
         'and set its new position. To the world, the payload simply appears at the target. Then something has to stop '
         'it there, or it keeps going, and that is the job of the powder-snow brake (chapter seven).',
         'cubicmetre published the first orbital strike cannon in 2023. Every design in this book, his and everyone '
         'else\'s, including my own Zephyr series, is a variation on the same three parts: a way to keep the payload '
         'frozen while it is charged, a way to charge it with exactly the right velocity, and a way to release and stop it.') +
       ['<div class="pull"><div>Not a bigger explosion: a place where an entity can be pushed without moving.</div><small>The principle</small></div>'] +
       p('The rest of this volume takes those parts apart. Chapters two and three are about chunk loading and stasis, '
         'four about how an entity moves in one huge step, five and six about the two propellants (TNT and wind charges), '
         'seven about the brake. Eight and nine cover handling TNT and the redstone traps that cost me days, ten covers '
         'Paper against vanilla, eleven fire control, and twelve to fourteen what the payload does when it arrives.',
         'A note on method. I did not take any of this on trust. Each claim in this volume was either measured on my own '
         'Paper 26.3 server (build 214), with a test script you can rerun from <code>paper-tests/</code>, or is credited to '
         'the video it came from. Where Paper and vanilla could differ, I ran both.') +
       ['<h3>The three parts in this book\'s designs</h3>',
        F.table(["part", "cubicmetre Mk.6", "Zephyr Mk2 (mine)"],
                [["stasis", "two portal loaders, lazy intersection", "force-loaded W/N/NW chunks, lazy payload chunk"],
                 ["charge", "duped TNT, two-stage acceleration", "wind charges from two dispensers"],
                 ["release & stop", "chunk load + powder snow", "chunk load + powder snow"],
                 ["aim", "55-bit instruction, ROM, wireless", "count of wind charges per axis"]])])

    ch("s2", "Chunk loading and tickets", "Chunk loading", "#d4572f", "Chapter two",
       "Why some loaded chunks process entities and others do not.",
       [("entity-processing level", "≤ 31"), ("lazy level", "32"), ("portal ticket", "3×3")],
       ['<h2>Levels, <em>not on/off</em></h2>',
        '<p class="lead">A chunk is not simply loaded or unloaded. The server gives every loaded chunk a level, set by '
        'the nearest "ticket" that holds it, and the level decides what runs there.</p>'] +
       p('A ticket has a source level, and its influence weakens by one per chunk of distance. Level 31 or lower means '
         'entity-processing: blocks, redstone and entities all tick. Level 32 is the lazy ring: redstone and scheduled '
         'block ticks still run, but entities are not ticked at all. Level 33 is the border: the chunk is loaded and can be '
         'read, but nothing in it runs.',
         'A nether-portal ticket is the classic orbital-cannon loader. An item passing through a portal leaves a ticket of '
         'level 30 on the destination chunk, so that chunk and its eight neighbours (the 3×3 block) are entity-processing, '
         'and the ring around them is lazy. <code>/forceload</code>, which my tests use instead, gives level 31 to the '
         'chunk itself: it processes, and its neighbours are lazy.') +
       [F.fig(fig_tickets(), "Ticket levels around one nether-portal ticket. My portal test sent an item through and probed "
              "the overworld chunks: the ticket chunk and the next were entity-ticking, and the chunk two over was frozen, "
              "where a knockback probe stored motion 0.687 without moving.", "Fig. 2.1")] +
       p('The orbital strike cannon needs both kinds of chunk side by side: a lazy one for the payload and a processing one '
         'right next to it for the propellant. cubicmetre\'s cannons get this from the intersection of two portal loaders, '
         'whose processed squares and lazy rings overlap. In the right corner of that pattern, one lazy chunk has '
         'processing chunks on two sides, so explosions from two directions can reach the payload.') +
       [F.fig(fig_intersection(), "Two portal loaders. Where their lazy rings cross, a payload chunk can be pushed from "
              "two directions by propellant in processing chunks, which gives full 2-D aim.", "Fig. 2.2")] +
       p('My Zephyr cannons use the simplest arrangement that gives two directions: three force-loaded chunks (west, north '
         'and north-west of the payload chunk) and nothing else. The payload chunk is lazy because it borders force-loaded '
         'chunks without being one. To release, I force-load the payload chunk too. In survival, that last step would be a '
         'portal or a player arriving.') +
       ['<div class="note"><b>Checked on Paper 26.3</b><p>Portal tickets behave as in vanilla. An item sent through a portal '
        'loaded the overworld side (it was unloaded before), its chunk and the next were entity-ticking, and the chunk two '
        'away was frozen.</p></div>'])

    ch("s3", "Stasis: charging a frozen payload", "Stasis", "#c2410c", "Chapter three",
       "In a lazy chunk, velocity accumulates and nothing moves.",
       [("motion per test shot", "0.6248"), ("after 3 shots", "1.8744"), ("fuse while frozen", "unchanged")],
       ['<h2>Pushed, <em>but not moving</em></h2>',
        '<p class="lead">An entity in a lazy chunk is not ticked. Explosions next to it still change its velocity, '
        'because knockback is applied by the explosion, not by the entity\'s own tick. So the velocity grows and the '
        'position stays put.</p>'] +
       p('My stasis test parked a primed TNT with fuse 200 in a lazy chunk and fired three identical charges at it from '
         'a processing chunk. After each charge the stored motion went up by exactly the same amount, 0.6248 blocks per tick, '
         'while its position and its fuse did not change at all. Then the chunk was loaded and the TNT moved off at the '
         'stored speed.') +
       [F.fig(fig_stasis(), "Left: stored X motion after each charge, perfectly additive. Right: distance moved per tick after "
              "the chunk is loaded. Drag (×0.98 per tick) starts only once it moves.", "Fig. 3.1")] +
       p('Three properties make stasis useful. The pushes add exactly, with no loss, so the charge is a simple sum. The '
         'fuse is frozen too, so a TNT payload can wait for as long as charging takes. And nothing moves, so the propellant '
         'always sees the payload in the same place: the hundredth charge pushes exactly like the first.',
         'The same physics is a trap. When a payload is released, it carries everything it stored. If a cannon\'s chunks '
         'unload and reload mid-charge, the payload loses its velocity (velocities are not saved above 10 blocks per tick, '
         'chapter four) or is released early, and cubicmetre\'s Mk.4 notes warn that this can blow up the cannon itself.') +
       ['<div class="pull"><div>The hundredth charge pushes exactly like the first.</div><small>Why stasis works</small></div>'])

    ch("s4", "Moving in one step", "Movement", "#9a3412", "Chapter four",
       "Y first, then the larger of X and Z: the order that decides where a payload ends up.",
       [("axis order", "Y → max(X,Z)"), ("ties go to", "X"), ("NBT clamp above", "10 b/t")],
       ['<h2>Three moves, <em>in order</em></h2>',
        '<p class="lead">When an entity moves, the game does not slide it along a straight line. It moves it one axis at a '
        'time: Y first, then whichever of X and Z is larger, then the other. Each step is stopped by the first block in its way.</p>'] +
       p('For a walking mob this hardly matters. For a payload moving thousands of blocks in one tick it decides '
         'everything. A payload leaving its cannon travels the full length of its first axis before the second axis '
         'starts, so the path is an L, not a diagonal, and anything standing on either leg of the L stops it.') +
       [F.fig(fig_axis_order(), "From my axis-order tests (motion 9 or 8 per axis, a stone block placed on one leg). With "
              "|X| = |Z| the X leg goes first; with |Z| > |X| the Z leg goes first. A blocked leg stops at 4.01, the other "
              "still moves its full distance.", "Fig. 4.1")] +
       F.table(["case", "motion", "block", "moved"],
               [[k, str(v["motion"]), str(v["block"] or "—"), str([round(d, 2) for d in v["delta"]])] for k, v in RES["axis_order"]["cases"].items()]) +
       p('Two consequences shape cannon design. First, Y moves before X and Z, and the cannon\'s own floor is right under '
         'the payload, so any downward velocity is cancelled by that floor (TheeDumbRock\'s MOSC notes this, and my Zephyr '
         'shots confirm it). The payload leaves level and falls afterwards. Second, the first horizontal leg leaves along a '
         'cardinal axis, so a cannon only needs a clear lane along one direction out of the barrel, not a clear diagonal.',
         'The last row of the table is the speed limit. An entity loaded from disk with a motion component above 10 blocks '
         'per tick has that component zeroed. cubicmetre ran into the same clamp on chunk load in his nuke, where '
         'falling TNT passed 10 blocks per tick downward and its cone of TNT flattened into a ring. Stored velocities above '
         '10 are safe only while the chunk stays loaded.') +
       ['<h3>How far can one tick go?</h3>'] +
       p('In vanilla, a long one-tick move is expensive: the game collects block shapes over the whole volume the entity\'s '
         'box sweeps, so the cost grows with the cube of the distance. cubicmetre measured a single 13-second tick for 171 '
         'TNT flying 100 blocks. Paper does not have that blow-up. My 6,000-TNT test moved its payload 4,436 blocks in one '
         'tick, and the server stepped that tick in about 0.2 seconds of wall time.') +
       [F.fig(fig_range_cost(), "Range against propellant in my lazy-launch test (0.7393 blocks of flight per TNT). Every one "
              "of these was a single release tick on Paper 26.3.", "Fig. 4.2"),
        F.fig(fig_free_flight(), "After the release tick, a free payload coasts with drag 0.98 per tick: 40 ticks of a test "
              "flight with no brake.", "Fig. 4.3")])

    ch("s5", "TNT as propellant", "TNT", "#7c2d12", "Chapter five",
       "How hard an explosion pushes, and why a cannon's response is linear.",
       [("push at 1 block", f"{kb[1]['motion_x']:.3f}"), ("per TNT in a batch", f"{per_tnt:.4f}"), ("falls to zero at", "8 blocks")],
       ['<h2>Distance, <em>exposure</em>, linearity</h2>',
        '<p class="lead">An exploding TNT pushes every entity within 8 blocks. The push points from the explosion centre '
        'to the entity and is roughly proportional to (1 − d/8), scaled by how much of the entity the explosion can see.</p>'] +
       p('I measured it directly: one TNT at increasing distances from a frozen payload, recording the motion it added. '
         'The curve follows (1 − d/8) closely. At half a block the push came out as zero: the propellant was overlapping '
         'the payload, so the direction was undefined.') +
       [F.fig(fig_knockback(), "Push from one TNT against distance, measured on a frozen payload, with the (1 − d/8) law scaled "
              "to the 1-block point.", "Fig. 5.1"),
        F.fig(fig_linearity(), f"TNT exploding together add up: {LAB['linearity'][-1]['tnt']} TNT gave {LAB['linearity'][-1]['motion_x']:.2f} b/t, "
              f"{per_tnt:.4f} per TNT. That linearity is what makes aiming a matter of counting.", "Fig. 5.2")] +
       p('Two details from cubicmetre\'s work matter here. An explosion is centred a little above the TNT\'s feet '
         '(I measured 0.0625 blocks, the TNT\'s explosion height). So a payload level with the propellant gets a slight '
         'downward push, and his Mk.4 used stonecutters to raise the TNT so the centre sat at the payload\'s height. '
         'And because the push is linear in the number of TNT, a cannon can be calibrated once per axis: fire a known count, '
         'measure the motion, and every other count is a multiplication.',
         'cubicmetre\'s cannons go one step further and make each axis independent with two-stage acceleration (from the '
         'Hellstorm cannon), so the aiming maths is a pair of separate multiplications rather than a 2×2 matrix. In my own '
         'TNT test the cross-coupling was zero to the precision I measured: the calibration matrix was diagonal, 0.7393 '
         'blocks of flight per TNT on each axis.') +
       [F.table(["calibration", "value"],
                [["blocks per TNT (X, Z)", "0.7393, 0.7393"], ["target", "150, 90"], ["solved TNT (X, Z)", "203, 122"],
                 ["error after firing", f"{LAB['calibration']['error_blocks'][0]:.2f}, {LAB['calibration']['error_blocks'][1]:.2f} blocks"]])])

    ch("s6", "Wind charges", "Wind charges", "#2c7a7b", "Chapter six",
       "A cleaner propellant: no fuse, no duper, one item per push.",
       [("per charge, X", "0.6738"), ("downward part", "−0.170"), ("repeatability", "0.37%")],
       ['<h2>The breeze\'s <em>gift</em></h2>',
        '<p class="lead">A wind charge is a projectile that bursts on impact and knocks entities away from the burst. '
        'Fired straight down from a dispenser onto a floor next to a frozen payload, it is a precise, repeatable push '
        'that needs no TNT duper.</p>'] +
       p('The burst happens 0.25 blocks above the surface the charge hits. That one fact sets the geometry of every '
         'wind-charge cannon in this book. In my Zephyr core the X launcher drops its charges into the cell west of the '
         'payload, they burst just above that cell\'s floor, and the frozen TNT next door is pushed east and slightly down.') +
       [F.fig(fig_windburst(), "Zephyr core, side view. The burst centre sits 0.25 above the W cell's floor; the push on the "
              "payload points from the burst to the TNT's feet.", "Fig. 6.1"),
        F.fig(fig_zlin(), "Linearity of the wind-charge push in the Zephyr core: 50, 100, 200 and 300 charges. 100 charges "
              f"gave {LIN['100'][0]:.2f} b/t of X motion.", "Fig. 6.2")] +
       p('The push is not quite independent of the launcher. Mounting the X launcher two blocks above the cell instead '
         'of one made the result noisier from run to run, because the charge had further to fall and could drift. One block '
         'up gave 0.37% run-to-run spread on 100 charges; two blocks up gave about 1%.') +
       [F.fig(fig_height(), "Run-to-run spread of the push from 100 charges, launcher one or two blocks above the cell "
              "(three runs each).", "Fig. 6.3")] +
       p('There is a catch that took me a long time to find. The push depends on where the payload sits to within a hundredth '
         'of a block. A TNT pressed against one wall of its 1-block channel (z = 0.49 instead of 0.51) is pushed 0.6% '
         'differently along that axis, which over a 117-block shot is half a block. That does not matter for a payload '
         'that detonates all at once. It ruins a drill, whose TNT must land exactly together (chapter twelve).',
         'One version warning. cubicmetre\'s anti-air cannon, which depends on wind charges and arrows passing a trapdoor, '
         'broke in 1.21.9, was fixed, and broke again in 1.21.11. 26.3 is after that change, so wind-charge contraptions '
         'should be re-tested on every version.'))

    ch("s7", "The powder-snow brake", "The brake", "#3f9ad6", "Chapter seven",
       "How a payload moving thousands of blocks per tick stops dead.",
       [("brake factors", "0.9 / 1.5 / 0.9"), ("arms when", "moving in"), ("Paper = vanilla", "bit-identical")],
       ['<h2>Stuck <em>in the snow</em></h2>',
        '<p class="lead">Powder snow slows anything that moves into it. Inside an entity\'s move, that slowing is applied '
        'as a one-time multiplier on the next move, and then the entity\'s velocity is set to zero. Exploited correctly, '
        'it stops a payload dead after exactly one more move.</p>'] +
       p('My control test fired a TNT at 4.9 blocks per tick down a corridor: it coasted on, losing 2% a tick. With powder '
         'snow five blocks ahead, it moved 4.41 blocks on the first tick into the snow and then stopped completely, motion '
         'zero, for good.') +
       [F.fig(fig_brake(), "A payload at 4.9 b/t, with and without powder snow ahead. With snow it stops on the spot.", "Fig. 7.1")] +
       p('For a cannon, the brake has to be armed before the release, while the payload sits frozen in the lazy chunk. '
         'Then on release it moves exactly 0.9 of its stored X and Z velocity and 1.5 of its Y, and stops: the stopping '
         'point is a multiplication, not a ballistic curve. cubicmetre credits the trick to Cayman.',
         'The arming rule is where my tests disagree with folklore. <b>An entity that merely starts inside powder snow is '
         'not braked.</b> It has to <i>move into</i> the snow during a tick in which it is processed. TNT dispensed straight '
         'into snow inside a lazy chunk never moved in, so on 26.3 it flies on with its full velocity. That is why '
         'TheeDumbRock\'s MOSC overshot on my server, on Paper and on vanilla alike.') +
       ['<div class="note"><b>Border-drift arming</b><p>Put the snow in the first block column of the lazy chunk and let '
        'the payload drift or be pushed across the chunk border into it. It moves in while still processed, which arms the '
        'brake, and freezes in the same tick. On release it moves 0.9·vx, 1.5·vy, 0.9·vz and stops. Paper and vanilla gave '
        'bit-identical results (49616.19 → 49680.218 for v = 71.142).</p></div>'] +
       p('Every Zephyr cannon arms its brake this way. A piston pushes each TNT from the processing chunk across the border '
         'into the snow cell, and the push counts as the move. cubicmetre\'s cannons do the same with a flying machine. '
         'Anvils are an exception: falling blocks treat powder snow as solid and need their own alignment.'))

    ch("s8", "Handling TNT", "TNT handling", "#b45309", "Chapter eight",
       "Dispensers, hops, fuses, and getting every TNT into the cell the same way.",
       [("dispenser rate", "1 per 4 ticks"), ("prime hop", "0.2 up"), ("fuse", "80 ticks")],
       ['<h2>The small <em>random</em> things</h2>',
        '<p class="lead">A dispensed TNT is not placed neatly. It appears at the centre of the cell in front of the '
        'dispenser with an upward hop of 0.2 blocks per tick and a random sideways drift of 0.02, and its fuse starts at 80.</p>'] +
       p('A dispenser fires at most once every 4 game ticks, however fast it is pulsed. That is the speed limit on feeding, '
         'and it matters because a TNT\'s fuse burns while it waits in a processing chunk. In my first automatic cannon '
         'every TNT waited in the loading cell until all of them had arrived, and the fuses came out spread 12 ticks apart. '
         'With 4 TNT the first had only 3 ticks of fuse left.',
         'The hop and drift matter for staging, the push from the loading cell into the frozen cell. Pushed in mid-hop, a '
         'TNT freezes at the wrong height and gets a different push from every charge. So the stager has to wait until it '
         'lands. On my enchanting-table floors (top at 0.75) that took 4 ticks. With full-block floors the launcher above '
         'the cell acts as a ceiling, the hop is cut to 0.02, and the TNT is down in 2 ticks.') +
       [F.fig(fig_tnt_hop(), "Height of a freshly dispensed TNT in the Zephyr loading cell. Full-block floors let the stager "
              "push it 2 ticks after it appears.", "Fig. 8.1")] +
       p('Paper adds one more limit: by default it explodes at most 100 TNT per tick (<code>max-tnt-per-tick</code>, a Spigot '
         'setting) and delays the rest. For a payload that must detonate together, set it to -1.') +
       [F.fig(fig_tnt_per_tick(), "300 TNT primed with fuse 1. Default Paper explodes them over 3 ticks; with the limit "
              "removed, all on the first.", "Fig. 8.2")] +
       p('Finally, the order of explosions in the same tick follows the order the TNT were spawned. cubicmetre\'s stab '
         'charges depend on it: the batch spawned first must have the longer fuse. My test confirmed it. With the long-fuse '
         'batch spawned first, the short-fuse batch exploded under it and drove it down at 1.93 blocks per tick. Spawned the '
         'other way round, it barely moved.'))

    ch("s9", "Redstone traps on 26.3", "Redstone", "#5b2a6e", "Chapter nine",
       "Everything that made my controller misbehave, and the rule behind each.",
       [("repeater delay 1", "= 2 game ticks"), ("comparator ignores", "2-tick pulses"), ("bugs found", "9")],
       ['<h2>The traps, <em>one by one</em></h2>',
        '<p class="lead">My automatic cannon\'s redstone is small, and it still produced nine separate bugs. Each one came '
        'from a rule I half-knew. Here they are as rules, with the symptom each one caused.</p>',
        '<h3>Timing</h3>'] +
       p('<b>Repeater delay counts redstone ticks.</b> <code>delay=4</code> is 8 game ticks, not 4. Every timing I first '
         'computed for the stager was off by a factor of two.',
         '<b>A comparator ignores 2-tick pulses.</b> It re-checks its input 2 game ticks after a change, by which time an '
         'observer\'s pulse is gone. A copper bulb in front, toggled by each pulse, turns them into a square wave the '
         'comparator can read.',
         '<b>A copper bulb\'s <code>powered</code> flag flips on both edges</b> of its input, even though its light only '
         'toggles on the rising edge. An observer watching the bulb fires twice per toggle; one watching a comparator that '
         'reads the bulb fires once.') +
       ['<h3>Connections</h3>'] +
       p('<b>Dust connects diagonally across a one-block step.</b> Stage dust one block up and over from the delay line '
         'joined them, and every stage pulse fed back into the line: observer and line became a 12-tick clock that '
         'fired the stager right through the launch. Use a repeater wherever two lines pass diagonally.',
         '<b>Dust strongly powers the block it sits on.</b> A concrete support under the launch staircase sat next to stage '
         'dust and fed it, so the stager fired on every launch pulse. Supports that touch other circuitry should be glass.',
         '<b>Dust on glass passes signal up a step, never down one.</b> My first glass-supported staircase carried nothing '
         'downwards and the stager never fired. Step-down supports must be solid.') +
       [F.fig(fig_qc(), "Quasi-connectivity, the hardest of the nine.", "Fig. 9.1")] +
       ['<h3>State</h3>'] +
       p('<b>Pistons and dispensers are quasi-connected and update-driven.</b> They count as powered when the block above '
         'them is, but they only check when something updates them, which makes the symptom look random (figure 9.1).',
         '<b>A comparator or repeater\'s <code>facing</code> points toward its input.</b> In block-state terms the arrow '
         'is backwards, and every layout I wrote by coordinates had to account for it.',
         '<b>Pasting with <code>setblock … strict</code> leaves stale scheduled ticks</b>: an observer pair can sit there '
         'without oscillating until a real block update kicks it. And a lever placed by command does not update what it '
         'powers; remove and re-place it to make it count.') +
       ['<div class="note"><b>One more, not redstone</b><p>My delay chain needs about 50 game ticks to settle after the '
        'feeder is loaded. Arming the cannon sooner let one launch pulse through before the lock engaged.</p></div>'])

    ch("s10", "Paper against vanilla", "Paper", "#e9b23a", "Chapter ten",
       "What Paper changes, what it does not, and the settings an OSC needs.",
       [("server", "Paper 26.3 #214"), ("A/B server", "vanilla 26.3"), ("one-tick 4,436 blocks", "~0.2 s")],
       ['<h2>Same physics, <em>different defaults</em></h2>',
        '<p class="lead">Paper is a performance fork of the Minecraft server, and most large servers run it. cubicmetre '
        'says his cannons do not work on Paper, and Mk.6 indeed did not fire on mine. But the physics an OSC needs is '
        'the same: every mechanic I tested on both servers gave identical results on Paper and on vanilla 26.3.</p>'] +
       p('What differs is defaults and limits. Paper caps explosions per tick, can delay chunk unloads, disables piston '
         'duplication of TNT, and times out slow ticks. None of that is physics, all of it is configuration, and all of it '
         'can stop a cannon. These are the settings my server used, the same set Biquaternions published for running OSCs '
         'on Paper:') +
       [F.table(["file", "setting", "value", "why"],
                [["spigot.yml", "max-tnt-per-tick", "-1", "payload must explode in one tick"],
                 ["spigot.yml", "timeout-time", "600", "long charging ticks are not crashes"],
                 ["paper-global.yml", "allow-piston-duplication", "true", "TNT dupers"],
                 ["paper-world-defaults.yml", "delay-chunk-unloads-by", "0s", "chunk states change exactly when expected"]])] +
       p('Paper also changes how fast long moves are computed. In vanilla a long one-tick move costs the cube of its length; '
         'on Paper my 4,436-block release stepped in about 0.2 seconds of wall time. For a large-range cannon that is the '
         'difference between a lag spike and a frozen server.',
         'The vanilla A/B checks were deliberate. The mechanics I ran on both servers, the brake and its arming rule '
         'among them, gave the same numbers, in the brake\'s case to the last digit. So a cannon built from these mechanics on Paper should work in '
         'vanilla, with the caveat that I only live-fired on Paper.'))

    ch("s11", "Fire control", "Fire control", "#2563eb", "Chapter eleven",
       "Turning a target into counts of propellant.",
       [("Mk.6 instruction", "55 bits"), ("Zephyr", "2 numbers"), ("my best miss", "0.55 blocks")],
       ['<h2>From target to <em>counts</em></h2>',
        '<p class="lead">Because the push is linear, aiming is arithmetic: the stopping point is the release point plus '
        'the stored velocity times the brake factors, and the stored velocity is the propellant count times the push per unit.</p>'] +
       p('For a Zephyr cannon the whole fire-control problem is two divisions:') +
       ['<div class="note"><b>Zephyr fire control</b><p>Δx = 0.9 · n<sub>X</sub> · 0.6738 &nbsp;&nbsp; Δz = 0.9 · n<sub>Z</sub> · 0.6725<br>'
        'so n<sub>X</sub> = Δx / 0.6064 and n<sub>Z</sub> = Δz / 0.6053, rounded. Y does not move at release (the floor '
        'blocks it); the payload falls from the cannon\'s height, which must be low enough that it lands before the fuse ends.</p></div>'] +
       p('cubicmetre\'s Mk.6 needs much more, because it is a weapon system rather than a test rig. Its instruction is '
         '55 bits: per horizontal axis a 15-bit count of 10-TNT batches, a 4-bit trim for the last batch and a direction '
         'bit; 5 bits of height and a 4-bit height trim; one bit for nuke or stab charge with its size or depth. My port of '
         'his fire-control maths (<code>tools/firecontrol.py</code>) uses his constants (8.7556 blocks per X count, brake '
         'factors 0.9 and 1.5) and produces the button pattern for his control panel.',
         'Error comes from three places. Rounding: half a charge is 0.3 blocks. Payload position: a hundredth of a block of '
         'offset changes the push by tenths of a percent (chapter six). And the per-charge calibration itself, which I '
         'measured to about 1%. My three live shots missed by 0.85, 0.79 and 0.55 blocks over 117 blocks.') +
       [F.table(["shot", "TNT", "charges X/Z", "predicted stop", "actual stop", "miss"],
                [["Mk1-A", "8", "150 / 120", "91.46, 73.13", "91.72, 73.95", "0.85"],
                 ["Mk2", "64", "150 / 120", "91.46, 73.13", "92.14, 73.53", "0.79"],
                 ["Mk3 drill", "12", "150 / 120", "91.46, 73.13", "91.79, 73.57", "0.55"]])])

    ch("s12", "Payloads: pop, stab and drill", "Payloads", "#dc2626", "Chapter twelve",
       "What happens on arrival, and why timing beats quantity.",
       [("64 equal-fuse TNT", "357 blocks"), ("20 TNT, 4 ticks apart", "825 blocks"), ("ratio per TNT", "7.4×")],
       ['<h2>Timing beats <em>quantity</em></h2>',
        '<p class="lead">A payload of TNT that detonates in one tick at one point mostly wastes itself: the explosions '
        'overlap. The same TNT detonating one after another digs.</p>'] +
       p('I tested this without a cannon: TNT stacked exactly on one spot of a 31×31×20 block of stone, fuses either equal '
         'or spaced a few ticks apart. 64 TNT together destroyed 357 blocks and went 6 deep. 20 TNT spaced 4 ticks apart '
         'destroyed 825 and went 19 deep. Each TNT falls into the hole the previous one made and explodes at the bottom, so '
         'every extra TNT adds about a block of depth.') +
       [F.fig(fig_drill(), "Crater sizes for stacked payloads, by fuse timing. Orange: equal fuses. Blue: staggered.", "Fig. 12.1")] +
       p('cubicmetre\'s stab charge is the refined form of this idea. A kick stage, a bulk downward stage and a penetrator, '
         'with the batches spawned so the longer-fuse batch is pushed down by the shorter one under it. Swing (TNT oscillating '
         'when it explodes near other moving TNT) cut his early stab charges to 24% efficiency. Adding a 10-TNT kick one tick '
         'earlier gave 72%, and 9 kick TNT with fuses 1 to 9 gave 99%. His charges reach 279 blocks deep.',
         'Delivering a drill is harder than delivering a pop, because a drill only works if the TNT are stacked exactly. '
         'My Zephyr Mk3 made the right fuse ladder (37 to 73, four ticks apart), but its payload landed spread over half a '
         'block, the blasts threw each other sideways, and the live crater was 377 blocks instead of the 471 the same '
         'payload makes when stacked. Volume III tells that story.'))

    ch("s13", "Ring nukes", "Ring nukes", "#be185d", "Chapter thirteen",
       "Throwing a ring of TNT outward to cover hundreds of blocks.",
       [("cubicmetre max", "372 across"), ("my test", "~404 across"), ("TNT used", "174")],
       ['<h2>A ring <em>from a point</em></h2>',
        '<p class="lead">cubicmetre\'s nuke covers a disk up to 372 blocks across. It works by throwing a ring of TNT '
        'outward from one point. I rebuilt the physics on 26.3 and got a single ring to 404 blocks.</p>'] +
       p('A ring needs every TNT a hair from a centre point, each in its own direction. When charges at the centre explode, '
         'each ring TNT is pushed straight away from the centre, and they all land on one circle: in my tests the minimum '
         'and maximum radius matched to 0.1 block. cubicmetre gets the directions from TNT duplicated inside lazy chunks, '
         'which keeps its random priming momentum of 0.02 blocks per tick.',
         'Three findings got my ring from 5 blocks to 200. First, an explosion is centred 0.0625 above its TNT, so an '
         'expansion charge level with the ring pushes it almost straight down; sinking the charge by 0.0625 gave radius 39 '
         'from one TNT. Second, expansion charges in the same tick knock each other around before exploding, so they must be '
         'spaced, and one per tick saturates at radius 90. A pair works if the second sits exactly at the first\'s blast '
         'centre: two full-strength pushes per tick, radius 113. Third, a booster ring of short-fuse TNT that follows the main '
         'ring out and detonates at tick 7 kicks it again, to radius 201.') +
       [F.fig(fig_ring_radius(), "Ring radius against the number of expansion TNT. The booster ring (not plotted) took the "
              "pairs from 113 to 201.", "Fig. 13.1")] +
       p('What I have not done yet is fill the disk or deliver it. Inner rings from larger starting offsets land at radii 72 '
         'to 116 on their own, but the booster blasts knock them off course. My cannons cannot deliver a ring at all yet: '
         'they stack their payload on one point, and a ring needs each TNT offset in its own direction.'))

    ch("s14", "Limits and failure modes", "Limits", "#475569", "Chapter fourteen",
       "Everything that stops a shot, in one place.",
       [("fuse", "≤ 80 ticks"), ("NBT motion", "≤ 10 b/t"), ("dispenser", "≥ 4 ticks")],
       ['<h2>What stops <em>a shot</em></h2>',
        '<p class="lead">Most orbital strike failures are not physics surprises. They are limits that were known, '
        'collected here so they can be checked before a build rather than after a crater in the wrong place.</p>'] +
       F.table(["limit", "value", "consequence", "where"],
               [["TNT fuse", "80 ticks", "the fall after release must fit inside it; a staggered payload's shortest fuse sets the drop height", "ch. 8, 12"],
                ["saved motion", "≤ 10 b/t per axis", "a chunk unload during charging zeroes large stored velocities", "ch. 4"],
                ["dispenser rate", "1 per 4 ticks", "feeding speed; staggered fuses at most 4 ticks apart from one feeder", "ch. 8"],
                ["Paper TNT cap", "100 per tick", "set max-tnt-per-tick -1", "ch. 10"],
                ["brake arming", "must move into snow", "TNT dispensed into lazy snow is never braked", "ch. 7"],
                ["position precision", "0.01 block", "0.6% push error per axis; spreads a drill", "ch. 6"],
                ["vertical move", "cancelled by the floor", "payload leaves level; falls from cannon height", "ch. 4"],
                ["version drift", "per release", "re-test wind charges, compressors, honey/slime behaviour", "ch. 6, Vol. II"]]) +
       p('The fuse limit deserves the last word, because two builders found it independently. TheeDumbRock\'s calculator '
         'warns that the drop from cannon to target must stay under about 71 blocks or "the TNT just explodes in the air", '
         'and HOGAN\'s setup moves his cannon to keep that drop near 71. My Mk3 drill made the same limit sharper: its '
         'shortest fuse was 37 ticks, so its payload could only fall about 20 blocks. A cannon is aimed in three '
         'dimensions, and one of them is time.'))
    PROTOCOLS = [
        ("osc_tests.py · t_axis_order", "High-speed movement is resolved one axis at a time.",
         "Summon a gravity-free TNT with motion such as (9, 0, 9) or (8, 0, 9); place one stone block on the X-first or Z-first "
         "leg of its path; step one tick and record the displacement. Repeat with Y motion and a block above, and with motion 12 "
         "loaded from NBT.", "Y moves first; then the larger of |X|, |Z| (X on ties); a blocked leg stops at 4.01. NBT motion 12 is zeroed."),
        ("osc_tests.py · t_lazy_stasis", "A payload in a lazy chunk keeps position and fuse but accumulates knockback.",
         "Force-load a chunk, leave its neighbour lazy, park a TNT (fuse 200) 0.5 inside the lazy chunk, fire three identical "
         "TNT next to it from the loaded side, then load the lazy chunk and step.",
         "Motion grows 0.6248 per shot exactly; position and fuse unchanged until release."),
        ("osc_tests.py · t_powder_snow", "An entity that has moved into powder snow is stopped dead on its next move.",
         "Fire a TNT at 4.9 b/t down a corridor, with and without powder snow 5 blocks ahead; log four ticks.",
         "Control coasts with 0.98 drag; with snow it moves 4.41 into the snow and stops, motion zero."),
        ("osc_tests.py · t_stab_order", "Of two co-located TNT batches, the one spawned first must have the longer fuse to be driven down.",
         "Spawn 10 TNT fuse 2 and 10 TNT fuse 1 at one point in both orders; record the survivors' motion.",
         "Long-fuse batch first: driven down at 1.93 b/t. Second: +0.02, barely moved."),
        ("osc_tests.py · t_unloaded_explosion", "TNT that flies into unloaded chunks and explodes there.",
         "Lazy-launch a payload with 400 TNT into chunks that are not loaded; step; inspect the landing area.",
         "The payload explodes on arrival; the landing chunk is not left loaded; 66 grass blocks destroyed in a 9×9."),
        ("osc_tests.py · t_max_tnt_per_tick", "Spigot's TNT cap defers explosions beyond 100 per tick.",
         "Prime 300 TNT with fuse 1 at once; count survivors per tick under default and tuned settings.",
         "Default: 300 → 200 → 100 → 0. With max-tnt-per-tick -1: all 300 on the first tick."),
        ("osc_tests.py · t_long_range", "Cost and accuracy of a one-tick flight thousands of blocks long.",
         "Lazy-launch with 6,000 TNT; release; time the step; find the payload.",
         "4,435.9 b/t stored; found exactly at the predicted x after one tick; step wall time 0.21 s on Paper."),
        ("osc_tests.py · t_portal_ticket", "A nether-portal arrival loads 3×3 entity-processing chunks and a lazy ring.",
         "Send an item through a portal into unloaded overworld chunks; probe chunk states and a knockback probe two chunks out.",
         "Chunks +0, +1 entity-ticking; +2 frozen, storing 0.687 b/t from a probe explosion."),
        ("osc_lab.py · knockback_sweep", "Knockback on a lazy payload against distance to one TNT.",
         "One propellant TNT at 0.5 to 8 blocks from a frozen payload; record stored motion.",
         "Follows (1 − d/8); 0.873 at 1 block; zero when overlapping."),
        ("osc_lab.py · linearity", "Displacement after one released tick against propellant count.",
         "Batches of 1 to 200 TNT at fixed geometry; release; measure.", "Linear: 0.7393 blocks per TNT at this geometry."),
        ("osc_lab.py · calibration", "The spreadsheet method: per-axis calibration predicts a mixed shot.",
         "Fire 200 TNT on X alone and on Z alone; build the 2×2 matrix; solve for a (150, 90) target; fire it.",
         "Diagonal matrix 0.7393; solved 203 / 122 TNT; landed 0.22 and 0.20 blocks off."),
        ("osc_lab.py · free_flight", "Gravity and drag of a free TNT.", "Kick a lit TNT; log 40 ticks.",
         "Gravity −0.04 b/t² and drag ×0.98 per tick, as in vanilla."),
        ("zephyr.py · calibration", "Push per wind charge in the Zephyr core.",
         "100 X (or Z) charges into eight frozen TNT; read motion; repeat at 50, 200, 300 and with the launcher at Y+1 and Y+2.",
         "0.668 X per charge, linear to 300; 0.37% run spread at Y+1 against ~1% at Y+2."),
        ("mk1a_test.py / mk2_test.py", "The automatic controllers, end to end, in real time.",
         "Build; load TNT and charges; arm; poll feeder, launchers and staged count every 0.2 s; freeze; read every TNT.",
         "Mk1-A: 8 TNT fuse 75, motion (67.38, −34.01, 67.25). Mk2: 64 TNT fuse 75. Mk3: fuse ladder 37–73."),
        ("mk1a_livefire.py", "A full shot onto a target, logged tick by tick.",
         "Build at a chunk corner over superflat; stone target under the predicted stop; charge in real time; force-load the "
         "payload chunk; step 90 ticks logging every TNT; save; read the crater from the region files.",
         "Misses 0.85 / 0.79 / 0.55 blocks over 117; craters 311 / 650 / 377 blocks."),
        ("payload_drill_test.py", "How fuse timing changes a crater, cannon-free.",
         "Stack TNT on one spot of a 31×31×20 stone block with fuses 20 + k·stagger; save; count missing blocks.",
         "64 equal: ~357; 20 at 4 ticks: 825; 64 at 1 tick: 1,441 (to bedrock)."),
        ("nuke_test.py", "Ring-nuke physics.",
         "Summon ring TNT a hair from a centre in evenly spaced directions plus expansion TNT (sunk 0.0625), optional booster "
         "ring; step and log every TNT; map the craters.", "Up to radius 201 (diameter ~404) with pairs and a fuse-7 booster."),
    ]
    blocks = ['<h2>Rerun <em>everything</em></h2>',
              '<p class="lead">Every measurement in this book came from one of these scripts in <code>paper-tests/</code>, run '
              'over RCON against a Paper 26.3 server (and, where noted, vanilla 26.3). Each entry gives the question, the '
              'method and the result.</p>']
    for name, q, how, res in PROTOCOLS:
        blocks += [f'<h3>{F.E(name)}</h3>', f'<p><b>Question.</b> {F.E(q)}</p>', f'<p><b>Method.</b> {F.E(how)}</p>',
                   f'<div class="note"><b>Result</b><p>{F.E(res)}</p></div>']
    C.append({"id": "s15", "no": len(C) + 1, "title": "Appendix: test protocols", "short": "Protocols", "color": "#334155",
              "kicker": "Appendix", "dek": "How every number in this volume was measured, and how to measure it again.",
              "facts": [("test scripts", "8"), ("procedures", str(len(PROTOCOLS))), ("server", "Paper 26.3")], "blocks": blocks})
    return C
