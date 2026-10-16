"""Banda sonora sintetizada (sin samples externos) para el video de Ligier.

Genera output/soundtrack.wav: 120 BPM, progresión Am-F-C-G, pads, bajo,
bombo, hi-hats, arpegio, whooshes en cada transición e impactos.
Uso: python3 music.py
"""
import os
import wave
import numpy as np

SR = 44100
DUR = 54.0
BEAT = 0.5
BOUNDS = [0, 5.0, 10.5, 17.0, 20.5, 29.5, 38.5, 47.5, 54.0]  # = SCENES en index.html
N = int(SR * DUR)
t = np.arange(N) / SR
L = np.zeros(N)
R = np.zeros(N)

rng = np.random.default_rng(7)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * gain * (1 - pan) ** 0.5
    R[i:i + len(sig)] += sig * gain * (1 + pan) ** 0.5


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= np.exp(-((np.log(f + 1) - np.log((lo + hi) / 2)) ** 2) / (2 * (np.log(hi / lo) / 2) ** 2))
    return np.fft.irfft(X, len(x))


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


# acordes (Am F C G), dos compases por acorde... 1 acorde = 2 s
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 55, 60, 64], [55, 59, 62]]
BAR = 4 * BEAT


def energy(x):
    """intensidad de la mezcla según la escena"""
    if x < 5:
        return 0.0       # intro: solo pad
    if 29.5 <= x < 38.5:
        return 0.55      # tracker (noche): más tranquilo
    if x >= 47.5:
        return 0.0       # cierre
    return 1.0


# ---- pad
for k in range(int(DUR / BAR) + 1):
    st = k * BAR
    ch = CHORDS[k % 4]
    n = int((BAR + 0.6) * SR)
    tt = np.arange(n) / SR
    sig = np.zeros(n)
    for m in ch:
        for det in (-0.12, 0.0, 0.11):
            f = hz(m + det)
            sig += np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt + 1)
    sig *= env(n, 0.5, 0.7) / (len(ch) * 3)
    add(sig, st, 0.16)

# ---- bajo (corcheas)
for k in range(int(DUR / (BEAT / 2))):
    st = k * BEAT / 2
    e = energy(st)
    if e == 0:
        continue
    root = CHORDS[int(st // BAR) % 4][0] - 24
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    f = hz(root)
    sig = np.sin(2 * np.pi * f * tt) + 0.35 * np.sign(np.sin(2 * np.pi * f * tt)) * 0.4
    sig *= np.exp(-tt * 9)
    add(sig, st, 0.22 * e)

# ---- bombo
for k in range(int(DUR / BEAT)):
    st = k * BEAT
    e = energy(st)
    if e == 0 or (e < 1 and k % 2):
        continue
    n = int(0.4 * SR)
    tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(45 + 110 * np.exp(-tt * 30)) / SR
    sig = np.sin(ph) * np.exp(-tt * 7)
    add(sig, st, 0.55)

# ---- hi-hats (contratiempos) + clap en 2 y 4
for k in range(int(DUR / (BEAT / 2))):
    st = k * BEAT / 2
    e = energy(st)
    if e == 0:
        continue
    n = int(0.06 * SR)
    noise = np.diff(rng.standard_normal(n + 1))
    hat = noise * np.exp(-np.arange(n) / SR * 60)
    add(hat, st + 0.0, (0.05 if k % 2 else 0.025) * e, pan=0.3)
    if k % 4 == 2 and e == 1:
        n2 = int(0.18 * SR)
        clap = bandpass(rng.standard_normal(n2), 900, 3000) * np.exp(-np.arange(n2) / SR * 22)
        add(clap, st, 0.22, pan=-0.2)

# ---- arpegio pluck (desde Grass Bio)
for k in range(int(DUR / (BEAT / 2))):
    st = k * BEAT / 2
    if st < 10.5 or st >= 47.5:
        continue
    ch = CHORDS[int(st // BAR) % 4]
    m = ch[k % len(ch)] + 12 + (12 if k % 8 >= 6 else 0)
    n = int(0.3 * SR)
    tt = np.arange(n) / SR
    f = hz(m)
    sig = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 3 * f * tt)) * np.exp(-tt * 12)
    pan = 0.5 if k % 2 else -0.5
    add(sig, st, 0.07, pan)
    add(sig, st + 0.375, 0.025, -pan)  # eco

# ---- "brillo" UV: campanitas en la escena Tracker
for k in range(18):
    st = 30.5 + k * 0.5 + rng.random() * 0.1
    n = int(0.9 * SR)
    tt = np.arange(n) / SR
    f = hz(CHORDS[int(st // BAR) % 4][k % 3] + 24)
    sig = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 4)
    add(sig, st, 0.05, pan=rng.uniform(-.7, .7))

# ---- whooshes en transiciones
for b in BOUNDS[1:-1]:
    n = int(1.0 * SR)
    noise = rng.standard_normal(n)
    sig = bandpass(noise, 400, 6000)
    tt = np.arange(n) / SR
    e = np.where(tt < 0.75, (tt / 0.75) ** 2, np.exp(-(tt - 0.75) * 14))
    add(sig * e, b - 0.75, 0.11, pan=0.0)

# ---- impactos
for b in (5.0, 10.5, 17.0, 47.5):
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(38 + 60 * np.exp(-tt * 12)) / SR
    boom = np.sin(ph) * np.exp(-tt * 2.5)
    crash = lowpass(rng.standard_normal(n), 7000) * np.exp(-tt * 3) * 0.25
    add(boom + crash, b, 0.5)

# ---- burbujas reventando (Cero): ráfaga de "pops"
for k in range(70):
    st = 24.95 + rng.random() * 2.2
    n = int(0.05 * SR)
    tt = np.arange(n) / SR
    f = rng.uniform(900, 2400)
    sig = np.sin(2 * np.pi * f * tt * (1 + tt * 8)) * np.exp(-tt * 90)
    add(sig, st, 0.05, pan=rng.uniform(-.6, .6))

# ---- zumbido de dron (Orbit)
st, en = 38.5, 47.5
i0, i1 = int(st * SR), int(en * SR)
tt = t[i0:i1] - st
f = 180 + 6 * np.sin(tt * 2.1)
ph = 2 * np.pi * np.cumsum(f) / SR
hum = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3.01 * ph)) * 0.6
hum = lowpass(hum, 1200)
fade = np.minimum(1, np.minimum(tt / 0.6, (en - st - tt) / 0.6))
L[i0:i1] += hum * fade * 0.05
R[i0:i1] += hum * fade * 0.05

# ---- master
fade_in = np.minimum(1, t / 1.0)
fade_out = np.clip((DUR - t) / 2.5, 0, 1)
mix = np.stack([L, R]) * fade_in * fade_out
mix = np.tanh(mix * 1.4)
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.89

os.makedirs(os.path.join(os.path.dirname(__file__), 'output'), exist_ok=True)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'soundtrack.wav')
pcm = (mix.T * 32767).astype(np.int16)
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('ok', out)
