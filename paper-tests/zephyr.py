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
