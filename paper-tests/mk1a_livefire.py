"""Live shot with Zephyr Mk1-A: build, charge in real time, release, log every tick, read the crater.

    python3 mk1a_livefire.py <S x> <S y> <S z> <TNT> <X charges> <Z charges> [mk2|mk3]

With "mk2" or "mk3" the compact Zephyr Mk2 / Mk3 Drill is built instead (no arming plate: TNT
is loaded first and the launch lock holds the charges until it is all staged).

S must be a chunk corner (x, z multiples of 16): the payload chunk is +x/+z of it. The script
force-loads the W, N and NW chunks (the payload chunk stays lazy until release) and the
target chunk, builds a stone target block under the predicted impact point, and writes
livefire-<tag>.json with the charge log, the frozen payload and per-tick flight positions,
then saves the world so the crater can be read from the region files.
"""
import json
import re
import sys
import time

import zephyr as Z

r = Z.r
bx, Ys, bz, NT, NX, NZ = (int(v) for v in sys.argv[1:7])
assert bx % 16 == 0 and bz % 16 == 0
# per-charge payload motion measured on Mk1-A (mk1a-test-8x100.json)
VX, VZ, VY = 0.673792, 0.672531, -0.170027
pred = (bx + 0.5 + 0.9 * NX * VX, Ys, bz + 0.5 + 0.9 * NZ * VZ)   # the floor under S blocks the Y move
tx, tz = int(pred[0] // 1), int(pred[2] // 1)
GROUND = -61                     # superflat: grass top at -61
TOP = GROUND + 10                # target block: stone, 10 high
FEED = (bx - 1, Ys, bz + 1); XL = (bx - 1, Ys + 1, bz); ZL = (bx, Ys + 1, bz - 1); PL = (bx - 7, Ys - 1, bz + 3)
MODEL = sys.argv[7] if len(sys.argv) > 7 else "mk1a"
MK2 = MODEL in ("mk2", "mk3")
tag = ("" if MODEL == "mk1a" else MODEL + "-") + f"{NT}x{NX}x{NZ}"
out = {"S": [bx, Ys, bz], "tnt": NT, "nx": NX, "nz": NZ, "predicted_stop": pred, "target": [tx, TOP + 1, tz]}


def cnt(p):
    return sum(int(c) for c in re.findall(r"count: (\d+)", r.cmd(f"data get block {p[0]} {p[1]} {p[2]} Items")))


def tnts():
    o = r.cmd("execute as @e[type=tnt] run data get entity @s Pos")
    return [[float(a), float(b), float(c)] for a, b, c in re.findall(r"\[(-?[\d.E-]+)d, (-?[\d.E-]+)d, (-?[\d.E-]+)d\]", o)]


r.cmd("tick unfreeze")
for cx, cz in [(bx - 16, bz), (bx, bz - 16), (bx - 16, bz - 16), (tx, tz)]:
    r.cmd(f"forceload add {cx} {cz}")
r.cmd(f"forceload remove {bx} {bz}")
time.sleep(3)
# target: 21x21 stone block 10 high with a bullseye on top
r.cmd(f"fill {tx-10} {GROUND+1} {tz-10} {tx+10} {TOP} {tz+10} stone")
for rad, col in [(9, "white"), (7, "red"), (5, "white"), (3, "red"), (1, "white")]:
    r.cmd(f"fill {tx-rad} {TOP} {tz-rad} {tx+rad} {TOP} {tz+rad} {col}_concrete")
r.cmd("kill @e[type=tnt]")
if MK2:
    out["model"] = MODEL
    lay, kick = (Z.mk3_layout, Z.MK3_KICK) if MODEL == "mk3" else (Z.mk2_layout, Z.MK2_KICK)
    out["build_failures"] = Z.build_auto(bx, Ys, bz, layout=lay, kick=kick)
    r.cmd("kill @e[type=tnt]"); r.cmd("kill @e[type=wind_charge]")
    time.sleep(1)
    Z.load(FEED, "minecraft:tnt", NT)
    time.sleep(1)
    Z.load(XL, "minecraft:wind_charge", NX); Z.load(ZL, "minecraft:wind_charge", NZ)
else:
    out["build_failures"] = Z.build_auto(bx, Ys, bz)
    r.cmd("kill @e[type=tnt]"); r.cmd("kill @e[type=arrow]"); r.cmd("kill @e[type=wind_charge]")
    r.cmd(f"summon arrow {PL[0]+0.5} {PL[1]+0.3} {PL[2]+0.5} {{Motion:[0d,-0.5d,0d],pickup:0b}}")
    time.sleep(1)
    for p in (FEED, XL, ZL):
        for i in range(9):
            r.cmd(f"item replace block {p[0]} {p[1]} {p[2]} container.{i} with air")
    Z.load(FEED, "minecraft:tnt", NT); Z.load(XL, "minecraft:wind_charge", NX); Z.load(ZL, "minecraft:wind_charge", NZ)
    time.sleep(4)
    r.cmd("kill @e[type=arrow]")                       # arm
t0 = time.time(); log = []
while time.time() - t0 < 600:
    ps = tnts(); f, x, z = cnt(FEED), cnt(XL), cnt(ZL)
    staged = sum(1 for p in ps if p[0] >= bx and p[2] >= bz)
    log.append((round(time.time() - t0, 2), f, x, z, len(ps), staged))
    if len(log) % 25 == 1:
        print(log[-1], flush=True)
    if f == 0 and x == 0 and z == 0:
        break
    time.sleep(0.2)
time.sleep(1)
r.cmd("tick freeze")
out["charge_log"] = log
o = r.cmd("execute as @e[type=tnt] run data get entity @s Motion")
out["payload_motion"] = [[float(a), float(b), float(c)] for a, b, c in re.findall(r"\[(-?[\d.E-]+)d, (-?[\d.E-]+)d, (-?[\d.E-]+)d\]", o)]
out["payload_pos"] = tnts()
out["payload_fuse"] = [int(v) for v in re.findall(r"data: (\d+)", r.cmd("execute as @e[type=tnt] run data get entity @s fuse"))]
print("payload", len(out["payload_pos"]), "fuses", out["payload_fuse"], "motion[0]", out["payload_motion"][:1])
# release: make the payload chunk entity-ticking and step tick by tick
r.cmd(f"forceload add {bx} {bz}")
flight = []
for t in range(90):
    r.step(1)
    ps = tnts()
    flight.append(ps)
    if not ps:
        break
out["flight"] = flight
print("flight ticks", len(flight), "first", flight[0][:1] if flight and flight[0] else None, "last", flight[-2][:1] if len(flight) > 1 else None)
r.step(5)
r.cmd("tick unfreeze")
time.sleep(1)
r.cmd("save-all flush")
time.sleep(2)
out["release_tick_count"] = len(flight)
json.dump(out, open(f"livefire-{tag}.json", "w"), indent=1)
print("saved", f"livefire-{tag}.json")
