"""Soundtrack for nuke.html (36 s, 48 kHz stereo WAV), cued to its timeline.

Reuses the synth voices of soundtrack.py (everything above its "pad" section).
  python3 nuke_sound.py out.wav
"""
import os
import sys
import wave

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "soundtrack.py")).read()
src = src[:src.index("# ---- pad")].replace("SR, DUR = 48000, 50.0", "SR, DUR = 48000, 36.0")
exec(src)   # defines np, rng, SR, N, L, R, put, env, kick, hat, clap, impact, whoosh, click, tone, midi, BEAT

T = dict(ign=10, boostEnd=15, impact=25, reveal=26.5, end=32.5)
tick_t = lambda k: T["ign"] + k / 8 * (T["boostEnd"] - T["ign"])   # ticks 0-8 span 10-15 s

# low drone that builds to the impact, then opens up
chords = [[45, 52, 57], [41, 48, 57], [43, 50, 55], [40, 47, 52]]
t, ci = 0.3, 0
while t < DUR - 1:
    for j, m in enumerate(chords[ci % 4]):
        put(tone(midi(m), 4.6, "saw", a=1.2) * 0.03, t, pan=(j - 1) * 0.45)
    t += 4.0
    ci += 1
# heartbeat under the setup cards
for i in range(9):
    put(kick(), 4.4 + i * 0.62, 0.55)
for c in (4.4, 6.1, 7.8):
    put(whoosh(0.35), c - 0.25, 0.7, pan=-0.2)
    put(click(1500), c, 0.8)
put(impact()[: int(0.6 * SR)], 0.45, 0.45)
# expansion pairs: ticks 1-7, two charges each
for k in range(1, 8):
    put(impact(), tick_t(k), 0.75, pan=0.25)
    put(impact(), tick_t(k) + 0.012, 0.6, pan=-0.25)
    put(kick(), tick_t(k), 0.9)
# booster ring: 80 detonations at once
put(impact(), tick_t(7.2), 1.0)
for i in range(12):
    put(impact()[: int(0.4 * SR)], tick_t(7.2) + i * 0.011, 0.35, pan=((i % 5) - 2) / 3)
# flight: rising wind, a tick every game tick at the compressed rate
n = int((T["impact"] - T["boostEnd"]) * SR)
tt = np.arange(n) / SR
rise = np.sin(2 * np.pi * np.cumsum(np.linspace(90, 900, n)) / SR) * (tt / tt[-1]) ** 2 * 0.09
put(rise + whoosh(T["impact"] - T["boostEnd"]) * 0.45, T["boostEnd"])
for k in range(8, 80):
    put(click(1300 + 9 * k), T["boostEnd"] + (k - 8) / 71 * (T["impact"] - T["boostEnd"]), 0.25 + 0.45 * (k - 8) / 71)
# impact: 80 craters in a rolling crackle, then the rumble
put(impact(), T["impact"], 1.0)
for i in range(80):
    put(impact()[: int(0.5 * SR)], T["impact"] + rng.uniform(0, 0.45), 0.22, pan=float(np.cos(i / 80 * 2 * np.pi)) * 0.8)
n = int(4.0 * SR)
rumble = np.convolve(rng.standard_normal(n), np.ones(500) / 500, "same") * np.exp(-np.arange(n) / SR / 1.3) * 1.4
put(rumble, T["impact"], 1.0)
# reveal + end stings
put(tone(midi(57), 3.5, "sin", a=0.05) * 0.2, T["reveal"] + 1.5)
put(tone(midi(64), 3.5, "sin", a=0.05) * 0.14, T["reveal"] + 2.6)
put(tone(midi(57), 3.2, "sin", a=0.01) * 0.25, T["end"] + 0.3)
put(tone(midi(69), 3.2, "sin", a=0.01) * 0.15, T["end"] + 0.3)
put(impact(), T["end"] + 0.3, 0.4)

d = int(0.375 * SR)
L[d:] += 0.22 * R[:-d]
R[d:] += 0.22 * L[:-d]
fade = np.ones(N)
fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
mix = np.stack([L, R], 1) * fade[:, None]
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= 0.89 / np.max(np.abs(mix))
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "nuke.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
