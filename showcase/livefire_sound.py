"""Soundtrack for livefire.html (44 s, 48 kHz stereo WAV), cued to its timeline.

Reuses the synth voices of soundtrack.py (everything above its "pad" section).
  python3 livefire_sound.py out.wav
"""
import json
import os
import sys
import wave

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "soundtrack.py")).read()
src = src[:src.index("# ---- pad")].replace("SR, DUR = 48000, 50.0", "SR, DUR = 48000, 44.0")
exec(src)   # defines np, SR, N, L, R, put, env, kick, hat, clap, impact, whoosh, click, tone, midi, BEAT

D = json.load(open(os.path.join(here, "lf", "data.json")))
T = dict(charge0=4, launch0=9, frozen0=17, release0=20, fall0=26, boom=31, crater0=32.4, end0=40)

# pad: Dm - Bb - F - C, low and wide, ducked around the boom
chords = [[50, 57, 62], [46, 53, 58], [53, 57, 60], [48, 55, 64]]
bar = 4 * BEAT
t, ci = 0.4, 0
while t < DUR - 1:
    for j, m in enumerate(chords[ci % 4]):
        put(tone(midi(m), 2 * bar + 0.4, "saw", a=0.8) * 0.03, t, pan=(j - 1) * 0.4)
    t += 2 * bar
    ci += 1
# drums from the charge sequence to the release, quiet through the fall
t, b = T["charge0"], 0
while t < T["release0"] - 0.1:
    put(kick(), t, 0.85)
    if b % 4 in (1, 3):
        put(clap(), t, 0.7, pan=0.1)
    put(hat(open_=(b % 2 == 1)), t + BEAT / 2, 0.7, pan=-0.3)
    t += BEAT
    b += 1
for c in [T["charge0"], T["launch0"], T["frozen0"], T["crater0"], T["end0"]]:
    put(whoosh(0.4), c - 0.3, 0.8, pan=0.2)
    put(impact(), c, 0.25)
put(impact()[: int(0.6 * SR)], 0.45, 0.4)
# staging pushes: one thump per TNT at its real time, compressed like the video
for ts, s in D["staged"]:
    if s:
        tv = T["charge0"] + ts / D["launch_start"] * (T["launch0"] - T["charge0"])
        put(kick(), tv, 0.55, pan=-0.2)
        put(click(900), tv, 0.5, pan=-0.2)
# wind charges: a soft tick per volley (compressed 11x)
n_v = D["nx"]
for i in range(n_v):
    tv = T["launch0"] + i * 0.6 / (D["launch_end"] - D["launch_start"]) * (T["frozen0"] - T["launch0"])
    put(click(2400 + (i * 53) % 700), tv, 0.35, pan=((i % 5) - 2) / 4)
# riser into the release, then the one-tick crack
n = int(2.6 * SR)
tt = np.arange(n) / SR
riser = np.sin(2 * np.pi * np.cumsum(np.linspace(160, 1500, n)) / SR) * (tt / tt[-1]) ** 2 * 0.12
put(riser + whoosh(2.6) * 0.5, T["release0"] - 2.0)
put(impact(), T["release0"] + 0.6, 0.9)
put(whoosh(3.0, up=False), T["release0"] + 0.7, 0.7, pan=0.3)
# fall: one click per game tick
for i in range(75):
    put(click(1600 + 8 * i), T["fall0"] + i * (T["boom"] - T["fall0"]) / 75, 0.55 + 0.4 * i / 75)
# detonation
put(impact(), T["boom"], 1.0)
put(impact(), T["boom"] + 0.03, 0.8, pan=0.5)
put(impact(), T["boom"] + 0.06, 0.8, pan=-0.5)
n = int(2.5 * SR)
rumble = np.convolve(rng.standard_normal(n), np.ones(400) / 400, "same") * np.exp(-np.arange(n) / SR / 0.8) * 1.2
put(rumble, T["boom"], 1.0)
put(tone(midi(62), 3.2, "sin", a=0.01) * 0.25, T["end0"] + 0.3)
put(tone(midi(69), 3.2, "sin", a=0.01) * 0.15, T["end0"] + 0.3)

d = int(0.375 * SR)
L[d:] += 0.22 * R[:-d]
R[d:] += 0.22 * L[:-d]
fade = np.ones(N)
fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
mix = np.stack([L, R], 1) * fade[:, None]
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= 0.89 / np.max(np.abs(mix))
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "livefire.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
