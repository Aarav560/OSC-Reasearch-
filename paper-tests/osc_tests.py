"""Headless verification of orbital-strike-cannon mechanics on a Paper server.

Everything is driven over RCON with vanilla commands only:
  * /forceload gives a chunk a level-31 ticket -> that chunk is entity-ticking and
    the ring of chunks around it is "lazy" (block-ticking, entities frozen), which
    is exactly the stasis region an OSC builds with nether-portal tickets.
  * /tick freeze + /tick step N make every measurement tick-exact.

Usage: python3 osc_tests.py [results.json]
"""
import json
import sys
import time

from rcon import Rcon

r = Rcon()
RESULTS = {}
CX = 1000  # tests live around chunk x=1000 (block x=16000), far from spawn


def bx(chunk_x, off=0.0):
    return chunk_x * 16 + off


def wait_loaded(x, y, z, timeout=10):
    t = time.time()
    while time.time() - t < timeout:
        if "passed" in r.cmd(f"execute if loaded {int(x)} {y} {int(z)}").lower():
            return True
        time.sleep(0.2)
    return False


def reset():
    r.cmd("tick freeze")
    r.cmd("kill @e[type=!player]")
    r.cmd("forceload remove all")
    time.sleep(0.5)


def forceload(cx0, cz0, cx1=None, cz1=None):
    cx1 = cx0 if cx1 is None else cx1
    cz1 = cz0 if cz1 is None else cz1
    r.cmd(f"forceload add {cx0*16} {cz0*16} {cx1*16+15} {cz1*16+15}")
    # a forced chunk's neighbours become lazy; give the chunk system time to settle
    wait_loaded(cx0 * 16 + 8, 100, cz0 * 16 + 8)
    r.step(2)
    time.sleep(0.5)


def tnt(x, y, z, fuse=80, motion=(0, 0, 0), nograv=True, tag="t"):
    m = ",".join(f"{v}d" for v in motion)
    ng = "1b" if nograv else "0b"
    return r.cmd(f"summon tnt {x} {y} {z} {{fuse:{fuse},NoGravity:{ng},Motion:[{m}],Tags:[\"{tag}\"]}}")


def record(name, **kw):
    RESULTS[name] = kw
    print(f"\n## {name}")
    for k, v in kw.items():
        print(f"  {k}: {v}")


# ----------------------------------------------------------------------------
def t_axis_order():
    """High-speed movement is resolved one axis at a time: Y, then the larger of X/Z, then the other."""
    reset()
    c = CX
    forceload(c - 2, -2, c + 2, 2)
    x0, y0, z0 = bx(c, 0.5), 100.0, 0.5
    cases = {}
    for label, motion, block in [
        # NBT Motion components with |v| > 10 are zeroed on load, so stay <= 10
        ("free flight", (9, 0, 9), None),
        ("|X|=|Z|, block on X-first leg", (9, 0, 9), (int(x0) + 5, 100, 0)),
        ("|X|=|Z|, block on Z-first leg", (9, 0, 9), (int(x0), 100, 5)),
        ("|Z|>|X|, block on X-first leg", (8, 0, 9), (int(x0) + 5, 100, 0)),
        ("|Z|>|X|, block on Z-first leg", (8, 0, 9), (int(x0), 100, 5)),
        ("|X|>|Z|, block on Z-first leg", (9, 0, 8), (int(x0), 100, 5)),
        ("Y first: block above start", (9, 5, 0), (int(x0), 103, 0)),
        ("NBT clamp: Motion x=12", (12, 0, 0), None),
    ]:
        r.cmd(f"fill {int(x0)-2} 99 -2 {int(x0)+14} 101 14 air")
        if block:
            r.cmd(f"setblock {block[0]} {block[1]} {block[2]} obsidian")
        r.cmd("kill @e[type=tnt]")
        tnt(x0, y0, z0, motion=motion)
        r.step(1)
        pos = r.vec("@e[type=tnt,limit=1]", "Pos")
        cases[label] = {"motion": motion, "block": block, "pos_after_1_tick": pos,
                        "delta": tuple(round(p - s, 3) for p, s in zip(pos, (x0, y0, z0))) if pos else None}
    r.cmd(f"fill {int(x0)-2} 99 -2 {int(x0)+14} 101 14 air")
    record("axis_order", cases=cases)


def t_lazy_stasis():
    """Payload in a lazy chunk keeps its position and fuse but accumulates knockback."""
    reset()
    c = CX + 10
    forceload(c, 0)                       # chunk c is entity-ticking, chunk c+1 is lazy
    px, py, pz = bx(c + 1, 1.5), 100.0, 8.5   # payload 1.5 blocks into the lazy chunk
    tnt(px, py, pz, fuse=200, tag="payload")
    log = []
    for shot in range(1, 4):
        tnt(bx(c, 14.5), py, pz, fuse=1, tag="prop")  # 3 blocks west, inside ticking chunk
        r.step(2)
        log.append({
            "after_shot": shot,
            "payload_pos": r.vec("@e[tag=payload,limit=1]", "Pos"),
            "payload_motion": r.vec("@e[tag=payload,limit=1]", "Motion"),
            "payload_fuse": r.num("@e[tag=payload,limit=1]", "fuse"),
        })
    # release: make the payload's chunk entity-ticking, then step one tick at a time
    before = r.vec("@e[tag=payload,limit=1]", "Pos")
    r.cmd(f"forceload add {(c+1)*16} 0")
    wait_loaded((c + 1) * 16 + 8, 100, 8)
    time.sleep(1)
    track = []
    for _ in range(3):
        r.step(1)
        track.append(r.vec("@e[tag=payload,limit=1]", "Pos"))
    record("lazy_stasis", charges=log, release={"pos_before": before, "pos_per_tick": track})


def t_powder_snow():
    """An entity that has *moved into* powder snow is stopped dead on its next move."""
    reset()
    c = CX + 20
    forceload(c - 1, -1, c + 3, 1)
    x0 = bx(c, 0.5)
    out = {}
    for label, snow in [("control (no snow)", False), ("powder snow at +5", True)]:
        r.cmd(f"fill {int(x0)} 99 0 {int(x0)+40} 101 2 air")
        r.cmd("kill @e[type=tnt]")
        if snow:
            r.cmd(f"setblock {int(x0)+5} 100 0 powder_snow")
        tnt(x0, 100, 0.5, motion=(5, 0, 0))
        track = []
        for _ in range(4):
            r.step(1)
            track.append((r.vec("@e[type=tnt,limit=1]", "Pos"), r.vec("@e[type=tnt,limit=1]", "Motion")))
        out[label] = [{"pos": p, "motion": m} for p, m in track]
    r.cmd(f"fill {int(x0)} 99 0 {int(x0)+40} 101 2 air")
    record("powder_snow", cases=out)


def t_stab_order():
    """Two co-located TNT batches; the one spawned first must have the longer fuse to be driven down."""
    reset()
    c = CX + 30
    forceload(c - 1, -1, c + 1, 1)
    x, y, z = bx(c, 8.5), 150.0, 8.5
    out = {}
    # NBT fuse:1 already detonates in the first tick, so the "1 vs 0" batches of the
    # video are fuse 2 (a) vs fuse 1 (b) here
    for label, order in [("long-fuse batch spawned FIRST", [(2, "a"), (1, "b")]),
                         ("long-fuse batch spawned SECOND", [(1, "b"), (2, "a")])]:
        r.cmd("kill @e[type=tnt]")
        for fuse, tag in order:
            for _ in range(10):
                r.cmd(f"summon tnt {x} {y} {z} {{fuse:{fuse},Tags:[\"{tag}\"]}}")
        r.step(1)
        out[label] = {"survivors(a)": r.count("@e[tag=a]"),
                      "a_motion": r.vec("@e[tag=a,limit=1]", "Motion"),
                      "a_pos": r.vec("@e[tag=a,limit=1]", "Pos")}
    record("stab_charge_order", batches="10 TNT fuse 2 (a) + 10 TNT fuse 1 (b)", cases=out)


def lazy_launch(c, n, payload_fuse, y=-60.0, z=8.5):
    """Build an n-TNT lazy-accelerated shot east from chunk c; returns the payload x.

    Payload sits 0.5 blocks inside lazy chunk c+1, propellant 1 block west of it inside
    ticking chunk c (knockback 1 - 1/8 = 0.875 b/t per TNT). Propellant is spawned in
    batches of 100 so Spigot's max-tnt-per-tick never defers any of it.
    """
    forceload(c, 0)
    px = bx(c + 1, 0.5)
    tnt(px, y, z, fuse=payload_fuse, tag="payload")
    left = n
    while left > 0:
        k = min(100, left)
        for _ in range(k):
            r.cmd(f"summon tnt {px - 1} {y} {z} {{fuse:1,NoGravity:1b}}")
        r.step(1)
        left -= k
    r.step(1)
    return px


def release(c):
    r.cmd(f"forceload add {(c+1)*16} 0")
    wait_loaded((c + 1) * 16 + 8, 100, 8)
    time.sleep(1)


def t_unloaded_explosion():
    """TNT that flies into unloaded chunks and explodes there (OSC log-in trap)."""
    reset()
    c = CX + 50
    n = 400
    # pre-generate the strip the payload will land in, then let it unload
    r.cmd(f"forceload add {(c+20)*16} 0 {(c+26)*16} 15")
    time.sleep(3)
    r.cmd("forceload remove all")
    time.sleep(3)
    r.step(5)
    px = lazy_launch(c, n, payload_fuse=1)
    motion = r.vec("@e[tag=payload,limit=1]", "Motion")
    land_x = px + motion[0]
    tx = int(land_x)
    loaded_before = "passed" in r.cmd(f"execute if loaded {tx} -61 8").lower()
    release(c)
    t0 = time.time()
    r.step(1)
    dt = time.time() - t0
    alive = r.count("@e[tag=payload]")
    loaded_after = "passed" in r.cmd(f"execute if loaded {tx} -61 8").lower()
    r.cmd(f"forceload add {tx} 8")
    wait_loaded(tx, -61, 8)
    r.step(1)

    # count air blocks in the dirt/grass layers around the predicted landing point
    air = 0
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            if "passed" in r.cmd(f"execute if block {tx+dx} -61 {8+dz} air").lower():
                air += 1
    r.cmd(f"fill {tx-8} -63 0 {tx+8} -62 16 dirt replace air")
    r.cmd(f"fill {tx-8} -61 0 {tx+8} -61 16 grass_block replace air")
    record("unloaded_chunk_explosion", propellant=n, payload_motion=motion, predicted_landing_x=land_x,
           landing_chunk_loaded_before=loaded_before, payload_alive_after=alive,
           landing_chunk_loaded_after_tick=loaded_after,
           grass_blocks_destroyed_9x9=air, step_wall_time_s=round(dt, 3))


def t_max_tnt_per_tick(n=300):
    """Spigot's max-tnt-per-tick (default 100) defers TNT beyond the cap to later ticks."""
    reset()
    c = CX + 80
    forceload(c - 1, -1, c + 1, 1)
    x, y, z = bx(c, 8.5), 200.0, 8.5
    r.cmd(f"summon tnt {x} {y} {z} {{fuse:1,NoGravity:1b}}")
    for _ in range(n - 1):
        r.cmd(f"summon tnt {x} {y} {z} {{fuse:1,NoGravity:1b}}")
    counts = [r.count("@e[type=tnt]")]
    for _ in range(4):
        r.step(1)
        counts.append(r.count("@e[type=tnt]"))
    record("max_tnt_per_tick", spawned=n, tnt_alive_per_tick=counts)


def t_long_range(n=6000):
    """Cost and accuracy of moving one lazy-accelerated payload thousands of blocks in one tick."""
    reset()
    c = CX + 120
    px = lazy_launch(c, n, payload_fuse=400, y=300.0)
    motion = r.vec("@e[tag=payload,limit=1]", "Motion")
    release(c)
    t0 = time.time()
    r.step(1)
    dt = time.time() - t0
    mspt = r.cmd("mspt")
    still_home = r.count("@e[tag=payload]")
    ex = int(px + motion[0])
    r.cmd(f"forceload add {ex-32} -16 {ex+32} 31")
    wait_loaded(ex, 300, 8)
    time.sleep(2)
    pos = r.vec("@e[tag=payload,limit=1]", "Pos")
    record("long_range_flight", propellant=n, payload_motion=motion,
           expected_x=px + motion[0], payload_left_origin=(still_home == 0), pos_found_at_landing=pos,
           step_wall_time_s=round(dt, 3), paper_mspt=" ".join(mspt.split()))


def t_portal_ticket():
    """An item arriving through a nether portal loads 3x3 entity-ticking chunks + a lazy ring."""
    reset()
    ox, oy, oz = 19208, 100, 8          # overworld portal (chunk 1200, 0)
    nx, nz = ox // 8, oz                  # nether-side portal
    nether = "execute in minecraft:the_nether run "
    r.cmd(nether + f"forceload add {nx} {nz}")
    wait_loaded(ox, oy, oz)
    time.sleep(3)
    for pre, x in [("", ox), (nether, nx)]:
        r.cmd(pre + f"fill {x-3} {oy-2} {oz-3} {x+4} {oy+5} {oz+3} air")
        r.cmd(pre + f"fill {x-1} {oy-1} {oz} {x+2} {oy+3} {oz} obsidian")
        r.cmd(pre + f"fill {x} {oy} {oz} {x+1} {oy+2} {oz} nether_portal[axis=x]")
    # overworld side must exist so the arrival finds it; load it briefly then let it unload
    r.cmd(f"forceload add {ox} {oz}")
    time.sleep(2)
    r.cmd(f"fill {ox-1} {oy-1} {oz} {ox+2} {oy+3} {oz} obsidian")
    r.cmd(f"fill {ox} {oy} {oz} {ox+1} {oy+2} {oz} nether_portal[axis=x]")
    r.cmd("forceload remove all")
    r.cmd(nether + f"forceload add {nx} {nz}")
    time.sleep(3)
    r.cmd("tick unfreeze")
    time.sleep(2)
    loaded_before = "passed" in r.cmd(f"execute if loaded {ox} {oy} {oz}").lower()
    r.cmd(nether + f"summon item {nx+0.5} {oy+0.2} {oz+0.5} {{Item:{{id:\"minecraft:cobblestone\",count:1}}}}")
    time.sleep(3)
    r.cmd("tick freeze")
    arrived = r.count("@e[type=item]")
    cx = ox // 16
    probes = {}
    for d in range(0, 3):
        x = (cx + d) * 16 + 8.5
        r.cmd("kill @e[type=tnt]")
        tnt(x, oy + 20, 8.5, fuse=80, motion=(0, 0.5, 0))
        r.step(1)
        p = r.vec("@e[type=tnt,limit=1]", "Pos")
        probes[f"chunk +{d}"] = "entity-ticking" if p and p[1] > oy + 20 else "frozen"
    # lazy test on the ring: probe 0.5 into chunk +2, propellant 2.5 blocks west in chunk +1
    r.cmd("kill @e[type=tnt]")
    x2 = (cx + 2) * 16 + 0.5
    tnt(x2, oy + 20, 8.5, fuse=80, tag="probe")
    tnt(x2 - 2.5, oy + 20, 8.5, fuse=1)
    r.step(3)
    probes["chunk +2 knockback probe"] = {"pos": r.vec("@e[tag=probe,limit=1]", "Pos"),
                                          "motion": r.vec("@e[tag=probe,limit=1]", "Motion")}
    r.cmd("kill @e[type=tnt]")
    r.cmd(nether + "forceload remove all")
    record("portal_ticket", overworld_loaded_before=loaded_before, items_arrived=arrived, chunk_states=probes)


if __name__ == "__main__":
    tests = [t_axis_order, t_lazy_stasis, t_powder_snow, t_stab_order,
             t_unloaded_explosion, t_max_tnt_per_tick, t_long_range, t_portal_ticket]
    only = [a for a in sys.argv[1:] if not a.endswith(".json")]
    for t in tests:
        if only and t.__name__ not in only:
            continue
        try:
            t()
        except Exception as e:  # keep going; record the failure
            record(t.__name__, error=repr(e))
    reset()
    r.cmd("tick unfreeze")
    out = next((a for a in sys.argv[1:] if a.endswith(".json")), None)
    if out:
        with open(out, "w") as f:
            json.dump(RESULTS, f, indent=2)
