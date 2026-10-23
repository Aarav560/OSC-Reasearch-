"""Helpers for tools/harvest.sh: trim metadata, flatten VTT captions, build contact sheets."""
import json
import os
import re
import sys


def meta(src, dst):
    with open(src, encoding="utf-8") as f:
        d = json.load(f)
    keep = ["id", "title", "channel", "channel_url", "upload_date", "duration",
            "view_count", "like_count", "description", "chapters", "tags", "webpage_url"]
    out = {k: d.get(k) for k in keep}
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


TS = re.compile(r"(\d+):(\d\d):(\d\d)\.\d+ -->")


def vtt(src, dst):
    """Auto-captions repeat each line as it scrolls; keep each new line once with its start time."""
    lines, seen, t = [], set(), 0
    with open(src, encoding="utf-8") as f:
        for raw in f:
            m = TS.match(raw)
            if m:
                h, mi, s = map(int, m.groups())
                t = h * 3600 + mi * 60 + s
                continue
            txt = re.sub(r"<[^>]+>", "", raw).strip()
            if not txt or txt in ("WEBVTT",) or txt.startswith(("Kind:", "Language:")):
                continue
            if txt in seen:
                continue
            seen.add(txt)
            lines.append((t, txt))
    # merge into ~30 s paragraphs
    paras, cur, start = [], [], None
    for t, txt in lines:
        if start is None:
            start = t
        cur.append(txt)
        if t - start >= 30:
            paras.append((start, " ".join(cur)))
            cur, start = [], None
    if cur:
        paras.append((start, " ".join(cur)))
    with open(dst, "w", encoding="utf-8") as f:
        for t, p in paras:
            f.write(f"[{t // 60:02d}:{t % 60:02d}] {p}\n\n")


def storyboard(mhtml, info, frames_dir):
    """Cut the sb0 storyboard grids into single frames named by their start second."""
    import email
    import io
    from PIL import Image
    with open(info, encoding="utf-8") as f:
        fmt = next(x for x in json.load(f)["formats"] if x["format_id"] == "sb0")
    with open(mhtml, "rb") as f:
        msg = email.message_from_bytes(f.read())
    grids = [p.get_payload(decode=True) for p in msg.walk() if p.get_content_type() == "image/jpeg"]
    w, h, rows, cols = fmt["width"], fmt["height"], fmt["rows"], fmt["columns"]
    per = rows * cols
    t0 = 0.0
    for grid, frag in zip(grids, fmt["fragments"]):
        im = Image.open(io.BytesIO(grid)).convert("RGB")
        n = min(per, int(im.width // w) * int(im.height // h))
        dt = frag["duration"] / per
        for i in range(n):
            x, y = (i % cols) * w, (i // cols) * h
            if y + h > im.height:
                break
            tile = im.crop((x, y, x + w, y + h))
            if tile.getextrema()[0][1] < 8:  # blank padding after the last frame
                continue
            tile.save(os.path.join(frames_dir, f"t{int(t0 + i * dt):05d}.jpg"), quality=90)
        t0 += frag["duration"]


def sheets(frames_dir, out_dir):
    from PIL import Image, ImageDraw
    files = sorted(x for x in os.listdir(frames_dir) if x.endswith(".jpg"))
    cols, rows, w = 6, 8, 320
    per = cols * rows
    for s in range(0, len(files), per):
        chunk = files[s:s + per]
        h = None
        tiles = []
        for i, fn in enumerate(chunk):
            im = Image.open(os.path.join(frames_dir, fn)).convert("RGB")
            im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
            h = h or im.height
            t = int(fn[1:6])
            d = ImageDraw.Draw(im)
            label = f"{t // 60:02d}:{t % 60:02d}"
            d.rectangle([0, 0, 52, 14], fill=(0, 0, 0))
            d.text((3, 1), label, fill=(255, 255, 0))
            tiles.append(im)
        sheet = Image.new("RGB", (cols * w, rows * h), (0, 0, 0))
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % cols) * w, (i // cols) * h))
        sheet.save(os.path.join(out_dir, f"sheet-{s // per + 1:02d}.jpg"), quality=60)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"meta": meta, "vtt": vtt, "storyboard": storyboard, "sheets": sheets}[cmd](*args)
