"""Volume III, Zephyr: my own cannons, from the first core to the ring nuke. All data from paper-tests/."""
import json
import math
import os

import svgfig as F
from svgfig import CORAL, CYAN, GOLD, GREEN, INK, MUTE, NAVY

PT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper-tests")
J = lambda f: json.load(open(os.path.join(PT, f)))
CAL = J("zephyr-calibration.json")
T8 = J("mk1a-test-8x100.json")
LF = {k: J(f) for k, f in [("mk1a", "livefire-8x150x120.json"), ("mk2", "livefire-mk2-64x150x120.json"), ("mk3", "livefire-mk3-12x150x120.json")]}


def p(*xs):
    return [f"<p>{x}</p>" for x in xs]


def crater_plan(key):
    d = LF[key]
    tx, _, tz = d["target"]
    blocks = d["crater"]["blocks"]
    depth = {}
    for x, y, z in blocks:
        depth[(x, z)] = max(depth.get((x, z), 0), -50 - y)
    s, R = 18, 11
    o = []
    for i in range(-R, R + 1):
        for j in range(-R, R + 1):
            dd = depth.get((tx + i, tz + j), 0)
            inside = abs(i) <= 10 and abs(j) <= 10
            col = "#e9e2d0" if not inside else ["#bdb5a5", "#d9a273", "#c97a45", "#a6522a", "#7a3415", "#4e1e0b", "#2a0f05"][min(dd, 6)]
            o.append(F.rect(20 + (i + R) * s, 20 + (j + R) * s, s, s, col, "#f7f1e2", .5))
    st = d["flight"][-2][0] if len(d["flight"]) > 1 and d["flight"][-2] else d["flight"][0][0]
    S = d["S"]
    fx, fz = d["flight"][0][0][0], d["flight"][0][0][2]
    px, pz = d["predicted_stop"][0], d["predicted_stop"][2]
    X = lambda x: 20 + (x - tx + R) * s
    Z = lambda z: 20 + (z - tz + R) * s
    o.append(f'<circle cx="{X(px):.1f}" cy="{Z(pz):.1f}" r="7" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    o.append(f'<circle cx="{X(fx):.1f}" cy="{Z(fz):.1f}" r="5" fill="{CORAL}" stroke="{INK}"/>')
    W = 20 + (2 * R + 1) * s + 20
    leg = [F.text(W + 10, 40, "crater depth (blocks)", 12, INK, "start", 700)]
    for k in range(1, 7):
        leg.append(F.rect(W + 10, 50 + k * 22, 18, 16, ["#bdb5a5", "#d9a273", "#c97a45", "#a6522a", "#7a3415", "#4e1e0b", "#2a0f05"][k]) + F.text(W + 36, 63 + k * 22, str(k), 12))
    leg.append(f'<circle cx="{W + 19}" cy="{230}" r="7" fill="none" stroke="{INK}" stroke-width="2.5"/>' + F.text(W + 36, 234, "predicted stop", 12))
    leg.append(f'<circle cx="{W + 19}" cy="{256}" r="5" fill="{CORAL}" stroke="{INK}"/>' + F.text(W + 36, 260, "actual stop", 12))
    leg.append(F.text(W + 10, 296, f"{d['crater']['destroyed']} blocks destroyed", 12, INK, "start", 700))
    return F.svg(W + 200, 20 + (2 * R + 1) * s + 20, "".join(o + leg))


def flight_chart(key):
    d = LF[key]
    S = d["S"]
    pts = []
    for t, fr in enumerate(d["flight"]):
        if fr:
            pts.append((t + 1, sum(q[1] for q in fr) / len(fr) - S[1]))
    return F.chart([("payload height (mean)", pts, CORAL)], "ticks after release", "height relative to cannon (blocks)", h=300)


def charge_chart(key):
    d = LF[key]
    log = d["charge_log"]
    st = [(r[0], r[5]) for r in log]
    return F.chart([("TNT staged in the frozen cell", st, CORAL)], "seconds after arming", "TNT staged", kind="step", h=260)


def per_tnt_chart():
    m = T8["motions"]
    xs = [(i + 1, v[0]) for i, v in enumerate(m)]
    zs = [(i + 1, v[2]) for i, v in enumerate(m)]
    return F.chart([("X", xs, CORAL), ("Z", zs, CYAN)], "TNT in the payload", "stored motion (b/t)", kind="scatter", h=280, ylim=(66.8, 68))


def fuse_chart():
    items = [("Mk1-A, staged at the end", [3, 15, 27, 39]), ("Mk1-A, staged per feed", [75] * 8), ("Mk2, 64 TNT", [75] * 64),
             ("Mk3 drill, 12 TNT", sorted(LF["mk3"]["payload_fuse"]))]
    series = [(lab, [(i + 1, f) for i, f in enumerate(v)], col) for (lab, v), col in zip(items, [MUTE, CORAL, GREEN, CYAN])]
    return F.chart(series, "TNT (sorted)", "fuse when frozen (ticks)", kind="scatter", h=300, ylim=(0, 85))


def comparison_table():
    rows = []
    for name, key, blocks in [("Mk1-A", "mk1a", 312), ("Mk2", "mk2", 102), ("Mk3 drill", "mk3", 106)]:
        d = LF[key]
        st = d["flight"][0][0]
        pr = d["predicted_stop"]
        miss = math.hypot(st[0] - pr[0], st[2] - pr[2])
        rows.append([name, blocks, d["tnt"], f"{d['nx']}/{d['nz']}", f"{miss:.2f}", d["crater"]["destroyed"], d["crater"]["depth"]])
    return F.table(["cannon", "blocks", "TNT", "charges X/Z", "miss (blocks)", "crater blocks", "depth"], rows)


def chapters(img):
    C = []

    def ch(id_, title, short, color, kicker, dek, facts, blocks, design=None):
        C.append({"id": id_, "no": len(C) + 1, "title": title, "short": short, "color": color, "kicker": kicker,
                  "dek": dek, "facts": facts, "blocks": blocks, "design": design})

    c100 = CAL["x100"]["avg"]
    ch("z1", "The Zephyr core", "Core", "#e9b23a", "Chapter one",
       "Seven blocks that charge, stop and release a payload.",
       [("blocks in the core", "7"), ("push per charge", "0.674"), ("stop factor", "×0.9")],
       ['<h2>Seven blocks <em>and a corner</em></h2>',
        '<p class="lead">Every Zephyr cannon is built around the same core: a cell of powder snow at the corner of a lazy '
        'chunk, two wind-charge dispensers that drop charges beside it, and a feeder and piston that put TNT into it.</p>'] +
       p('The payload cell S sits at the north-west corner of its chunk, so the cell to its west (W) and the cell to its '
         'north (N) are in other chunks. Those chunks are force-loaded; S\'s chunk is only next to them, so it is lazy. A '
         'dispenser above W drops wind charges into W, where they burst against W\'s floor and push the frozen payload east. '
         'A dispenser above N does the same from the north, pushing south. Two counts of wind charges are the whole aim.',
         'TNT arrives through W. A feeder dispenser south of W drops it in, it lands, and a piston west of W pushes it east '
         'across the chunk border into the snow. That push is the move into the snow that arms the brake (Volume I, chapter '
         'seven), and the TNT freezes the instant it crosses. On release (the chunk is loaded) the payload moves 0.9 of its '
         'stored velocity in X and Z, its Y move is blocked by the floor, and it stops dead in the air above the target, '
         'then falls.') +
       [F.fig(f'<img src="{img("zephyr-mk2-iso")}">', "Zephyr Mk2, the compact build, with the core in the near corner.", "Fig. 1.1")] +
       F.table(["cell", "block", "job"],
               [["S (0,0,0)", "powder snow", "payload cell, lazy chunk"], ["floors", "full blocks", "set burst height and TNT landing"],
                ["(-1,1,0)", "dispenser ↓", "X launcher: charges burst in W"], ["(0,1,-1)", "dispenser ↓", "Z launcher: charges burst in N"],
                ["(-1,0,1)", "dispenser →N", "TNT feeder into W"], ["(-2,0,0)", "piston →E", "stager: pushes TNT from W into S"],
                ["(-1,0,-1)", "concrete", "channel wall"]]))

    ch("z2", "Calibration", "Calibration", "#d97706", "Chapter two",
       "Measuring the push once, so every shot is arithmetic.",
       [("X per 100 charges", f"{c100[0]:.2f}"), ("Y per 100 charges", f"{c100[1]:.2f}"), ("linear to", "300 charges")],
       ['<h2>One number <em>per axis</em></h2>',
        '<p class="lead">A cannon that pushes linearly needs calibrating once. Fire 100 charges into a frozen payload, '
        'read its stored motion, and divide.</p>'] +
       p(f'Eight test payloads, 100 X charges each, stored {c100[0]:.3f} blocks per tick in X and {c100[1]:.3f} in Y on '
         f'average, with Z close to zero; the Z launcher alone gave the mirror image. 50, 100, 200 and 300 charges lay on one '
         'straight line. After the release brake (×0.9) that is 0.606 blocks of range per X charge.',
         'The Y component is the price of the geometry: each burst sits slightly above the payload\'s feet. It does not matter '
         'for aiming, because the cannon\'s floor cancels the Y move at release, but it is useful as a check: X and Z each add '
         'about −0.17 per charge, so −34 after 100 + 100.') +
       [F.fig(per_tnt_chart(), "Stored motion of each TNT in an 8-TNT payload after 100 + 100 charges (Mk1-A test). X spread "
              "0.003 b/t; Z spread 0.16, from the ±0.01 position of each TNT in its channel.", "Fig. 2.1"),
        F.table(["test", "X", "Y", "Z"], [[k, f"{v['avg'][0]:.3f}", f"{v['avg'][1]:.3f}", f"{v['avg'][2]:.3f}"] for k, v in CAL.items() if isinstance(v, dict) and "avg" in v])])

    ch("z3", "Mk1-A: the automatic cannon", "Mk1-A", "#c2410c", "Chapter three",
       "The core plus a controller that loads, stages and fires on its own.",
       [("blocks", "312"), ("TNT per shot", "8"), ("arming", "arrow despawn")],
       ['<h2>Load it, <em>walk away</em></h2>',
        '<p class="lead">Mk1-A adds a controller to the core. Put TNT in the feeder and charges in the launchers, shoot an '
        'arrow off its pressure plate (or let it despawn), and it stages every TNT, waits, and fires every charge.</p>'] +
       p('Its parts: an observer-pair clock divided by a copper bulb into a 12-tick square wave; a master comparator that '
         'passes the clock only while the arming plate is up; a feed line to the TNT feeder; a stager that pushes each TNT '
         'in 6 ticks after it is dispensed; a comparator reading the feeder through a 50-tick delay chain, which holds the '
         'launch comparator shut until feeding is done; and a long launch line round the west and north to the two launchers.',
         'Arming uses a vanilla quirk. An arrow on a wooden pressure plate keeps it pressed, and an arrow despawns 1,200 ticks '
         'after it was shot, but only while its chunk is processed. So the cannon arms itself a minute after you leave it '
         'running, and not while it sits unloaded.') +
       [F.fig(f'<img src="{img("zephyr-mk1-a-iso")}">', "Zephyr Mk1-A: the controller spread over a 13×14 base slab.", "Fig. 3.1"),
        F.fig(fuse_chart(), "Fuse of each TNT when it froze. Staging at the end of feeding gave a 12-tick ladder (grey); per-feed "
              "staging gave every TNT the same fuse (orange). Mk2 kept it, Mk3 made a ladder on purpose.", "Fig. 3.2")])

    ch("z4", "Nine bugs", "Debugging", "#9a3412", "Chapter four",
       "How the automatic cannon was made to work, one wrong assumption at a time.",
       [("bugs", "9"), ("worst", "quasi-connectivity"), ("fix that mattered most", "dust above air")],
       ['<h2>The X axis <em>was zero</em></h2>',
        '<p class="lead">The first automatic runs looked fine until the numbers came in. The payload had 67 blocks per tick '
        'of Z motion and almost none in X.</p>'] +
       p('The stager piston was extended during the launch, its head sitting in the W cell where the X charges burst. '
         'Each X charge exploded on the piston head. The first explanation, a two-tick pulse ending mid-extension, was wrong. '
         'A tick-by-tick trace showed the real cause: the observer on the delay line kept firing through the launch, because '
         'stage dust one block up and one over had joined the delay line diagonally, and the two made a 12-tick clock. '
         'A repeater in place of that dust fixed it, and X went to 67.5.',
         'Then per-feed staging, which gave equal fuses but caught every TNT mid-hop, until full-block floors cut the hop '
         'to 2 ticks. Then the copper bulb, whose <code>powered</code> flag flips twice per toggle, so the observer watching it '
         'pushed twice. Then a concrete step under the launch staircase strongly powering the stage dust beside it, so the '
         'stager fired on every launch pulse.',
         'The last one was the hardest. With all of that fixed, live runs still showed X near zero, and stepped tests did not. '
         'The X launcher was powered by a repeater, which made the dispenser a powered block, and that block touches the '
         'space above the stager piston. A piston counts as powered when the space above it is, but only checks when '
         'something updates it, so it extended whenever the next feed edge happened to update it, and held its head in W '
         'for the launch. Powering the air above the launcher instead fires the launcher through its own quasi-connectivity, '
         'and the dispenser is never a powered block.') +
       ['<div class="pull"><div>Every bug was a rule I half-knew.</div><small>Volume I, chapter nine lists them as rules</small></div>'])

    ch("z5", "Live fire", "Live fire", "#dc2626", "Chapter five",
       "The first real shot: 150 + 120 charges, 117 blocks, 0.85 blocks off.",
       [("TNT", "8"), ("miss", "0.85"), ("crater", f"{LF['mk1a']['crater']['destroyed']} blocks")],
       ['<h2>Real time, <em>real crater</em></h2>',
        '<p class="lead">For the live shot Mk1-A was built at y = −10 over a superflat world, with a 21×21×10 block of stone '
        'placed under the predicted impact point and a bullseye painted on top.</p>'] +
       p('Nothing was stepped or frozen until the launchers were empty. The controller staged 8 TNT in 5.9 seconds and fired '
         '150 X and 120 Z charges over 90. The payload then held (101.35, −45.49, 81.60) blocks per tick with every fuse at 75. '
         'The payload chunk was force-loaded and the server stepped tick by tick. The payload moved 91.2 blocks east and 73.4 '
         'south in that first tick, stopped, fell 40 blocks, and detonated on the bullseye at tick 75.') +
       [F.fig(charge_chart("mk1a"), "Staging during the live shot: one TNT every 0.6 s, all eight in under 6 s.", "Fig. 5.1"),
        F.fig(flight_chart("mk1a"), "Height of the payload after release: one tick sideways, then a 40-block fall.", "Fig. 5.2"),
        F.fig(crater_plan("mk1a"), "The crater, read back from the world's region files. 311 blocks, 5 deep.", "Fig. 5.3")])

    ch("z6", "Mk2: compact", "Mk2", "#3f9ad6", "Chapter six",
       "A third of the blocks, eight times the TNT.",
       [("blocks", "102"), ("TNT", "64"), ("crater", f"{LF['mk2']['crater']['destroyed']} blocks")],
       ['<h2>Lock, <em>don\'t invert</em></h2>',
        '<p class="lead">Mk1-A\'s controller was big because of one requirement: hold the launch until feeding is done. '
        'Mk2 meets it with a single locked repeater.</p>'] +
       p('A repeater whose side is powered by another repeater holds its state. Mk2 points the feeder comparator\'s boosted '
         'signal into the side of the launch repeater. While there is TNT in the feeder the launch is locked; when the '
         'feeder empties it unlocks two ticks later. No inverter, no 50-tick delay chain, no master gate. With the arming '
         'plate gone too, the clock moves to a four-block column behind the feeder and the base slab is unnecessary: '
         '102 blocks in an 8×4×13 box. The one rule is to load the TNT before the charges.',
         'With per-feed staging, payload size is limited only by the feeder. 64 TNT staged with equal fuses, and the live shot '
         'landed 0.79 blocks from the prediction. The crater was 650 blocks: twice Mk1-A\'s, for eight times the TNT. '
         'Explosions in one tick at one point mostly overlap.') +
       [F.fig(crater_plan("mk2"), "Mk2's 64-TNT crater in the same kind of target. It reaches the edge of the stone block.", "Fig. 6.1"),
        comparison_table()], design="zephyr-mk2")

    ch("z7", "Mk3: drill", "Mk3", "#0f766e", "Chapter seven",
       "A 4-tick clock and a fuse ladder: the right idea, delivered half a block wide.",
       [("blocks", "106"), ("fuse ladder", "37 → 73"), ("miss", "0.55")],
       ['<h2>Staggered on <em>purpose</em></h2>',
        '<p class="lead">The payload test in Volume I showed 12 TNT four ticks apart out-dig 64 together. Mk3 makes that '
        'payload: a ring clock of two repeaters feeds every 4 ticks, the TNT collects in the loading cell, and an observer '
        'on the feeder comparator pushes it all in when the feeder runs empty.</p>'] +
       p('The fuses came out exactly as planned: 37, 41, 45 … 73, plus two that arrived early. The 4-tick clock also launched '
         'twice as fast. The live shot was the most accurate of the three, 0.55 blocks off. But the crater was 377 blocks and '
         '6 deep, where the same payload stacked exactly made 471 and 12.',
         'The per-tick flight log shows why. Each TNT freezes against one wall of the 1-block loading channel or the other, '
         'z = 0.49 or 0.51. The Z charges amplify that into a 0.6% velocity difference, half a block at the target. Spread TNT '
         'throw each other sideways instead of falling into the hole; one landed 4 blocks away. The fix is to centre every TNT '
         'in Z before it is staged, and stop the stager\'s first pulse during loading. Neither is built yet.') +
       [F.fig(crater_plan("mk3"), "Mk3's drill crater: deeper in the middle, but scattered.", "Fig. 7.1")], design="zephyr-mk3-drill")

    ch("z8", "The ring nuke", "Ring nuke", "#be185d", "Chapter eight",
       "Matching cubicmetre's blast diameter with a test warhead.",
       [("diameter", "~404"), ("ring TNT", "80"), ("booster fuse", "7")],
       ['<h2>Wider than <em>372</em></h2>',
        '<p class="lead">With the boosted ring (Volume I, chapter thirteen) a single payload left 80 craters on a circle '
        'about 404 blocks across, wider than cubicmetre\'s largest nuke. It was placed by command, not fired.</p>'] +
       [F.fig(f'<img src="{img("nuke-boosted-r201")}">', "Blast map read from the world after the boosted ring test. The orange "
              "circle is cubicmetre's maximum (372 across).", "Fig. 8.1"),
        F.fig(f'<img src="{img("nuke-ring-seq5-r90")}">', "An earlier ring: five expansion charges, one per tick, radius 90.", "Fig. 8.2")] +
       p('The ring is dotted rather than filled: 80 craters, about 16 blocks apart. Filling it needs inner rings, which the '
         'booster currently blows off course, and many more TNT. Delivering it needs a payload builder that places each TNT a '
         'hair from the centre in its own direction, which is what cubicmetre\'s in-chunk duper does and my cannons do not.'))

    STILLS = [("lf60", "Live fire · the cannon as built"), ("lf230", "Staging · each TNT pushed in as it lands"),
              ("lf330", "Launch · wind charges every 12 ticks"), ("lf450", "Launch · stored velocity climbing"),
              ("lf560", "Frozen · lazy chunk, velocity stored"), ("lf640", "Release · one game tick, X then Z"),
              ("lf700", "Release · the pan to the target"), ("lf770", "Fall · 40 blocks onto the bullseye"),
              ("lf880", "Impact · the crater read from the world"), ("lf1060", "Result · 0.85 blocks off"),
              ("nk70", "Ring nuke · the warhead"), ("nk200", "Ring nuke · three ingredients"),
              ("nk310", "Ring nuke · expansion pairs"), ("nk400", "Ring nuke · the booster ring at tick 7"),
              ("nk470", "Ring nuke · flight"), ("nk600", "Ring nuke · the ring spreading"),
              ("nk760", "Ring nuke · impact"), ("nk790", "Ring nuke · 80 craters"),
              ("nk860", "Ring nuke · against cubicmetre's 372"), ("nk950", "Ring nuke · matched")]
    C.append({"id": "z10", "no": len(C) + 1, "title": "Stills from the recordings", "short": "Stills", "color": "#111827",
              "kicker": "Recordings", "dek": "Frames from the two videos: the Mk1-A live fire and the ring nuke test.",
              "facts": [("frames", "20"), ("videos", "2"), ("all from logged data", "yes")], "blocks": [],
              "stills": STILLS})

    ch("z9", "What comes next", "Next", "#475569", "Chapter nine",
       "The open problems, in the order I would attack them.",
       [("open problems", "5"), ("cannons fired", "3"), ("misses", "≤ 0.85")],
       ['<h2>Open <em>problems</em></h2>'] +
       ["<ul>" + "".join(f"<li>{x}</li>" for x in [
           "<b>Centre the TNT before staging.</b> A second push along Z, or a dispenser drift that always lands on one side, "
           "would make the Mk3 drill dig like the stacked test.",
           "<b>A real chunk loader.</b> Every shot so far used <code>/forceload</code>. A survival build needs portal loaders "
           "for the W, N and NW chunks and a way to load the payload chunk on command.",
           "<b>Survival arming and release.</b> Mk1-A's arrow timer works; Mk2 and Mk3 need an equivalent, plus a remote trigger.",
           "<b>A ring payload builder.</b> The warhead works; the cannon cannot make it. That means TNT placed inside the lazy "
           "chunk with its priming momentum intact.",
           "<b>Vanilla live fire.</b> The mechanics match on vanilla 26.3; the full cannon has only been fired on Paper.",
       ]) + "</ul>"] +
       p('Each of these is a test before it is a build. That was the lesson of the whole project: measure the mechanism on '
         'its own, then build the machine around the numbers.'))
    return C
