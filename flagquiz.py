"""Guess the Flag Shorts (2026-11-08; Marble Rush Arena kanalının yeni konsepti — kanal dağıtımı çöktü: medyan 57).
Trend taraması: "guess the flag" son 30 gün Shorts medyanı 577K, 33 kanal 100K+. İngilizce, ABD izleyicisi.
Her video 6 bayrak, seviye 1 (kolay) → 6 (zor); 3 şık, 3 sn düşün, cevap. Seri numarası #N.
Bayraklar: flagcdn.com (kamu malı ulusal bayraklar), fonts/flags/<kod>.png önbelleği. Tartışmalı/çatışma bölgeleri yok (yorum kavgası).
    python flagquiz.py --dry-run | --auto
"""
import os, random, sys, urllib.request
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw
import shortkit as K

HERE = Path(__file__).resolve().parent
FLAGS = HERE / 'fonts' / 'flags'
LOG = HERE / 'records' / 'flag_published.csv'
OUT = HERE / 'out' / 'flag'
DRY = '--dry-run' in sys.argv
N_Q, THINK, SHOW = 6, 3.0, 1.6
INTRO, OUTRO = 1.4, 3.0
GOLD = (255, 215, 60)

# zorluk kademeleri (1 kolay → 4 zor); İngilizce adlar
TIERS = {
    1: {'us': 'USA', 'ca': 'Canada', 'mx': 'Mexico', 'gb': 'United Kingdom', 'fr': 'France', 'de': 'Germany', 'it': 'Italy',
        'es': 'Spain', 'jp': 'Japan', 'br': 'Brazil', 'au': 'Australia', 'in': 'India', 'cn': 'China', 'kr': 'South Korea',
        'ar': 'Argentina', 'se': 'Sweden', 'ch': 'Switzerland', 'gr': 'Greece', 'ie': 'Ireland', 'nl': 'Netherlands'},
    2: {'pt': 'Portugal', 'be': 'Belgium', 'at': 'Austria', 'no': 'Norway', 'dk': 'Denmark', 'fi': 'Finland', 'pl': 'Poland',
        'tr': 'Turkey', 'eg': 'Egypt', 'za': 'South Africa', 'ng': 'Nigeria', 'ke': 'Kenya', 'co': 'Colombia', 'cl': 'Chile',
        'pe': 'Peru', 'nz': 'New Zealand', 'jm': 'Jamaica', 'th': 'Thailand', 'vn': 'Vietnam', 'ph': 'Philippines', 'id': 'Indonesia',
        'sa': 'Saudi Arabia', 'ma': 'Morocco', 'cu': 'Cuba', 'is': 'Iceland'},
    3: {'cz': 'Czechia', 'hu': 'Hungary', 'ro': 'Romania', 'bg': 'Bulgaria', 'hr': 'Croatia', 'rs': 'Serbia', 'sk': 'Slovakia',
        'si': 'Slovenia', 'ee': 'Estonia', 'lv': 'Latvia', 'lt': 'Lithuania', 'my': 'Malaysia', 'sg': 'Singapore', 'pk': 'Pakistan',
        'bd': 'Bangladesh', 'lk': 'Sri Lanka', 'np': 'Nepal', 'ae': 'United Arab Emirates', 'qa': 'Qatar', 'gh': 'Ghana',
        'et': 'Ethiopia', 'tz': 'Tanzania', 'uy': 'Uruguay', 've': 'Venezuela', 'ec': 'Ecuador', 'bo': 'Bolivia', 'pa': 'Panama',
        'cr': 'Costa Rica', 'do': 'Dominican Republic', 'mn': 'Mongolia', 'kz': 'Kazakhstan', 'lu': 'Luxembourg', 'mt': 'Malta'},
    4: {'bt': 'Bhutan', 'kh': 'Cambodia', 'la': 'Laos', 'mm': 'Myanmar', 'uz': 'Uzbekistan', 'kg': 'Kyrgyzstan', 'tj': 'Tajikistan',
        'tm': 'Turkmenistan', 'om': 'Oman', 'kw': 'Kuwait', 'bh': 'Bahrain', 'jo': 'Jordan', 'tn': 'Tunisia', 'dz': 'Algeria',
        'sn': 'Senegal', 'ci': "Ivory Coast", 'cm': 'Cameroon', 'ug': 'Uganda', 'rw': 'Rwanda', 'zm': 'Zambia', 'zw': 'Zimbabwe',
        'na': 'Namibia', 'bw': 'Botswana', 'mg': 'Madagascar', 'mz': 'Mozambique', 'py': 'Paraguay', 'gt': 'Guatemala',
        'hn': 'Honduras', 'sv': 'El Salvador', 'ni': 'Nicaragua', 'bs': 'Bahamas', 'tt': 'Trinidad and Tobago', 'bb': 'Barbados',
        'fj': 'Fiji', 'pg': 'Papua New Guinea', 'mv': 'Maldives', 'cy': 'Cyprus', 'ge': 'Georgia', 'am': 'Armenia', 'al': 'Albania',
        'mk': 'North Macedonia', 'me': 'Montenegro', 'ba': 'Bosnia and Herzegovina', 'md': 'Moldova', 'li': 'Liechtenstein',
        'ad': 'Andorra', 'mc': 'Monaco', 'sm': 'San Marino'},
}
LEVEL_TIER = [1, 1, 2, 2, 3, 4]
NAME = {c: n for t in TIERS.values() for c, n in t.items()}


@lru_cache(None)
def flag(code, w):
    p = FLAGS / f'{code}.png'
    if not p.exists():
        FLAGS.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(f'https://flagcdn.com/w640/{code}.png', headers={'User-Agent': 'flagquiz/1.0'})
        p.write_bytes(urllib.request.urlopen(req, timeout=30).read())
    im = Image.open(p).convert('RGBA'); s = w / im.width
    return im.resize((w, max(1, int(im.height * s))), Image.LANCZOS)


def make_plan(rnd, used_codes):
    qs = []
    for lv, t in enumerate(LEVEL_TIER, 1):
        pool = [c for c in TIERS[t] if c not in used_codes and c not in [q['c'] for q in qs]] or list(TIERS[t])
        c = rnd.choice(pool)
        decoys = rnd.sample([x for x in TIERS[t] if x != c], 2)
        opts = [c] + decoys; rnd.shuffle(opts)
        qs.append(dict(c=c, opts=opts, lv=lv))
    return qs


def frame_fn(p):
    qs = p['qs']; seg = THINK + SHOW; total = INTRO + N_Q * seg + OUTRO

    def f(T):
        img = K.gradient((30, 50, 110), (12, 20, 50), False).copy(); d = ImageDraw.Draw(img)
        if T < INTRO:
            u = K.ease(T / 0.5)
            K.text(d, (K.W / 2, 760), 'GUESS THE', int(130 * u) + 1)
            K.text(d, (K.W / 2, 900), 'FLAG!', int(180 * u) + 1, fill=GOLD)
            K.text(d, (K.W / 2, 1070), f"6 LEVELS · #{p['n']}", int(64 * u) + 1)
            return img
        if T >= INTRO + N_Q * seg:
            u = K.ease((T - INTRO - N_Q * seg) / 0.5)
            K.text(d, (K.W / 2, 720), 'WHAT LEVEL', int(110 * u) + 1)
            K.text(d, (K.W / 2, 850), 'DID YOU REACH?', int(100 * u) + 1, fill=GOLD)
            K.text(d, (K.W / 2, 1010), 'COMMENT 1-6', int(80 * u) + 1)
            K.text(d, (K.W / 2, 1160), f"NEXT: FLAG QUIZ #{p['n'] + 1}", int(60 * u) + 1)
            return img
        i = int((T - INTRO) // seg); lt = T - INTRO - i * seg; q = qs[i]; pop = K.ease(lt / 0.35); show = lt >= THINK
        K.text(d, (K.W / 2, 150), f"LEVEL {q['lv']}/6", 70, fill=GOLD)
        K.text(d, (K.W / 2, 240), ['EASY', 'EASY', 'MEDIUM', 'MEDIUM', 'HARD', 'EXPERT'][q['lv'] - 1], 56)
        fl = flag(q['c'], int(760 * pop) + 1)
        d.rounded_rectangle([K.W / 2 - fl.width / 2 - 18, 640 - fl.height / 2 - 18, K.W / 2 + fl.width / 2 + 18, 640 + fl.height / 2 + 18],
                            radius=20, fill=(255, 255, 255, 255))
        img.alpha_composite(fl, (int(K.W / 2 - fl.width / 2), int(640 - fl.height / 2)))
        for j, c in enumerate(q['opts']):
            y = 1080 + j * 190; ok = c == q['c']
            col = ((60, 180, 100) if ok else (90, 95, 110)) if show else (255, 255, 255)
            d.rounded_rectangle([110, y - 75, K.W - 110, y + 75], radius=40, fill=col + (255,))
            K.text(d, (K.W / 2, y), f"{'ABC'[j]}. {NAME[c].upper()}", 64, fill=(255, 255, 255) if show else (30, 40, 80),
                   stroke=(30, 40, 80) if show else (255, 255, 255), max_w=K.W - 300)
        if not show:
            frac = max(0.0, 1 - lt / THINK)
            d.rounded_rectangle([90, 1700, K.W - 90, 1746], radius=23, fill=(255, 255, 255, 120))
            d.rounded_rectangle([90, 1700, 90 + max(46, (K.W - 180) * frac), 1746], radius=23, fill=GOLD)
        return img
    events = [(INTRO + i * seg, 'new') for i in range(N_Q)] + [(INTRO + i * seg + s, 'tick') for i in range(N_Q) for s in (1, 2)]
    events += [(INTRO + i * seg + THINK, 'ding') for i in range(N_Q)] + [(INTRO + N_Q * seg, 'end')]
    return f, total, events


# 2026-11-09: 576 kombinasyon (3/gün ≈ 6 ay)
_HOOKS = ['Guess the Flag!', 'Flag Quiz: Can You Reach Level 6?', 'How Many Flags Do You Know?', 'Guess the Country by Its Flag!', 'Only Experts Pass Level 6!', 'Name This Flag!', 'World Flags Challenge!', 'Flag Detective Quiz!', 'Can You Beat the Flag Quiz?', 'Name That Country!', 'The Real Geography Test!', 'Which Country Is This?', 'Flags of the World Quiz!', 'Think You Know Flags?', 'Geography Nerds Only!', 'World Traveler Flag Test!', 'Spot the Country!', 'Test Your Flag Knowledge!', 'Whose Flag Is This?', 'Can You Name All 6 Flags?', 'Flag Guessing Game!', 'Country Flag Challenge!', 'Beat the Flag Levels!', 'Globe Trotter Quiz!']
_EM = ['🌍','🏳️','🌎','🗺️']
_TAILS = ['6 Levels {0}', 'Level 1-6 {1}', 'Easy to Hard {2}', '6 Rounds {3}', 'Can You Get 6/6? {0}', 'Hard Mode at the End {1}', 'Comment Your Score {2}', 'Beat Your Friends {3}', '3 Seconds Each {0}', 'No Cheating {1}', 'Level 6 Is Tough {2}', 'How Far Can You Go? {3}', 'Daily Quiz {0}', 'Quick Brain Test {1}', 'Try It With Family {2}', 'Keep Your Streak {3}', 'Six Chances {0}', 'Answer Before Time Ends {1}', 'Fast Round {2}', 'Play Along {3}', 'Score Yourself {0}', 'Test Yourself {1}', 'Challenge a Friend {2}', 'Beat the Timer {3}']
TITLES = [f'{h} {t.format(*_EM)} #{{n}}' for h in _HOOKS for t in _TAILS]


def main():
    a = sys.argv[1:]
    if '--auto' in a and K.today_count(LOG) >= int(os.environ.get('PER_DAY') or 3):
        print('bugünkü sayı doldu'); return
    rows = K.rows(LOG); used = {c for r in rows[-20:] for c in r['topic_id'].split(':', 1)[-1].split('|')}
    rnd = random.Random(); qs = make_plan(rnd, used)
    n = len(rows) + 1; p = dict(qs=qs, n=n, seed=rnd.randrange(10 ** 6))
    seen = {K.tkey(r['title']) for r in rows}
    opts = [t.format(n=n) for t in TITLES]; rnd.shuffle(opts)
    title = next((o for o in opts if K.tkey(o) not in seen), opts[0])
    desc = ('Guess the flag! 6 levels from easy to expert.\n\n' + '\n'.join(f"Level {q['lv']}: {NAME[q['c']]}" for q in qs)
            + '\n\nWhat level did you reach? Comment 1-6 👇 New flag quiz every day.\n\n'
            'Flag images: flagcdn.com (public domain national flags).\n\n#shorts #flags #flagquiz #geography #quiz')
    tags = ['guess the flag', 'flag quiz', 'flags of the world', 'geography quiz', 'countries', 'quiz', 'shorts']
    f, total, events = frame_fn(p)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    print(f'[flag] #{n} {title}', flush=True)
    mp4 = K.render(f, total, events, p['seed'], OUT / f'flag_{stamp}.mp4')
    if DRY: print('  [dry-run]', mp4); return
    pa = K.publish_at(['15:30', '18:30', '21:00'], K.today_count(LOG))
    vid = K.upload(mp4, title + ' #shorts', desc, tags, pa, category='27')
    K.record(LOG, 'flag:' + '|'.join(q['c'] for q in qs), vid, title, pa)
    print(f'  ✓ https://youtu.be/{vid} ({pa})')


if __name__ == '__main__':
    main()
