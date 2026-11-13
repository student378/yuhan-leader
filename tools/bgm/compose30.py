# 30s original track for the short promo cut. 120 BPM, 4/4, C major, 15 bars.
import sys
import mido

OUT = sys.argv[1]
TPB = 480
BPM = 120
BAR = 4 * TPB

PROG = [(48, 'C'), (43, 'G'), (45, 'Am'), (41, 'F')]
TRIADS = {'C': [60, 64, 67], 'G': [59, 62, 67], 'Am': [60, 64, 69], 'F': [60, 65, 69]}
NBARS = 15

# 0-1 intro | 2-7 groove (drop at bar 2 = 4.0s) | 8-10 chorus (16s) | 11-12 light (22s) | 13-14 final chorus (26s)
def sec(b):
    if b < 2: return 'intro'
    if b < 8: return 'groove'
    if b < 11: return 'chorus'
    if b < 13: return 'light'
    return 'final'

events = {}
def note(trk, ch, start, dur, pitch, vel):
    events.setdefault(trk, []).append((start, 'on', ch, pitch, vel))
    events.setdefault(trk, []).append((start + dur, 'off', ch, pitch, 0))

E = TPB // 2
S = TPB // 4

for b in range(NBARS):
    s0 = b * BAR
    root, name = PROG[b % 4]
    tri = TRIADS[name]
    sc = sec(b)
    full = sc in ('groove', 'chorus', 'final')

    # drums
    if full:
        for beat in range(4):
            note('drums', 9, s0 + beat * TPB, E, 36, 118)
        for beat in (1, 3):
            note('drums', 9, s0 + beat * TPB, E, 39, 96)
            note('drums', 9, s0 + beat * TPB, E, 38, 58)
        for i in range(8):
            note('drums', 9, s0 + i * E, S, 42 if i % 2 == 0 else 46, 52 if i % 2 == 0 else 70)
        if sc in ('chorus', 'final'):
            for i in range(16):
                if i % 2: note('drums', 9, s0 + i * S, S, 42, 38)
    elif sc == 'light':
        note('drums', 9, s0, E, 36, 96); note('drums', 9, s0 + 2 * TPB + E, E, 36, 78)
        note('drums', 9, s0 + TPB, E, 39, 68); note('drums', 9, s0 + 3 * TPB, E, 39, 76)
        for i in range(8):
            note('drums', 9, s0 + i * E, S, 42, 40)
    else:  # intro
        for i in range(8):
            note('drums', 9, s0 + i * E, S, 42, 32 + i * 4 + b * 22)
        if b == 1:
            for i in range(8):
                note('drums', 9, s0 + 2 * TPB + i * S, S, 38, 52 + i * 8)
    if b in (2, 8, 11, 13):
        note('drums', 9, s0, TPB * 2, 49, 102)

    # bass
    if full:
        for i in range(8):
            p = root if i % 2 else root - 12
            note('bass', 1, s0 + i * E, E - 30, p, 100 if i % 2 else 84)
    elif sc == 'light':
        note('bass', 1, s0, TPB * 2 - 40, root, 78); note('bass', 1, s0 + 2 * TPB, TPB * 2 - 40, root, 70)

    # keys stabs + pad
    if full or sc == 'light':
        hits = [E, 3 * E, 5 * E, 7 * E] if full else [0, 3 * E, 6 * E]
        for h in hits:
            for p in tri:
                note('keys', 2, s0 + h, E - 40, p + 12, 78 if full else 68)
    if sc in ('intro', 'light', 'chorus', 'final'):
        for p in tri:
            note('pad', 3, s0, BAR - 20, p, 56)

    # marimba arp in intro/light
    if sc in ('intro', 'light'):
        arp = [tri[0], tri[1], tri[2], tri[1] + 12, tri[2] + 12, tri[1] + 12, tri[2], tri[1]]
        for i in range(16):
            note('arp', 4, s0 + i * S, S, arp[i % 8] + 12, 68 if i % 4 == 0 else 52)

# lead motif (original) for chorus bars
MOTIF = [
    (0, .5, 76), (.5, .5, 79), (1, 1, 81), (2.5, .5, 79), (3, 1, 76),
    (4, .5, 74), (4.5, .5, 76), (5, 1, 79), (6.5, 1.5, 74),
    (8, .5, 72), (8.5, .5, 76), (9, 1, 81), (10.5, .5, 79), (11, 1.5, 76),
]
def lead(bar0, motif, vel=86):
    for st, ln, p in motif:
        t0 = bar0 * BAR + int(st * TPB)
        note('lead', 5, t0, int(ln * TPB) - 30, p, vel)
        note('glock', 6, t0, int(ln * TPB) - 30, p + 12, int(vel * .6))
lead(8, MOTIF, 86)
lead(13, MOTIF[:9], 88)
note('lead', 5, 14 * BAR + 2 * TPB, TPB * 2, 72, 92)
note('glock', 6, 14 * BAR + 2 * TPB, TPB * 2, 84, 60)

mid = mido.MidiFile(ticks_per_beat=TPB)
meta = mido.MidiTrack()
meta.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM), time=0))
mid.tracks.append(meta)
PROGS = {'drums': (9, None), 'bass': (1, 38), 'keys': (2, 4), 'pad': (3, 89), 'arp': (4, 12), 'lead': (5, 80), 'glock': (6, 9)}
VOL = {'drums': 110, 'bass': 100, 'keys': 78, 'pad': 70, 'arp': 76, 'lead': 70, 'glock': 64}
REV = {'drums': 20, 'bass': 0, 'keys': 50, 'pad': 80, 'arp': 60, 'lead': 50, 'glock': 70}
GROUPS = {'drums': {'drums'}, 'music': {'bass', 'keys', 'pad', 'arp', 'lead', 'glock'}}
for name, (ch, prog) in PROGS.items():
    t = mido.MidiTrack(); t.name = name
    if prog is not None:
        t.append(mido.Message('program_change', channel=ch, program=prog, time=0))
    t.append(mido.Message('control_change', channel=ch, control=7, value=VOL[name], time=0))
    t.append(mido.Message('control_change', channel=ch, control=91, value=REV[name], time=0))
    t.append(mido.Message('control_change', channel=ch, control=10, value={'keys': 54, 'arp': 76, 'glock': 46}.get(name, 64), time=0))
    evs = sorted(events.get(name, []), key=lambda e: (e[0], 0 if e[1] == 'off' else 1))
    last = 0
    for st, kind, c, a, v in evs:
        dt = st - last; last = st
        t.append(mido.Message('note_on' if kind == 'on' else 'note_off', channel=c, note=a, velocity=v, time=dt))
    mid.tracks.append(t)
mid.save(OUT)

# stems
base = OUT.rsplit('/', 1)[0]
for stem, keep in GROUPS.items():
    o = mido.MidiFile(ticks_per_beat=TPB); o.tracks.append(mid.tracks[0])
    for t in mid.tracks[1:]:
        if t.name in keep: o.tracks.append(t)
    o.save(f'{base}/{stem}30.mid')
print('saved', OUT, round(mid.length, 2), 's')
