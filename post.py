"""HUD overlay + sound for a rendered marble race, then encode the Short.

  python post.py                         overlay all frames -> race_<TAG>.mp4 (with audio)
  python post.py --range a b out.mp4     overlay + encode frames a..b-1 only (silent chunk, for parallel jobs)
  python post.py --audio out.wav         write the soundtrack only
  python post.py --thumb out.jpg         thumbnail from the rendered frames
Environment: RACE_CFG (same as race.py), FRAMES_DIR (default frames_<TAG>)."""
import os, sys, math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import theme as T  # noqa: E402
from race_logic import load, FPS, VIEW_H  # noqa: E402

FR = os.environ.get("FRAMES_DIR", os.path.join(HERE, "frames_" + T.TAG))
FONT = os.path.join(HERE, "fonts", "Anton-Regular.ttf")

S, INFO = load(os.path.join(HERE, f"sim_{T.TAG}.npz"))
POS = S["pos"]
GATE_T = float(S["gate_t"])
END = INFO["end_frame"]
WIN_F = INFO["winner_f"]
ORDER = INFO["order"]
FIN = INFO["finish"]
CAMZ = INFO["cam_z"]
N = POS.shape[1]
RGB = [tuple(c) for c in T.RGB]
LABELS = T.LABELS

_fonts = {}


def font(sz):
    if sz not in _fonts:
        _fonts[sz] = ImageFont.truetype(FONT, sz)
    return _fonts[sz]


def text(d, xy, s, sz, fill=(255, 255, 255), stroke=8, anchor="mm", sc=(10, 10, 30), maxw=None):
    if maxw:
        while sz > 20 and d.textlength(s, font=font(sz)) > maxw:
            sz -= 4
    d.text(xy, s, font=font(sz), fill=fill, stroke_width=stroke, stroke_fill=sc, anchor=anchor)


def pill(d, box, fill, outline=(255, 255, 255), w=5, r=40):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=w)


def ease(u):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def pop(u):
    """0 -> overshoot -> 1 scale for punchy text."""
    u = max(0.0, min(1.0, u))
    return 1 + 0.35 * math.sin(u * math.pi) * (1 - u) if u < 1 else 1.0


def scaled_text(img, center, s, sz, fill, k, maxw=980):
    if k <= 0.02:
        return
    d = ImageDraw.Draw(img)
    text(d, center, s, max(8, int(sz * k)), fill, stroke=max(2, int(10 * k)), maxw=maxw * k)


_icons = {}


def icon(j, size):
    """Round badge for entrant j: its flag (countries) or its colour."""
    key = (j, size)
    if key not in _icons:
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        if T.THEME == "countries":
            fl = Image.open(os.path.join(HERE, "flags", T.ENTRANTS[j] + ".png")).convert("RGB")
            fl = fl.resize((size * 2, size)).crop((size // 2, 0, size // 2 + size, size))
            im.paste(fl, (0, 0), mask)
        else:
            ImageDraw.Draw(im).ellipse((0, 0, size - 1, size - 1), fill=RGB[j])
        ImageDraw.Draw(im).ellipse((0, 0, size - 1, size - 1), outline=(255, 255, 255), width=max(2, size // 14))
        _icons[key] = im
    return _icons[key]


def to_screen(x, z, f, W=1080, H=1920):
    half_h = VIEW_H / 2
    half_w = half_h * W / H
    cz = CAMZ[max(0, min(len(CAMZ) - 1, f - 1))]
    return W / 2 + x / half_w * W / 2, H / 2 - (z - cz) / half_h * H / 2


# impacts: sudden velocity changes (drive the sparks and the click sounds)
VEL = np.diff(POS, axis=0) * FPS
ACC = np.linalg.norm(np.diff(VEL, axis=0), axis=-1)
HITS = []
for j in range(N):
    last = -99
    for f in np.nonzero(ACC[:, j] > 25)[0]:
        if f - last >= 3:
            HITS.append((int(f) + 2, j, float(ACC[f, j])))
            last = f
HITS.sort()

rng = random.Random(T.TAG)
CONF = [(rng.uniform(0, 1080), rng.uniform(-400, 0), rng.uniform(-80, 80), rng.uniform(250, 600),
         RGB[rng.randrange(N)], rng.uniform(0, 6.28), rng.uniform(10, 22)) for _ in range(140)]


def frame_hud(img, f):
    t = f / FPS
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size

    # impact sparks
    for (hf, j, a) in HITS:
        if hf > f:
            break
        age = f - hf
        if age > 6 or a < 45:
            continue
        sx, sy = to_screen(POS[hf - 1, j, 0], POS[hf - 1, j, 2], f, W, H)
        ln = (18 + min(a, 200) * 0.25) * (1 - age / 7)
        al = int(255 * (1 - age / 7))
        for k in range(8):
            ang = k * math.pi / 4 + hf
            r0 = 30 + age * 5
            d.line((sx + math.cos(ang) * r0, sy + math.sin(ang) * r0, sx + math.cos(ang) * (r0 + ln),
                    sy + math.sin(ang) * (r0 + ln)), fill=(255, 245, 190, al), width=5)

    # title strip (always)
    pill(d, (70, 70, W - 70, 200), (15, 10, 45, 215), (255, 255, 255, 230), 5, 50)
    text(d, (W // 2, 135), T.TITLE_HUD, 84, (255, 230, 60), 6, maxw=W - 200)

    # pick your entrant + countdown
    if t < GATE_T + 0.8:
        if t < GATE_T - 3.0:
            k = pop((t - 0.15) / 0.5)
            scaled_text(img, (W // 2, 1180), T.PICK_HUD, 104, (255, 255, 255), k * min(1, t / 0.3))
        else:
            n = GATE_T - t
            if n > 0:
                num = str(int(math.ceil(n)))
                u = 1 - (n - math.floor(n)) if n != math.floor(n) else 0
                scaled_text(img, (W // 2, 1180), num, 330, (255, 230, 60), pop(u / 0.35))
            else:
                scaled_text(img, (W // 2, 1180), "GO!", 300, (60, 255, 120), pop((-n) / 0.3))

    # live leader + standings
    if GATE_T < t < WIN_F / FPS:
        rk = INFO["rank"][f - 1]
        lead = rk[0]
        d = ImageDraw.Draw(img, "RGBA")
        pill(d, (190, 225, W - 190, 320), (*RGB[lead], 235), (255, 255, 255), 5, 46)
        ic = icon(lead, 76)
        img.paste(ic, (200, 235), ic)
        d = ImageDraw.Draw(img, "RGBA")
        text(d, (W // 2 + 40, 272), f"LEADER: {LABELS[lead]}", 60, (255, 255, 255), 5, maxw=W - 520)
        step = min(84, 860 // N)
        x0 = W // 2 - (N - 1) / 2 * step
        for p, j in enumerate(rk):
            cx = int(x0 + p * step)
            ic = icon(j, step - 14)
            img.paste(ic, (cx - ic.width // 2, 345), ic)
        d = ImageDraw.Draw(img, "RGBA")
        for p in range(N):
            text(d, (int(x0 + p * step), 345 + step - 6), str(p + 1), 26, (255, 255, 255), 3)

    # winner
    if f >= WIN_F:
        u = (f - WIN_F) / FPS
        w = ORDER[0]
        d = ImageDraw.Draw(img, "RGBA")
        for (x, y0, vx, vy, c, ph, sz) in CONF:
            y = y0 + vy * u + 60 * u * u
            xx = x + vx * u + 25 * math.sin(ph + u * 5)
            if 0 < y < H:
                a = sz * abs(math.cos(ph + u * 7))
                d.rectangle((xx - sz / 2, y - a / 2, xx + sz / 2, y + a / 2), fill=(*c, 255))
        k = pop(u / 0.45)
        bw = int(460 * k)
        if bw > 10:
            pill(d, (W // 2 - bw, 560 - int(120 * k), W // 2 + bw, 560 + int(120 * k)), (*RGB[w], 245),
                 (255, 255, 255), 8, 60)
            scaled_text(img, (W // 2, 560), f"{LABELS[w]} WINS!", 150, (255, 255, 255), k, maxw=860)
            d = ImageDraw.Draw(img, "RGBA")
        if u > 1.6:
            v = ease((u - 1.6) / 0.5)
            y0 = 770 + int(60 * (1 - v))
            pill(d, (200, y0, W - 200, y0 + 330), (15, 10, 45, int(225 * v)), (255, 255, 255, int(255 * v)), 5, 40)
            for p in range(3):
                j = ORDER[p]
                if FIN[j] > f:
                    continue
                yy = y0 + 70 + p * 95
                ic = icon(j, 70)
                img.paste(ic, (262, yy - 35), ic)
                d = ImageDraw.Draw(img, "RGBA")
                text(d, (360, yy), ["1ST", "2ND", "3RD"][p], 60, (255, 230, 60), 5, "lm")
                text(d, (480, yy), LABELS[j], 60, (255, 255, 255), 5, "lm", maxw=380)
        if u > 3.0:
            scaled_text(img, (W // 2, 1230), T.COMMENT_HUD, 84, (255, 255, 255), pop((u - 3.0) / 0.45))
    return img


# ---------------------------------------------------------------- audio
SR = 44100


def synth_audio(path):
    n = int(END / FPS * SR) + SR
    out = np.zeros(n)
    rs = np.random.RandomState(T.SEED % 2 ** 31)
    tick_len = int(0.05 * SR)
    tt = np.arange(tick_len) / SR
    for (f, j, a) in HITS:
        if f >= END:
            continue
        amp = min(1.0, a / 140) * 0.22
        p = (1300 + 120 * j) * rs.uniform(0.85, 1.2)
        tick = amp * np.sin(2 * np.pi * p * tt) * np.exp(-tt * 90) + amp * 0.4 * rs.randn(tick_len) * np.exp(-tt * 200)
        i0 = int(f / FPS * SR)
        out[i0:i0 + tick_len] += tick[:len(out) - i0]
    for (tb, fr, ln) in [(GATE_T - 3, 660, 0.15), (GATE_T - 2, 660, 0.15), (GATE_T - 1, 660, 0.15), (GATE_T, 1320, 0.4)]:
        tt2 = np.arange(int(ln * SR)) / SR
        b = 0.3 * np.sin(2 * np.pi * fr * tt2) * np.minimum(1, (ln - tt2) * 30)
        i0 = int(tb * SR)
        out[i0:i0 + len(b)] += b
    # music bed (tempo, key and progression vary per video)
    bpm = 116 + int(rs.randint(0, 18))
    key = int(rs.randint(-3, 4))
    progs = [[[60, 64, 67], [67, 71, 74], [69, 72, 76], [65, 69, 72]],
             [[57, 60, 64], [65, 69, 72], [60, 64, 67], [67, 71, 74]],
             [[60, 64, 67], [65, 69, 72], [67, 71, 74], [65, 69, 72]],
             [[62, 65, 69], [67, 71, 74], [60, 64, 67], [69, 72, 76]]]
    prog = progs[rs.randint(0, len(progs))]
    beat = 60 / bpm
    hz = lambda m: 440 * 2 ** ((m + key - 69) / 12)
    music = np.zeros(n)
    for b in range(int(n / SR / beat)):
        ch = prog[(b // 4) % 4]
        t0 = int(b * beat * SR)
        L = int(beat * SR)
        tt3 = np.arange(L) / SR
        seg = 0.16 * np.sin(2 * np.pi * hz(ch[0] - 24) * tt3) * np.exp(-tt3 * 3)
        seg += 0.07 * np.sign(np.sin(2 * np.pi * hz(ch[(b * 2) % 3] + 12) * tt3)) * np.exp(-tt3 * 9)
        h2 = L // 2
        tt5 = tt3[:L - h2]
        seg[h2:] += 0.05 * np.sign(np.sin(2 * np.pi * hz(ch[(b * 2 + 1) % 3] + 12) * tt5)) * np.exp(-tt5 * 12)
        hl = int(0.03 * SR)
        seg[h2:h2 + hl] += 0.03 * rs.randn(hl) * np.exp(-np.arange(hl) / SR * 150)
        if b % 2 == 0:  # kick
            kl = min(L, int(0.12 * SR))
            tk = np.arange(kl) / SR
            seg[:kl] += 0.25 * np.sin(2 * np.pi * (110 * np.exp(-tk * 25) + 45) * tk) * np.exp(-tk * 18)
        music[t0:t0 + L] += seg[:len(music) - t0]
    env = np.ones(n) * 0.55
    env[int(GATE_T * SR):] = 0.85
    out += music * env
    wt = WIN_F / FPS
    for k, m in enumerate([72, 76, 79, 84]):
        tt4 = np.arange(int(0.5 * SR)) / SR
        nb_ = 0.18 * np.sign(np.sin(2 * np.pi * hz(m) * tt4)) * np.exp(-tt4 * 4)
        i0 = int((wt + k * 0.12) * SR)
        out[i0:i0 + len(nb_)] += nb_[:len(out) - i0]
    out = out[:int(END / FPS * SR)]
    out = np.tanh(out * 1.1) * 0.9
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def encode_range(a, b, out, audio=None):
    """Overlay frames a..b-1 and pipe them straight into x264."""
    cmd = [ffmpeg(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS),
           "-i", "-"]
    if audio:
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(a, b):
        img = Image.open(os.path.join(FR, f"f{f:05d}.jpg")).convert("RGB")
        if img.size != (1080, 1920):
            img = img.resize((1080, 1920))
        p.stdin.write(frame_hud(img, f).tobytes())
    p.stdin.close()
    if p.wait():
        sys.exit("ffmpeg failed")


def thumbnail(out):
    """Mid-race moment with a big question title (no spoiler of the winner)."""
    f = max(1, int(GATE_T * FPS) + int(5 * FPS))
    img = Image.open(os.path.join(FR, f"f{f:05d}.jpg")).convert("RGB").resize((1080, 1920))
    d = ImageDraw.Draw(img, "RGBA")
    pill(d, (60, 700, 1020, 1100), (15, 10, 45, 220), (255, 255, 255), 8, 60)
    text(d, (540, 900), T.TITLE_HUD, 120, (255, 230, 60), 8, maxw=900)
    img.save(out, quality=92)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--range":
        encode_range(int(a[1]), min(int(a[2]), END + 1), a[3])
    elif a and a[0] == "--audio":
        synth_audio(a[1])
    elif a and a[0] == "--thumb":
        thumbnail(a[1])
    elif a and a[0] == "--end":
        print(END)
    else:
        wav = os.path.join(HERE, f"audio_{T.TAG}.wav")
        synth_audio(wav)
        out = os.path.join(HERE, f"race_{T.TAG}.mp4")
        encode_range(1, END + 1, out, wav)
        print("wrote", out)
