"""Functional test of Zephyr Mk1-A in real time: disarm with an arrow, load, arm, log phases."""
import json
import re
import sys
import time

import zephyr as Z

r = Z.r
bx, bz, Y = (int(v) for v in sys.argv[1:4]) if len(sys.argv) > 3 else (52000, 52000, -44)
NT, NX, NZ = (int(v) for v in sys.argv[4:7]) if len(sys.argv) > 6 else (8, 100, 100)
FEED = (bx - 1, Y, bz + 1); XL = (bx - 1, Y + 1, bz); ZL = (bx, Y + 1, bz - 1); PL = (bx - 7, Y - 1, bz + 3)


def cnt(p):
    out = r.cmd(f"data get block {p[0]} {p[1]} {p[2]} Items")
    return sum(int(c) for c in re.findall(r"count: (\d+)", out))


r.cmd("tick unfreeze")
r.cmd("kill @e[type=tnt]"); r.cmd("kill @e[type=arrow]"); r.cmd("kill @e[type=wind_charge]")
r.cmd(f"summon arrow {PL[0]+0.5} {PL[1]+0.3} {PL[2]+0.5} {{Motion:[0d,-0.5d,0d],pickup:0b}}")
time.sleep(1)
print("disarmed:", "passed" in r.cmd(f"execute if block {PL[0]} {PL[1]} {PL[2]} oak_pressure_plate[powered=true]"))
for p in (FEED, XL, ZL):
    for i in range(9):
        r.cmd(f"item replace block {p[0]} {p[1]} {p[2]} container.{i} with air")
Z.load(FEED, "minecraft:tnt", NT); Z.load(XL, "minecraft:wind_charge", NX); Z.load(ZL, "minecraft:wind_charge", NZ)
time.sleep(4)          # the feeder-sense delay chain needs ~50 ticks to settle before arming
print("loaded, still disarmed: feeder", cnt(FEED), "X", cnt(XL), "Z", cnt(ZL), "tnt", len(Z.tnt_positions()))
r.cmd("kill @e[type=arrow]")          # the despawn
t0 = time.time(); log = []
while time.time() - t0 < 120:
    ps = Z.tnt_positions(); f, x, z = cnt(FEED), cnt(XL), cnt(ZL)
    inS = sum(1 for p in ps if p[0] >= bx and p[2] >= bz)
    log.append((round(time.time() - t0, 2), f, x, z, len(ps), inS))
    if len(log) % 8 == 1:
        print(log[-1], flush=True)
    if x == 0 and z == 0 and f == 0:
        break
    time.sleep(0.2)
time.sleep(1)
r.cmd("tick freeze")
out = r.cmd("execute as @e[type=tnt] run data get entity @s Motion")
ms = [[float(m.group(i)) for i in (1, 2, 3)] for m in re.finditer(r"\[(-?[\d.E-]+)d, (-?[\d.E-]+)d, (-?[\d.E-]+)d\]", out)]
print("final", log[-1], "payload", len(ms), "avg motion", [round(sum(m[i] for m in ms) / len(ms), 3) for i in range(3)] if ms else None)
print("fuses", sorted(int(v) for v in re.findall(r"data: (\d+)", r.cmd("execute as @e[type=tnt] run data get entity @s fuse"))))
json.dump({"log": log, "motions": ms}, open("mk1a-test.json", "w"))
