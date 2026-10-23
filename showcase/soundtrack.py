"""Synthesize the reel soundtrack (50 s, 48 kHz stereo WAV) with numpy only.

Cues line up with the scene cuts in reel.html.
  python3 soundtrack.py out.wav
"""
import sys
import wave

import numpy as np

SR, DUR = 48000, 50.0
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(7)
CUTS = [3.6, 7.0, 9.2, 21.0, 25.0, 29.0, 34.0, 39.4, 43.0, 46.4]
BPM = 120
BEAT = 60 / BPM


def put(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * (1 - max(0, pan))
    R[i:i + len(sig)] += sig * (1 + min(0, pan))


def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / d)


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 42 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.16) * 0.95


def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # crude high-pass
    return x * env(n, 0.001, 0.06 if open_ else 0.012) * 0.16


def clap():
    n = int(0.25 * SR)
    x = rng.standard_normal(n)
    e = sum(env(n, 0.001, 0.012) * (np.arange(n) >= int(k * SR)) for k in (0, 0.011, 0.023)) + env(n, 0.001, 0.09)
    return x * e * 0.12


def impact():
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-t * 6)) / SR) * np.exp(-t * 1.6)
    noise = rng.standard_normal(n) * np.exp(-t * 5) * 0.35
    return (sub + noise) * 0.9


def whoosh(len_s=0.45, up=True):
    n = int(len_s * SR)
    x = rng.standard_normal(n)
    # sweep a one-pole low-pass cutoff
    cut = np.linspace(0.02, 0.5, n) if up else np.linspace(0.5, 0.02, n)
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc += cut[i] * (x[i] - acc)
        y[i] = acc
    shape = np.sin(np.linspace(0, np.pi, n)) ** 2
    return y * shape * 0.5


def click(f=3200):
    n = int(0.012 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * env(n, 0.0005, 0.003) * 0.25


def tone(freq, dur, kind="saw", a=0.4, d=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "saw":
        x = sum(np.sin(2 * np.pi * freq * k * t + k) / k for k in range(1, 9))
    else:
        x = np.sin(2 * np.pi * freq * t)
    e = np.minimum(t / a, 1) * np.minimum((dur - t) / 0.6, 1)
    return x * np.clip(e, 0, 1)


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---- pad: Am - F - C - G, two bars each, from 3.6 s -----------------------
chords = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62]]
bar = 4 * BEAT
t = 3.6
ci = 0
while t < DUR - 1:
    for j, m in enumerate(chords[ci % 4]):
        sig = tone(midi(m), 2 * bar + 0.4, "saw", a=0.6) * 0.035
        put(sig, t, pan=(j - 1) * 0.35)
    # bass on the root, eighth-note pulse
    root = midi(chords[ci % 4][0] - 12)
    for k in range(16):
        bt = t + k * BEAT / 2
        if 18.9 < bt < 21.0:
            continue
        n = int(BEAT / 2 * SR * 0.9)
        tt = np.arange(n) / SR
        put(np.sin(2 * np.pi * root * tt) * env(n, 0.004, 0.12) * 0.22, bt)
    t += 2 * bar
    ci += 1

# ---- drums ---------------------------------------------------------------
t = 3.6
b = 0
while t < 46.4:
    quiet = 17.0 < t < 21.0 or 39.4 <= t < 43.0
    if not quiet or b % 4 == 0:
        put(kick(), t, 0.9)
    if b % 4 in (1, 3) and not quiet:
        put(clap(), t, 0.9, pan=0.1)
    put(hat(open_=(b % 2 == 1)), t + BEAT / 2, 0.8, pan=-0.3)
    t += BEAT
    b += 1

# ---- cues ------------------------------------------------------------------
for t0 in (0.0, 1.2, 2.4):  # intro punch cards
    put(kick(), t0, 1.0)
    put(impact()[: int(0.6 * SR)], t0, 0.35)
for c in CUTS:
    put(whoosh(0.4), c - 0.3, 0.9, pan=0.2)
    put(impact(), c, 0.28)
# terminal typing clicks
for i in range(140):
    put(click(2800 + (i * 37) % 900), 3.7 + i * 0.022, 0.6, pan=((i % 7) - 3) / 6)
# riser into the launch, then the boom
n = int(1.9 * SR)
tt = np.arange(n) / SR
riser = np.sin(2 * np.pi * np.cumsum(np.linspace(180, 1400, n)) / SR) * (tt / tt[-1]) ** 2 * 0.12
put(riser + whoosh(1.9) * 0.6, 17.05)
put(impact(), 18.95, 1.0)
put(impact(), 18.95, 0.6, pan=0.4)
# split-flap ticks
for i in range(28):
    put(click(1800), 21.1 + i * 0.018, 0.9)
# checklist ticks
for i in range(8):
    put(click(1400 if i < 7 else 900) * 2, 34.0 + 0.7 + i * 0.38, 0.8)
# final sting
put(tone(midi(69), 3.2, "sin", a=0.01) * 0.25, 46.4)
put(tone(midi(76), 3.2, "sin", a=0.01) * 0.15, 46.4)
put(impact(), 46.4, 0.5)

# ---- simple stereo delay "space" + master ----------------------------------
d = int(0.375 * SR)
L[d:] += 0.22 * R[:-d]
R[d:] += 0.22 * L[:-d]
fade = np.ones(N)
fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
mix = np.stack([L, R], 1) * fade[:, None]
mix = np.tanh(mix * 1.4) / np.tanh(1.4)  # soft clip
mix *= 0.89 / np.max(np.abs(mix))
pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "soundtrack.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
