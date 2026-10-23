"""Paste a .litematic into the running server over RCON with `setblock ... strict`.

    python3 paste.py <file.litematic> <ox> <oy> <oz> [dimension]

`strict` places blocks without neighbour updates, so redstone keeps exactly the states
stored in the schematic (Litematica's chat-command pasting breaks redstone for the same
reason). Commands go into a datapack function (tile-entity NBT is far longer than an RCON
packet allows), then every block is verified; mismatches go to paste-errors.log.
Needs MC_SERVER=<server dir>.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "paper-tests"))
from litematic import load  # noqa: E402
from rcon import Rcon  # noqa: E402


WORLD = os.environ.get("MC_WORLD", "world")


def main():
    import nbtlib
    path, ox, oy, oz = sys.argv[1], *map(int, sys.argv[2:5])
    dim = sys.argv[5] if len(sys.argv) > 5 else "minecraft:overworld"
    name = os.path.splitext(os.path.basename(path))[0].lower()
    name = "".join(c if c.isalnum() else "_" for c in name)
    s = load(path)
    (x0, y0, z0), (x1, y1, z1) = s.bounds()
    lines = []
    for y in range(y0, y1 + 1):
        lines.append(f"fill {ox + x0} {oy + y} {oz + z0} {ox + x1} {oy + y} {oz + z1} air strict")
    for (x, y, z), st in sorted(s.blocks.items(), key=lambda kv: kv[0][1]):
        nbt = s.tiles.get((x, y, z))
        tag = nbt.snbt() if nbt is not None and len(nbt) else ""
        lines.append(f"setblock {ox + x} {oy + y} {oz + z} {st}{tag} strict")
    for (x, y, z), e in s.entities:
        body = nbtlib.Compound({k: v for k, v in e.items() if k != "id"})
        lines.append(f"summon {e['id']} {ox + x} {oy + y} {oz + z} {body.snbt()}")
    # datapack function: no RCON packet-size limit, runs in a single tick
    dp = os.path.join(os.environ["MC_SERVER"], WORLD, "datapacks", "osctools")
    fn = os.path.join(dp, "data", "osctools", "function")
    os.makedirs(fn, exist_ok=True)
    with open(os.path.join(dp, "pack.mcmeta"), "w") as f:
        f.write('{"pack":{"description":"osc tools","pack_format":121,"min_format":121,"max_format":121}}')
    with open(os.path.join(fn, f"paste_{name}.mcfunction"), "w") as f:
        f.write("\n".join(lines) + "\n")
    r = Rcon()
    pre = f"execute in {dim} run "
    r.cmd("tick freeze")
    r.cmd(pre + f"forceload add {ox + x0 - 16} {oz + z0 - 16} {ox + x1 + 16} {oz + z1 + 16}")
    time.sleep(4)
    print("reload:", r.cmd("minecraft:reload")[:200])
    time.sleep(3)
    print("run:", r.cmd(pre + f"function osctools:paste_{name}")[:300])
    # verify every block
    bad = []
    for (x, y, z), st in s.blocks.items():
        out = r.cmd(pre + f"execute if block {ox + x} {oy + y} {oz + z} {st}")
        if "passed" not in out.lower():
            bad.append(f"{(x, y, z)} {st} -> {out[:120]}")
    with open("paste-errors.log", "w") as f:
        f.write("\n".join(bad))
    print(f"{s.name}: {len(s.blocks) - len(bad)}/{len(s.blocks)} blocks verified, {len(bad)} mismatches; "
          f"{len(s.entities)} entities summoned")


if __name__ == "__main__":
    main()
