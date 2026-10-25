"""Volume IV, the video atlas: one page per harvested video (research/videos/<id>)."""
import html
import json
import os
import re

from PIL import Image

E = html.escape
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VID = os.path.join(ROOT, "research", "videos")

ORDER = ["cubicmetre", "wmc", "tkparmaa", "dumbrock", "paper", "others"]
TITLES = {"cubicmetre": "cubicmetre", "wmc": "White Mc (WMC)", "tkparmaa": "TK.Paarmaa", "dumbrock": "TheeDumbRock",
          "paper": "Paper ports", "others": "Builders, tutorials & search"}
SHORT = {"cubicmetre": "cubicmetre", "wmc": "WMC", "tkparmaa": "TK.Paarmaa", "dumbrock": "DumbRock",
         "paper": "Paper ports", "others": "Others"}
COLORS = {"cubicmetre": "#e5673b", "wmc": "#4fae6a", "tkparmaa": "#3f9ad6", "dumbrock": "#b88ad9",
          "paper": "#e9b23a", "others": "#d0457a"}
DEKS = {
    "cubicmetre": "The inventor of the orbital strike cannon: from the 2023 original to the Mk.6 with its "
                  "fire-control ROM, wireless link and nuclear payloads, plus a decade of TNT engineering around it.",
    "wmc": "Lazy-chunk accelerators, pearl cannons and wither cannons: the same physics pushed in other directions.",
    "tkparmaa": "Compact cannons and the CE line, built for players who want an OSC without a megaproject.",
    "dumbrock": "The smallest cannons in the atlas: TOSC, WOSC and MOSC, where a whole cannon fits in a few blocks.",
    "paper": "Making orbital strikes work on Paper servers, where piston duplication, TNT limits and "
             "chunk unloading behave differently.",
    "others": "Showcases, tutorials and every other orbital strike video the searches turned up.",
}
TERMS = ["lazy chunk", "entity processing", "chunk loader", "portal", "nether", "ender pearl", "pearl", "wind charge",
         "powder snow", "tnt", "duper", "duplication", "piston", "observer", "comparator", "repeater", "dispenser",
         "fire control", "payload", "nuke", "stab", "fuse", "velocity", "knockback", "wireless", "hopper",
         "minecart", "flying machine", "slime", "honey", "paper", "spigot", "lag", "coordinates", "accuracy",
         "anvil", "wither", "breeze", "blast", "crater", "momentum", "stasis", "redstone", "schematic", "litematica"]
_meta = {}


def meta(vid):
    if vid not in _meta:
        p = os.path.join(VID, vid, "meta.json")
        _meta[vid] = json.load(open(p)) if os.path.exists(p) else {}
    return _meta[vid]


def group_of(r):
    c = r["creator"].lower().replace(".", "")
    if c in ("cubicmetre", "wmc", "tkparmaa", "dumbrock"):
        return c
    return "paper" if r["group"] == "paper" else "others"


def key_terms(text, n=9):
    t = text.lower()
    found = [(t.count(k), k) for k in TERMS if t.count(k)]
    return [k for c, k in sorted(found, reverse=True)[:n]]


def excerpt(text, words=165):
    """The opening of the transcript, timestamps kept, cut at a sentence end where possible."""
    text = html.unescape(text)
    out, n = [], 0
    for line in text.splitlines():
        m = re.match(r"\[(\d\d:\d\d(?::\d\d)?)\]\s*(.*)", line)
        if not m:
            continue
        ws = m.group(2).split()
        take = ws[: max(0, words - n)]
        out.append(f"<b>[{E(m.group(1))}]</b> {E(' '.join(take))}")
        n += len(take)
        if n >= words:
            break
    s = " ".join(out)
    cut = max(s.rfind(". "), s.rfind("? "), s.rfind("! "))
    return (s[: cut + 1] if cut > len(s) * .6 else s) + " …"


def video_page(r, no, sheets_dir, color):
    vid = r["id"]
    m = meta(vid)
    d = os.path.join(VID, vid)
    sheet = None
    for cand in ("sheet-02.jpg", "sheet-01.jpg", "thumb.jpg"):
        src = os.path.join(d, cand)
        if os.path.exists(src):
            dst = os.path.join(sheets_dir, f"{vid}.jpg")
            if not os.path.exists(dst):
                im = Image.open(src).convert("RGB")
                im.thumbnail((1150, 1150))
                im.save(dst, quality=76)
            sheet = f"vsheets/{vid}.jpg"
            break
    tx = open(os.path.join(d, "transcript.txt")).read() if os.path.exists(os.path.join(d, "transcript.txt")) else ""
    date = m.get("upload_date") or ""
    date = f"{date[:4]}-{date[4:6]}-{date[6:]}" if len(date) == 8 else "—"
    dur = int(m.get("duration") or 0)
    views = m.get("view_count")
    views = f"{int(views):,}" if views and views != "None" else "—"
    desc = re.sub(r"https?://\S+", "", m.get("description") or "").strip()
    desc = E(desc[:420]) + ("…" if len(desc) > 420 else "")
    terms = "".join(f"<span>{E(t)}</span>" for t in key_terms(tx))
    return f'''<div class="head" style="--chan:{color}"><div class="ch">{E(m.get("channel") or r["creator"])} · {E(r["group"])}</div>
      <div class="ti">{E(m.get("title") or r["title"])}</div><div class="no">{no:03d}</div>
      <div class="meta"><span>uploaded <b>{date}</b></span><span>length <b>{dur // 60}:{dur % 60:02d}</b></span>
        <span>views <b>{views}</b></span><span>id <b>{E(vid)}</b></span></div></div>
      <div class="sheet" style="--chan:{color}">{f'<img src="{sheet}">' if sheet else ''}<div class="lbl">STORYBOARD FRAMES</div></div>
      <div class="cols"><div class="tx">{excerpt(tx) if tx else "<i>No transcript available.</i>"}</div>
        <div class="side"><h4>What it covers</h4><div class="terms">{terms or "<span>—</span>"}</div>
          <h4>From the description</h4><div class="desc">{desc or "—"}</div>
          <div class="url">{E(m.get("webpage_url") or "https://youtu.be/" + vid)}</div></div></div>'''


INTRO = [
    '<h2>How to read <em>the atlas</em></h2>',
    '<p class="lead">This volume is the reading list behind the other four. Every video here was downloaded, '
    'transcribed and sampled frame by frame while I worked out how orbital strike cannons work: 260 of them, '
    'from cubicmetre\'s first 2023 cannon to the Paper ports and showcase videos of 2026.</p>',
    '<p>Each page shows one video. The header gives the channel, the title, the upload date, the length and the '
    'view count at the time it was harvested. The large image is a sheet of storyboard frames: thumbnails that '
    'YouTube samples evenly through the video, so a whole build or test can be skimmed at a glance. Below it is the '
    'opening of the transcript with its timestamps, and on the right the orbital strike terms the video uses most '
    '(counted over the whole transcript) and the start of its description.</p>',
    '<h3>Chapters</h3>',
    '<p>The chapters follow the people who built this field. cubicmetre comes first: he invented the orbital strike '
    'cannon and his channel is also a decade of TNT engineering, so all of it is here. WMC, TK.Paarmaa and '
    'TheeDumbRock follow, then the Paper ports, then everyone else. Within a chapter, videos run in upload order.</p>',
    '<div class="note"><b>Sources</b><p>Titles, descriptions, frames and transcript excerpts belong to the video '
    'creators and are quoted here for study. The full videos are at the address printed on each page.</p></div>',
]
