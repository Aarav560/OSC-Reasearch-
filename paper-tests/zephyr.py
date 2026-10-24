"""Zephyr Mk1: compact wind-charge lazy-acceleration cannon (my design), built and fired on Paper.

Geometry (one quadrant, fires +X/+Z). P = payload chunk (lazy), W = chunk to its west and
N = chunk to its north (both entity-ticking). S = (bx, Y, bz) is P's north-west corner block.

  S            powder_snow            payload cell (lazy); stone under it cancels -Y motion
  W pad        enchanting_table at (bx-1, Y-1, bz)   burst surface 0.25 below payload feet
  N pad        enchanting_table at (bx, Y-1, bz-1)
  X launcher   dispenser[down] at (bx-1, Y+1, bz)    wind charges -> burst on W pad
  Z launcher   dispenser[down] at (bx, Y+1, bz-1)    wind charges -> burst on N pad
  floor        enchanting_table at (bx, Y-1, bz)     payload rests at the same height as staged TNT
  TNT feeder   dispenser[north] at (bx-1, Y, bz+1)   stages primed TNT on the W pad
  stager       piston[east] at (bx-2, Y, bz)         pushes the staged stack 1 block east
  TNT feeder 2 dispenser[south] at (bx-1, Y, bz-1)   doubles the feed rate; also the channel wall

The piston push carries the stack across the chunk border into the powder snow, which arms the
brake (the entity moved into the snow while it was being processed) and freezes it in the lazy
chunk. Only then are wind charges fired, so every payload TNT receives the same impulses. On
release the payload moves 0.9 * v horizontally and stops dead above the target.
"""
import re
import sys
import time

from rcon import Rcon

r = Rcon()


def build(bx, Y, bz):
    """Zephyr Mk1b layout (see module doc; feeder fires north into the W cell, piston pushes east)."""
    cmds = [
        f"fill {bx-3} {Y-2} {bz-3} {bx+1} {Y+3} {bz+2} air",
        f"setblock {bx} {Y} {bz} powder_snow",
        f"setblock {bx} {Y-1} {bz} enchanting_table",          # floor of the payload cell
        f"setblock {bx-1} {Y-1} {bz} enchanting_table",        # W pad: staging floor + X burst surface
        f"setblock {bx} {Y-1} {bz-1} enchanting_table",        # N pad: Z burst surface
        f"setblock {bx-1} {Y+1} {bz} dispenser[facing=down]",  # X launcher (Y+1: 0.37% shot-to-shot)
        f"setblock {bx} {Y+1} {bz-1} dispenser[facing=down]",  # Z launcher
        f"setblock {bx-1} {Y} {bz+1} dispenser[facing=north]", # TNT feeder -> W cell
        f"setblock {bx-2} {Y} {bz} piston[facing=east]",       # stager: W cell -> payload cell
        f"setblock {bx-1} {Y} {bz-1} dispenser[facing=south]", # 2nd TNT feeder, also the channel wall
    ]
    for c in cmds:
        r.cmd(c)


def load(pos, item, n):
    x, y, z = pos
    slot = 0
    while n > 0:
        k = min(64, n)
        r.cmd(f"item replace block {x} {y} {z} container.{slot} with {item} {k}")
        n -= k
        slot += 1


def pulse(pos, side=(0, 1, 0)):
    """Power a component for 2 ticks with a redstone block placed beside it."""
    x, y, z = pos[0] + side[0], pos[1] + side[1], pos[2] + side[2]
    r.cmd(f"setblock {x} {y} {z} redstone_block")
    r.step(2)
    r.cmd(f"setblock {x} {y} {z} air")
    r.step(2)


def tnt_positions():
    out = r.cmd("execute as @e[type=tnt] run data get entity @s Pos")
    return [[float(m.group(i)) for i in (1, 2, 3)]
            for m in re.finditer(r"\[(-?[\d.E-]+)d, (-?[\d.E-]+)d, (-?[\d.E-]+)d\]", out)]


def charge(bx, Y, bz, n_tnt, nx, nz, simultaneous=False, rec=None):
    """Stage n_tnt TNT (two feeders, 4-tick dispenser cadence), settle, push them into the payload
    cell, then fire nx X-charges and nz Z-charges (sequentially, or X and Z in the same tick).
    rec(note) is called once per game tick if given. Returns the payload TNT motions."""
    F1 = (bx - 1, Y, bz + 1); F2 = (bx - 1, Y, bz - 1)
    XL = (bx - 1, Y + 1, bz); ZL = (bx, Y + 1, bz - 1); PISTON = (bx - 2, Y, bz)
    load(F1, "minecraft:tnt", (n_tnt + 1) // 2)
    load(F2, "minecraft:tnt", n_tnt // 2)
    if nx:
        load(XL, "minecraft:wind_charge", nx)
    if nz:
        load(ZL, "minecraft:wind_charge", nz)

    def tick(n=1, note=None):
        for _ in range(n):
            r.step(1)
            if rec:
                rec(note)
                note = None

    def fire(blocks, note=None):
        for p in blocks:
            r.cmd(f"setblock {p[0]} {p[1]} {p[2]} redstone_block")
        tick(2, note)
        for p in blocks:
            r.cmd(f"setblock {p[0]} {p[1]} {p[2]} air")
        tick(2)

    above = lambda p: (p[0], p[1] + 1, p[2])
    for i in range((n_tnt + 1) // 2):
        fire([(F1[0], F1[1], F1[2] + 1)] + ([(F2[0], F2[1], F2[2] - 1)] if 2 * i + 1 < n_tnt else []),
             "feed" if i == 0 else None)
    tick(14, "settle")
    fire([(PISTON[0] - 1, PISTON[1], PISTON[2])], "stage")
    if simultaneous:
        for i in range(max(nx, nz)):
            fire(([above(XL)] if i < nx else []) + ([above(ZL)] if i < nz else []), "charge" if i == 0 else None)
    else:
        for i in range(nx):
            fire([above(XL)], "x-charges" if i == 0 else None)
        for i in range(nz):
            fire([above(ZL)], "z-charges" if i == 0 else None)
    out = r.cmd("execute as @e[type=tnt] run data get entity @s Motion")
    return [[float(m.group(i)) for i in (1, 2, 3)]
            for m in re.finditer(r"\[(-?[\d.E-]+)d, (-?[\d.E-]+)d, (-?[\d.E-]+)d\]", out)]


# ---------------------------------------------------------------------------------------------
# Zephyr Mk1-A: the same core with a self-contained redstone controller.
# Coordinates are relative to S (the payload cell). Everything with x < 0 is in the W chunk,
# z < 0 in the N/NW chunks; nothing but S and its floor sits in the payload chunk P.
#   arm:    wooden pressure plate (-7,-1,3). An arrow on it disarms; it despawns 1200 ticks
#           after being shot (only while the chunk is ticking), which arms the cannon.
#   clock:  observer pair (-9,-2,4)/(-8,-2,4) -> repeater -> comparator C_master (-6,-2,4,
#           subtract, side = plate via dust) -> bus B (-5,-2,4)
#   feed:   B -> dust east -> staircase up -> repeater (-1,0,3) -> block (-1,0,2) -> feeder
#   sense:  comparator C_F (-2,0,1) reads the feeder -> R1 -> staircase down -> R2..R5 (y=-2)
#           -> R6 (-6,-2,5) into the side of C_launch: launch unlocks ~50 ticks after feeding ends
#   stage:  copper bulb (-2,0,2) toggled by every feed -> comparator -> observer -> piston from
#           the north: each TNT is pushed into the lazy cell as soon as it has settled
#   launch: C_launch (-5,-2,5, subtract, rear = B) -> long dust loop round the west and north
#           -> staircase up -> dust (-1,2,-1) above the X launcher, repeater B (1,1,-1) into Z
# ---------------------------------------------------------------------------------------------
STAGE_D = 1   # redstone ticks (2 game ticks each)


def auto_layout():
    L = []

    def put(x, y, z, b):
        L.append((x, y, z, b))

    def dust(pts):
        for p in pts:
            put(*p, "redstone_wire")

    # slab under the y=-2 controller
    for x in range(-13, 0):
        for z in range(-6, 8):
            put(x, -3, z, "gray_concrete")
    # core (single feeder; the old second feeder position becomes the channel wall)
    put(0, 0, 0, "powder_snow")
    # full-block floors (the Mk1b core uses enchanting tables): payload and both bursts all sit
    # 0.25 higher, so the burst-to-payload geometry is unchanged, but a dispensed TNT lands in
    # 2 ticks instead of 4 and can be staged before the next one arrives
    for p in [(0, -1, 0), (-1, -1, 0), (0, -1, -1)]:
        put(*p, "polished_andesite")
    put(-1, 1, 0, "dispenser[facing=down]")          # X launcher
    put(0, 1, -1, "dispenser[facing=down]")          # Z launcher
    put(-1, 0, 1, "dispenser[facing=north]")         # TNT feeder
    put(-1, 0, -1, "white_concrete")                 # channel wall
    put(-2, 0, 0, "piston[facing=east]")             # stager
    # clock + master gate. A comparator re-checks its input 2 game ticks after it changes, so
    # the observers' 2-gt pulses never get through. A copper bulb toggled by every pulse turns
    # them into a square wave (half the clock rate) that the comparator reads directly.
    put(-9, -2, 4, "observer[facing=east]"); put(-8, -2, 4, "observer[facing=west]")
    put(-7, -2, 4, "waxed_copper_bulb")
    put(-6, -2, 4, "comparator[facing=west,mode=subtract]")                               # C_master
    put(-7, -2, 3, "oak_planks"); put(-7, -1, 3, "oak_pressure_plate")                    # arm plate
    dust([(-6, -2, 3)])                                                                    # plate -> side
    dust([(-5, -2, 4)])                               # bus B
    # feed line: B -> east -> staircase -> feeder
    dust([(-4, -2, 4), (-3, -2, 4)])
    put(-2, -2, 4, "gray_concrete"); dust([(-2, -1, 4)])
    put(-1, -1, 4, "gray_concrete"); dust([(-1, 0, 4)])
    put(-1, -1, 3, "gray_concrete"); put(-1, 0, 3, "repeater[facing=south,delay=1]")
    put(-1, 0, 2, "white_concrete")
    # feeder sensing + 24-tick launch delay
    put(-2, -1, 1, "gray_concrete"); put(-2, 0, 1, "comparator[facing=east,mode=compare]")
    put(-3, -1, 1, "gray_concrete"); put(-3, 0, 1, "repeater[facing=east,delay=4]")       # R1
    put(-4, -1, 1, "gray_concrete"); dust([(-4, 0, 1)])
    put(-5, -2, 1, "gray_concrete"); dust([(-5, -1, 1)])
    dust([(-6, -2, 1)])
    for x in (-7, -8, -10):
        put(x, -2, 1, "repeater[facing=east,delay=4]")                                   # R2,R3,R5
    put(-9, -2, 1, "repeater[facing=east,delay=4]")                                       # R4
    dust([(-11, -2, z) for z in range(1, 6)] + [(-10, -2, 5), (-9, -2, 5), (-8, -2, 5), (-7, -2, 5)])
    put(-6, -2, 5, "repeater[facing=west,delay=4]")                                       # R6
    put(-5, -2, 5, "comparator[facing=north,mode=subtract]")                              # C_launch
    # stage, once per feed: the feed's output block (-1,0,2) toggles a copper bulb on every feed.
    # A comparator reads the bulb, so its state flips once per feed (the bulb's own `powered`
    # flag flips twice), and an observer on the comparator makes one pulse. That pulse reaches
    # the piston from the north 6 game ticks after the feed edge: the new TNT has landed (2
    # ticks after being dispensed) and the head is clear before the next one arrives.
    # Every TNT enters the lazy cell with the same fuse, so the payload detonates together.
    # Supports under stage dust are glass where they touch other circuitry.
    put(-2, 0, 2, "waxed_copper_bulb")
    put(-3, -1, 2, "gray_concrete"); put(-3, 0, 2, "comparator[facing=east,mode=compare]")
    put(-3, 1, 2, "observer[facing=down]")
    dust([(-3, 2, 2)])
    put(-3, 1, 1, "glass"); put(-3, 2, 1, f"repeater[facing=south,delay={STAGE_D}]")
    put(-3, 1, 0, "glass"); dust([(-3, 2, 0)])
    put(-3, 1, -1, "gray_concrete"); dust([(-3, 2, -1)])   # solid: dust on glass passes signal
    put(-3, 0, -2, "gray_concrete"); dust([(-3, 1, -2)])   # up a step but never down one
    put(-3, -1, -3, "glass"); dust([(-3, 0, -3)])
    put(-2, -1, -3, "glass"); dust([(-2, 0, -3)])
    put(-2, -1, -2, "glass"); dust([(-2, 0, -2)])
    put(-2, 1, -3, "gray_concrete"); put(-2, 1, -2, "gray_concrete")   # cut the diagonal links to
                                                                         # the launch staircase
    put(-2, -1, -1, "gray_concrete"); put(-2, 0, -1, "repeater[facing=north,delay=1]")
    # launch line: C_launch -> west -> north -> east -> staircase -> X and Z launchers
    # (row z=7, one row clear of the z=5 delay line so the two never touch)
    dust([(-5, -2, 6)] + [(x, -2, 7) for x in range(-5, -14, -1) if x != -10])
    put(-10, -2, 7, "repeater[facing=east,delay=1]")
    dust([(-13, -2, z) for z in range(6, -7, -1) if z != 0])
    put(-13, -2, 0, "repeater[facing=south,delay=1]")
    dust([(x, -2, -6) for x in range(-12, 0) if x != -7])
    put(-7, -2, -6, "repeater[facing=west,delay=1]")
    put(-1, -2, -5, "gray_concrete"); dust([(-1, -1, -5)])
    put(-1, -1, -4, "gray_concrete"); dust([(-1, 0, -4)])
    put(-1, 0, -3, "glass"); dust([(-1, 1, -3)])     # glass under launch dust next to the stage
    put(-1, 0, -2, "glass"); dust([(-1, 1, -2)])     # path, so neither feeds the other
    # X launcher: dust pointing into the air above it fires it by quasi-connectivity. Powering
    # the dispenser itself (a repeater or dust into it) makes it a powered block beside the
    # space above the stager piston, which then quasi-powers the piston: its head sat in the W
    # cell for the whole launch pulse and caught the X charges.
    put(-1, 1, -1, "glass"); dust([(-1, 2, -1)])                                          # -> X
    for p in [(0, 0, -3), (1, 0, -3), (2, 0, -3), (2, 0, -2), (2, 0, -1), (1, 0, -1)]:
        put(*p, "gray_concrete")
    dust([(0, 1, -3), (1, 1, -3), (2, 1, -3), (2, 1, -2), (2, 1, -1)])
    put(1, 1, -1, "repeater[facing=east,delay=1]")                                        # B -> Z
    return L


def build_auto(bx, Y, bz):
    r.cmd(f"fill {bx-14} {Y-3} {bz-7} {bx+3} {Y+3} {bz+8} air")
    lay = auto_layout()
    # supports first, components after, so nothing pops off while placing
    lay.sort(key=lambda b: (b[1], 0 if "concrete" in b[3] or "planks" in b[3] or "table" in b[3] else 1))
    bad = []
    for x, y, z, b in lay:
        out = r.cmd(f"setblock {bx+x} {Y+y} {bz+z} minecraft:{b}")
        if not out.startswith("Changed"):
            bad.append((x, y, z, b, out[:80]))
    # rebuilding pops loose dust/repeaters as items; any entity left on the arming plate holds it
    r.cmd(f"kill @e[type=item,x={bx-16},y={Y-4},z={bz-8},dx=20,dy=8,dz=17]")
    # kick the observer clock into oscillation (placing an observer facing another does it)
    r.cmd(f"setblock {bx-8} {Y-2} {bz+4} air")
    r.cmd(f"setblock {bx-8} {Y-2} {bz+4} observer[facing=west]")
    return bad
