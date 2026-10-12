import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt
M = sys.argv[1]; SR = 48000; DUR = 42.95
def load(p):
    w = wave.open(p); n = w.getnframes(); ch = w.getnchannels(); sw = w.getsampwidth()
    a = np.frombuffer(w.readframes(n), dtype={2: np.int16, 4: np.int32}[sw]).astype(np.float32)
    a /= {2: 32768., 4: 2147483648.}[sw]
    return a.reshape(-1, ch)
dr, mu = load(f'{M}/drums.wav'), load(f'{M}/music.wav')
N = int(DUR * SR) + SR
def fit(a):
    o = np.zeros((N, 2), np.float32); k = min(len(a), N); o[:k] = a[:k]; return o
dr, mu = fit(dr), fit(mu)
t = np.arange(N) / SR

# sidechain pump on the music bus (on every beat) during groove/chorus sections
beat = 0.5
ph = (t % beat) / beat
env = 1 - 0.45 * np.exp(-ph * 9)
active = ((t >= 4) & (t < 28)) | ((t >= 36) & (t < 42))
mu *= np.where(active, env, 1.0)[:, None]

fx = np.zeros((N, 2), np.float32)
rng = np.random.default_rng(7)
def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); k = min(len(sig), N - i)
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    fx[i:i + k, 0] += sig[:k] * gain * l * 1.414; fx[i:i + k, 1] += sig[:k] * gain * r * 1.414
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'bandpass', fs=SR, output='sos'), x)

# riser into the drop (2.0 -> 4.0s) and before final chorus (34 -> 36s)
def riser(d):
    n = int(d * SR); x = rng.standard_normal(n)
    out = np.zeros(n); seg = n // 40
    for j in range(40):
        f = 400 * (12 ** (j / 39)); s = slice(j * seg, (j + 1) * seg if j < 39 else n)
        out[s] = bp(x[s], f, min(f * 1.8, 20000))
    return out * np.linspace(0, 1, n) ** 2 * 0.5
add(riser(2.0), 2.0, 0.55); add(riser(2.0), 34.0, 0.45)

# whoosh on each wipe transition
def whoosh(d=0.5):
    n = int(d * SR); x = bp(rng.standard_normal(n), 900, 6000)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return x * e * 0.6
for at, pan in [(4.2, -.3), (8.55, .3), (13.3, -.3), (24.0, .3), (28.85, -.3), (37.4, .3)]:
    add(whoosh(), at - 0.05, 0.5, pan)

# impact on the drop
n = int(1.2 * SR); tt = np.arange(n) / SR
boom = np.sin(2 * np.pi * (70 * tt - 25 * tt ** 2)) * np.exp(-tt * 4)
add(boom, 4.0, 0.7)

# coin "ding" when 총 1,000원 lands (~5.7s) and on the end CTA (~39.1s)
def ding():
    n = int(1.0 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1975 * tt) + .5 * np.sin(2 * np.pi * 2637 * tt) + .25 * np.sin(2 * np.pi * 3951 * tt)) * np.exp(-tt * 6) * .35
add(ding(), 5.70, 0.8, .2); add(ding(), 5.82, 0.6, -.2); add(ding(), 39.05, 0.6)

mix = dr * 1.0 + mu * 0.95 + fx
mix = mix[:int(DUR * SR)]
fade = int(1.0 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5
mix /= max(1e-6, np.abs(mix).max()) / 0.9
w = wave.open(f'{M}/mix.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print('ok', mix.shape[0] / SR)
