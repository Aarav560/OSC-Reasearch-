"""Small SVG chart and diagram kit for the Codex (no plotting library needed)."""
import html
import math

E = html.escape
INK, PAPER, CORAL, GOLD, NAVY, CYAN, GREEN, PLUM, MUTE = "#15120f", "#fffaf0", "#e5673b", "#e9b23a", "#0b2a4a", "#3f9ad6", "#4fae6a", "#8e5bb0", "#8a7f6f"
PALETTE = [CORAL, CYAN, GREEN, GOLD, PLUM, "#d0457a", "#2c7a7b", INK]


def nice_ticks(lo, hi, n=5):
    if hi == lo:
        hi = lo + 1
    span = hi - lo
    step = 10 ** math.floor(math.log10(span / n))
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= n:
            step *= m
            break
    start = math.floor(lo / step) * step
    ticks = []
    v = start
    while v <= hi + step * .001:
        if v >= lo - step * .001:
            ticks.append(round(v, 10))
        v += step
    return ticks


def fmt(v):
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if v == int(v):
        return str(int(v))
    return f"{v:.3g}"


def chart(series, xlabel="", ylabel="", w=640, h=380, kind="line", xlim=None, ylim=None, legend=True, hlines=(), notes=()):
    """series: [(label, [(x, y), ...], colour)]; kind line | scatter | step."""
    L, R, T, B = 66, 18, 18, 52
    xs = [p[0] for _, pts, *_ in series for p in pts]
    ys = [p[1] for _, pts, *_ in series for p in pts] + [hv for hv, *_ in hlines]
    x0, x1 = xlim or (min(xs), max(xs))
    y0, y1 = ylim or (min(0, min(ys)), max(ys) * 1.08 if max(ys) > 0 else 1)
    X = lambda v: L + (v - x0) / ((x1 - x0) or 1) * (w - L - R)
    Y = lambda v: h - B - (v - y0) / ((y1 - y0) or 1) * (h - T - B)
    o = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" font-family="JetBrains Mono, monospace">']
    for t in nice_ticks(y0, y1):
        o.append(f'<line x1="{L}" x2="{w - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{INK}" stroke-opacity=".12"/>'
                 f'<text x="{L - 6}" y="{Y(t) + 3:.1f}" font-size="10" text-anchor="end" fill="{INK}">{fmt(t)}</text>')
    for t in nice_ticks(x0, x1, 6):
        o.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{h - B}" y2="{h - B + 4}" stroke="{INK}"/>'
                 f'<text x="{X(t):.1f}" y="{h - B + 16}" font-size="10" text-anchor="middle" fill="{INK}">{fmt(t)}</text>')
    o.append(f'<line x1="{L}" x2="{w - R}" y1="{h - B}" y2="{h - B}" stroke="{INK}" stroke-width="2"/>'
             f'<line x1="{L}" x2="{L}" y1="{T}" y2="{h - B}" stroke="{INK}" stroke-width="2"/>')
    for hv, lab, col in hlines:
        o.append(f'<line x1="{L}" x2="{w - R}" y1="{Y(hv):.1f}" y2="{Y(hv):.1f}" stroke="{col}" stroke-width="2" stroke-dasharray="7 5"/>'
                 f'<text x="{w - R - 4}" y="{Y(hv) - 5:.1f}" font-size="10" text-anchor="end" fill="{col}" font-weight="700">{E(lab)}</text>')
    for i, (label, pts, *rest) in enumerate(series):
        col = rest[0] if rest else PALETTE[i % len(PALETTE)]
        if kind in ("line", "step") and len(pts) > 1:
            if kind == "step":
                d = f"M{X(pts[0][0]):.1f},{Y(pts[0][1]):.1f}" + "".join(f"H{X(x):.1f}V{Y(y):.1f}" for x, y in pts[1:])
            else:
                d = "M" + " L".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
            o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3" stroke-linejoin="round"/>')
        if kind == "scatter" or len(pts) < 30:
            o += [f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{4 if kind == "scatter" else 3}" fill="{col}" stroke="{INK}" stroke-width=".8"/>' for x, y in pts]
    for x, y, txt in notes:
        o.append(f'<text x="{X(x) + 6:.1f}" y="{Y(y) - 6:.1f}" font-size="10" fill="{INK}" font-weight="700">{E(txt)}</text>')
    o.append(f'<text x="{(L + w - R) / 2}" y="{h - 12}" font-size="11" text-anchor="middle" fill="{INK}" font-weight="700">{E(xlabel)}</text>'
             f'<text transform="translate(16 {(T + h - B) / 2}) rotate(-90)" font-size="11" text-anchor="middle" fill="{INK}" font-weight="700">{E(ylabel)}</text>')
    if legend and len(series) > 1:
        lx, ly = L + 12, T + 8
        for i, (label, pts, *rest) in enumerate(series):
            col = rest[0] if rest else PALETTE[i % len(PALETTE)]
            o.append(f'<rect x="{lx}" y="{ly + i * 16}" width="14" height="10" fill="{col}"/><text x="{lx + 20}" y="{ly + i * 16 + 9}" font-size="10" fill="{INK}">{E(label)}</text>')
    o.append("</svg>")
    return "".join(o)


def bars(items, xlabel="", w=640, h=None, color=CORAL, fmtv=fmt, ref=None):
    """Horizontal bars: items [(label, value)] or [(label, value, colour)]."""
    rowh = 26
    h = h or 30 + rowh * len(items) + 30
    L, R = 210, 70
    vmax = max(abs(it[1]) for it in items) or 1
    if ref:
        vmax = max(vmax, ref[0])
    o = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" font-family="JetBrains Mono, monospace">']
    for i, it in enumerate(items):
        lab, v = it[0], it[1]
        col = it[2] if len(it) > 2 else color
        y = 20 + i * rowh
        bw = abs(v) / vmax * (w - L - R)
        o.append(f'<text x="{L - 8}" y="{y + 15}" font-size="11" text-anchor="end" fill="{INK}">{E(lab)}</text>'
                 f'<rect x="{L}" y="{y + 3}" width="{bw:.1f}" height="{rowh - 8}" fill="{col}" stroke="{INK}" stroke-width="1"/>'
                 f'<text x="{L + bw + 6:.1f}" y="{y + 15}" font-size="11" fill="{INK}" font-weight="700">{E(fmtv(v))}</text>')
    if ref:
        x = L + ref[0] / vmax * (w - L - R)
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="12" y2="{h - 26}" stroke="{INK}" stroke-width="2" stroke-dasharray="6 4"/>'
                 f'<text x="{x:.1f}" y="{h - 10}" font-size="10" text-anchor="middle" fill="{INK}" font-weight="700">{E(ref[1])}</text>')
    if xlabel:
        o.append(f'<text x="{(L + w - R) / 2}" y="{h - 4}" font-size="10" text-anchor="middle" fill="{MUTE}">{E(xlabel)}</text>')
    o.append("</svg>")
    return "".join(o)


def svg(w, h, body, bg=None):
    b = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" font-family="JetBrains Mono, monospace">{b}{body}</svg>'


def text(x, y, s, size=12, col=INK, anchor="start", weight=400, family=None):
    fam = f' font-family="{family}"' if family else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}"{fam}>{E(s)}</text>'


def arrowhead_defs(col=INK, id_="ah"):
    return f'<defs><marker id="{id_}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker></defs>'


def line(x1, y1, x2, y2, col=INK, w=2, dash=None, arrow=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a = f' marker-end="url(#{arrow})"' if arrow else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"{d}{a}/>'


def rect(x, y, w, h, fill, stroke=INK, sw=1.5, op=1, rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" fill-opacity="{op}" rx="{rx}"/>'


class Block(str):
    """An HTML block that can be concatenated with lists of blocks: [a] + Block + [b]."""
    def __add__(self, other):
        return [str(self)] + other if isinstance(other, list) else Block(str.__add__(self, other))

    def __radd__(self, other):
        return other + [str(self)] if isinstance(other, list) else Block(other + str(self))


def fig(svg_markup, caption, label="Fig.", dark=False):
    return Block(f'<div class="fig{" dark" if dark else ""}"><div class="art">{svg_markup}</div>'
                 f'<div class="cap"><b>{E(label)}</b>{caption}</div></div>')


def table(head, rows):
    th = "".join(f"<th>{E(str(h))}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{E(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return Block(f'<table class="data"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>')
