"""Payload test: how fuse timing changes the crater, with no cannon involved.

    python3 payload_drill_test.py <x0> <z0> "<name>:<count>:<stagger>" ...

Each trial fills a 31x31x20 stone block (top at y=-41) at its own spot on the superflat, then
summons <count> TNT stacked on its centre with fuses 20, 20+stagger, 20+2*stagger, ...
Read the craters afterwards from the region files (the world is saved at the end).
"""
import json
import sys
import time

import zephyr as Z

r = Z.r
x0, z0 = int(sys.argv[1]), int(sys.argv[2])
trials = [(a.split(":")[0], int(a.split(":")[1]), int(a.split(":")[2])) for a in sys.argv[3:]]
res = {}
r.cmd("tick unfreeze")
for i, (name, n, st) in enumerate(trials):
    cx, cz = x0 + i * 64, z0
    r.cmd(f"forceload add {cx-16} {cz-16} {cx+16} {cz+16}")
    time.sleep(2)
    for y0 in range(-60, -40, 10):
        r.cmd(f"fill {cx-15} {y0} {cz-15} {cx+15} {y0+9} {cz+15} stone")
    r.cmd(f"fill {cx-15} -40 {cz-15} {cx+15} -20 {cz+15} air")
    for k in range(n):
        r.cmd(f"summon tnt {cx+0.5} -40 {cz+0.5} {{fuse:{20+k*st},Motion:[0d,0d,0d]}}")
    time.sleep(1.2 + n * st / 20 + 1.5)
    res[name] = (cx, cz)
r.cmd("save-all flush")
time.sleep(3)
json.dump(res, open("payload-drill-sites.json", "w"))
print(res)
