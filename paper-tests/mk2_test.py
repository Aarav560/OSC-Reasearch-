"""Functional test of Zephyr Mk2 in real time: build, load TNT, then wind charges, log, freeze.

    python3 mk2_test.py <S x> <S y> <S z> <TNT> <X charges> <Z charges> [mk3]

S must be a chunk corner. Force-loads the W, N and NW chunks (the payload chunk stays lazy),
builds Mk2, loads the feeder, loads the launchers a second later (the lock holds the launch
until every TNT is staged), and waits until everything is empty. Writes mk2-test.json.
"""
import json
import re
import sys
import time

import zephyr as Z

r = Z.r
bx, Ys, bz, NT, NX, NZ = (int(v) for v in sys.argv[1:7])
FEED = (bx - 1, Ys, bz + 1); XL = (bx - 1, Ys + 1, bz); ZL = (bx, Ys + 1, bz - 1)


def items(p):
    out = r.cmd(f"data get block {p[0]} {p[1]} {p[2]} Items")
    return sum(int(c) for c in re.findall(r"count: (\d+)", out))


def vecs(path):
    o = r.cmd(f"execute as @e[type=tnt] run data get entity @s {path}")
    return [[float(a), float(b), float(c)] for a, b, c in re.findall(r"\[(-?[\d.E-]+)d, (-?[\d.E-]+)d, (-?[\d.E-]+)d\]", o)]


r.cmd("tick unfreeze")
for cx, cz in [(bx - 16, bz), (bx, bz - 16), (bx - 16, bz - 16)]:
    r.cmd(f"forceload add {cx} {cz}")
r.cmd(f"forceload remove {bx} {bz}")
time.sleep(2)
r.cmd("kill @e[type=tnt]")
MK3 = len(sys.argv) > 7 and sys.argv[7] == "mk3"
bad = Z.build_auto(bx, Ys, bz, layout=Z.mk3_layout if MK3 else Z.mk2_layout, kick=Z.MK3_KICK if MK3 else Z.MK2_KICK)
print("build failures:", bad)
time.sleep(1)
Z.load(FEED, "minecraft:tnt", NT)
time.sleep(1)
Z.load(XL, "minecraft:wind_charge", NX); Z.load(ZL, "minecraft:wind_charge", NZ)
t0 = time.time(); log = []
while time.time() - t0 < 900:
    ps = vecs("Pos"); f, x, z = items(FEED), items(XL), items(ZL)
    staged = sum(1 for p in ps if p[0] >= bx and p[2] >= bz)
    log.append((round(time.time() - t0, 2), f, x, z, len(ps), staged))
    if len(log) % 25 == 1:
        print(log[-1], flush=True)
    if f == 0 and x == 0 and z == 0:
        break
    time.sleep(0.2)
time.sleep(1.5)
r.cmd("tick freeze")
ms = vecs("Motion")
fuses = sorted(int(v) for v in re.findall(r"data: (\d+)", r.cmd("execute as @e[type=tnt] run data get entity @s fuse")))
avg = [round(sum(m[i] for m in ms) / len(ms), 3) for i in range(3)] if ms else None
print("final", log[-1], "payload", len(ms), "avg motion", avg)
print("fuses", fuses)
json.dump({"S": [bx, Ys, bz], "tnt": NT, "nx": NX, "nz": NZ, "build_failures": bad, "log": log,
           "motions": ms, "fuses": fuses, "positions": vecs("Pos")}, open("mk3-test.json" if MK3 else "mk2-test.json", "w"))
