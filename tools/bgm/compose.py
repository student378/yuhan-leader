# Original background track for the 천원매점 promo (composed here, no samples).
# 120 BPM, 4/4, C major, I–V–vi–IV. One bar = 2.0 s. Video length 42.95 s.
import sys
import mido

OUT = sys.argv[1]
TPB = 480
BPM = 120
BAR = 4 * TPB

# chord roots per bar (C, G, Am, F)
PROG = [(48, 'C'), (43, 'G'), (45, 'Am'), (41, 'F')]
TRIADS = {'C': [60, 64, 67], 'G': [59, 62, 67], 'Am': [60, 64, 69], 'F': [60, 65, 69]}
NBARS = 22

# section map (bar index -> energy)
#  0-1 intro | 2-9 groove | 10-11 lift | 12-13 chorus | 14-17 guide (light) | 18-20 final chorus | 21 tail
def sec(b):
    if b < 2: return 'intro'
    if b < 10: return 'groove'
    if b < 12: return 'lift'
    if b < 14: return 'chorus'
    if b < 18: return 'light'
    if b < 21: return 'chorus'
    return 'tail'

def track(name, ch, program=None):
    t = mido.MidiTrack(); t.name = name
    if program is not None:
        t.append(mido.Message('program_change', channel=ch, program=program, time=0))
    return t

events = {}
def note(trk, ch, start, dur, pitch, vel):
    events.setdefault(trk, []).append((start, 'on', ch, pitch, vel))
    events.setdefault(trk, []).append((start + dur, 'off', ch, pitch, 0))

def cc(trk, ch, start, ctl, val):
    events.setdefault(trk, []).append((start, 'cc', ch, ctl, val))

E = TPB // 2   # eighth
S = TPB // 4   # sixteenth

for b in range(NBARS):
    s0 = b * BAR
    root, name = PROG[b % 4]
    tri = TRIADS[name]
    sc = sec(b)

    # ── drums (ch 9) ──
    if sc in ('groove', 'lift', 'chorus'):
        for beat in range(4):
            note('drums', 9, s0 + beat * TPB, E, 36, 118)                      # four-on-the-floor kick
        for beat in (1, 3):
            note('drums', 9, s0 + beat * TPB, E, 39, 96)                       # clap
            note('drums', 9, s0 + beat * TPB, E, 38, 60)                       # snare layer
        for i in range(8):
            note('drums', 9, s0 + i * E + E // 1 * 0, S, 42 if i % 2 == 0 else 46, 52 if i % 2 == 0 else 70)
        if sc == 'chorus':
            for i in range(16):
                if i % 2: note('drums', 9, s0 + i * S, S, 42, 38)                 # 16th shaker feel
    elif sc == 'light':
        note('drums', 9, s0, E, 36, 100); note('drums', 9, s0 + 2 * TPB + E, E, 36, 80)
        note('drums', 9, s0 + TPB, E, 39, 70); note('drums', 9, s0 + 3 * TPB, E, 39, 80)
        for i in range(8):
            note('drums', 9, s0 + i * E, S, 42, 42)
    elif sc == 'intro':
        for i in range(8):
            note('drums', 9, s0 + i * E, S, 42, 30 + i * 4 + b * 20)
        if b == 1:   # snare build into the drop
            for i in range(8):
                note('drums', 9, s0 + 2 * TPB + i * S, S, 38, 50 + i * 8)
    # crash on section starts
    if b in (2, 10, 12, 14, 18) or (b == 21):
        note('drums', 9, s0, TPB * 2, 49, 100)

    # ── bass (ch 1, synth bass) — pumping eighths on the off-beat ──
    if sc in ('groove', 'lift', 'chorus'):
        for i in range(8):
            p = root if i % 2 else root - 12
            v = 100 if i % 2 else 84
            note('bass', 1, s0 + i * E, E - 30, p, v)
    elif sc == 'light':
        note('bass', 1, s0, TPB * 2 - 40, root, 80); note('bass', 1, s0 + 2 * TPB, TPB * 2 - 40, root, 72)
    elif sc == 'tail':
        note('bass', 1, s0, TPB * 4, root - 12, 100)

    # ── chords (ch 2 electric piano stabs, ch 3 warm pad) ──
    if sc in ('groove', 'lift', 'chorus', 'light'):
        hits = [E, 3 * E, 5 * E, 7 * E] if sc != 'light' else [0, 3 * E, 6 * E]
        for h in hits:
            for p in tri:
                note('keys', 2, s0 + h, E - 40, p + 12, 78 if sc != 'light' else 70)
    if sc in ('intro', 'light', 'chorus', 'lift', 'tail'):
        for p in tri:
            note('pad', 3, s0, BAR - 20 if sc != 'tail' else BAR * 1, p, 58 if sc != 'chorus' else 52)

    # ── pluck arpeggio (ch 4 marimba) ──
    if sc in ('intro', 'light', 'lift'):
        arp = [tri[0], tri[1], tri[2], tri[1] + 12, tri[2] + 12, tri[1] + 12, tri[2], tri[1]]
        for i in range(16):
            note('arp', 4, s0 + i * S, S, arp[i % 8] + 12, 70 if i % 4 == 0 else 54)

# ── lead melody (ch 5 square lead + ch 6 glockenspiel double) — original motif ──
# phrase per 4 bars, in beats (start, length, pitch)
MOTIF_A = [  # over C G Am F
    (0, .5, 76), (.5, .5, 79), (1, 1, 81), (2.5, .5, 79), (3, 1, 76),
    (4, .5, 74), (4.5, .5, 76), (5, 1, 79), (6.5, 1.5, 74),
    (8, .5, 72), (8.5, .5, 76), (9, 1, 81), (10.5, .5, 79), (11, 1, 76),
    (12, .5, 77), (12.5, .5, 76), (13, .5, 74), (13.5, .5, 72), (14, 2, 74),
]
MOTIF_B = MOTIF_A[:-1] + [(14, .5, 74), (14.5, .5, 76), (15, 1, 72)]
def lead(bar0, motif, vel=82):
    for st, ln, p in motif:
        t0 = bar0 * BAR + int(st * TPB)
        note('lead', 5, t0, int(ln * TPB) - 30, p, vel)
        note('glock', 6, t0, int(ln * TPB) - 30, p + 12, int(vel * .6))
lead(10, MOTIF_A[:9] + [(4 + 3.5, .5, 79)], 76)   # lift teaser (bars 10–11)
lead(12, MOTIF_A[:9], 86)                          # chorus (bars 12–13)
lead(18, MOTIF_A, 88)                              # final chorus (18–21)
# final hit
note('lead', 5, 21 * BAR, TPB * 3, 72, 92); note('glock', 6, 21 * BAR, TPB * 3, 84, 60)

# ── assemble ──
mid = mido.MidiFile(ticks_per_beat=TPB)
meta = mido.MidiTrack()
meta.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM), time=0))
mid.tracks.append(meta)
PROGS = {'drums': (9, None), 'bass': (1, 38), 'keys': (2, 4), 'pad': (3, 89), 'arp': (4, 12), 'lead': (5, 80), 'glock': (6, 9)}
VOL = {'drums': 110, 'bass': 100, 'keys': 78, 'pad': 70, 'arp': 76, 'lead': 70, 'glock': 64}
REV = {'drums': 20, 'bass': 0, 'keys': 50, 'pad': 80, 'arp': 60, 'lead': 50, 'glock': 70}
for name, (ch, prog) in PROGS.items():
    t = track(name, ch, prog)
    t.append(mido.Message('control_change', channel=ch, control=7, value=VOL[name], time=0))
    t.append(mido.Message('control_change', channel=ch, control=91, value=REV[name], time=0))
    t.append(mido.Message('control_change', channel=ch, control=10, value={'keys': 54, 'arp': 76, 'glock': 46}.get(name, 64), time=0))
    evs = sorted(events.get(name, []), key=lambda e: (e[0], 0 if e[1] == 'off' else 1))
    last = 0
    for st, kind, c, a, v in evs:
        dt = st - last; last = st
        if kind == 'on': t.append(mido.Message('note_on', channel=c, note=a, velocity=v, time=dt))
        elif kind == 'off': t.append(mido.Message('note_off', channel=c, note=a, velocity=0, time=dt))
        else: t.append(mido.Message('control_change', channel=c, control=a, value=v, time=dt))
    mid.tracks.append(t)
mid.save(OUT)
print('saved', OUT, round(mid.length, 2), 's')
