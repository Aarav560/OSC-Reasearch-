"""Minimal Source-RCON client for driving a Paper test server."""
import os
import re
import socket
import struct
import time


class Rcon:
    def __init__(self, host="127.0.0.1", port=None, password="osctest"):
        port = port or int(os.environ.get("RCON_PORT", 25575))  # 25576 = vanilla A/B server
        self.s = socket.create_connection((host, port), timeout=30)
        self.rid = 0
        self._send(3, password)
        if self._recv()[0] == -1:
            raise RuntimeError("rcon auth failed")

    def _send(self, kind, body):
        self.rid += 1
        data = struct.pack("<ii", self.rid, kind) + body.encode() + b"\0\0"
        self.s.sendall(struct.pack("<i", len(data)) + data)

    def _read(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.s.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("rcon closed")
            buf += chunk
        return buf

    def _recv(self):
        (n,) = struct.unpack("<i", self._read(4))
        data = self._read(n)
        rid, _ = struct.unpack("<ii", data[:8])
        return rid, data[8:-2].decode(errors="replace")

    def cmd(self, c):
        """Run a command; responses over 4 KB arrive split, so a marker request (an empty
        command, answered by both Paper and vanilla with its own id) ends the read."""
        self._send(2, c)
        cid = self.rid
        if os.environ.get("RCON_MARKER", "1") == "0":  # vanilla drops clients that pipeline
            return self._recv()[1]
        self._send(2, "")
        mid = self.rid
        parts = []
        while True:
            rid, body = self._recv()
            if rid == mid:
                break
            if rid == cid:
                parts.append(body)
        return "".join(parts)

    def cmds(self, *cs):
        return [self.cmd(c) for c in cs]

    # --- helpers -------------------------------------------------------
    def step(self, n=1):
        """Advance exactly n game ticks while frozen and wait for them to finish."""
        self.cmd(f"tick step {n}")
        time.sleep(0.06 * n + 0.15)

    NUM = r"(-?[\d.]+(?:E-?\d+)?)d"

    def vec(self, selector, path):
        out = self.cmd(f"data get entity {selector} {path}")
        m = re.findall(self.NUM, out)
        return tuple(float(x) for x in m) if m else None

    def num(self, selector, path):
        out = self.cmd(f"data get entity {selector} {path}")
        m = re.search(r"(-?[\d.]+(?:E-?\d+)?)[bsdfL]?$", out.strip())
        return float(m.group(1)) if m else None

    def count(self, selector):
        out = self.cmd(f"execute if entity {selector}")
        m = re.search(r"Count: (\d+)", out)
        return int(m.group(1)) if m else 0
