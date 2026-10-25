"""Title / description / tags for a race (English, general audience). Never spoils the winner."""
import csv, glob, os, re
import theme as T

HERE = os.path.dirname(os.path.abspath(__file__))


def _key(t):
    """Başlık karşılaştırma anahtarı (emoji/etiket/noktalama yok)."""
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", re.sub(r"#\w+", " ", t.lower())).split())


def _used():
    keys = set()
    for f in glob.glob(os.path.join(HERE, "records", "published", "*.csv")):
        for row in csv.reader(open(f, encoding="utf-8")):
            if len(row) >= 4: keys.add(_key(row[3]))
    return keys


def _pick(options, k=0):
    """2026-10-25: aynı başlık tekrar edince YouTube dağıtmıyor → daha önce kullanılmamış ilk seçenek (tohuma göre sıralı)."""
    used = _used()
    order = options[(T.SEED + k) % len(options):] + options[:(T.SEED + k) % len(options)]
    return next((o for o in order if _key(o) not in used), order[0])


def _nm(l):
    return l if l.upper() in ("USA", "UK", "UAE") else l.title()


def meta():
    n = T.N
    if T.THEME == "countries":
        star = next((l for c, l in zip(T.ENTRANTS, T.LABELS) if c in ("US", "GB", "CA", "BR", "MX", "IN", "TR")), T.LABELS[0])
        trio = " vs ".join(_nm(l) for l in T.LABELS[:3])   # 2026-10-13: sabit 6 başlık tekrar ediyordu → yarıştaki ülkeler başlıkta
        title = _pick([
            f"{trio}... Which Country Wins? 🏁 #shorts",
            f"{trio} + {n - 3} More: Country Marble Race 🌍 #shorts",
            f"Can {_nm(star)} Beat {_nm(T.LABELS[-1])}? 🏁 Marble Race #shorts",
            f"{_nm(T.LABELS[0])}, {_nm(T.LABELS[1])} or {_nm(T.LABELS[2])}? Country Marble Race 🌍 #shorts",
            f"{n} Countries, Only 1 Winner: {trio} 🌍 #shorts",
            f"{_nm(star)} vs {n - 1} Countries in a Marble Race 🏁 #shorts",
            f"Can {_nm(star)} Win This Marble Race? 🏁 #shorts",
            f"Pick Your Flag: {trio} 🌍 Marble Race #shorts",
            f"Marble Race of Nations: {trio} 🏆 #shorts",
            f"{trio}: Bumpers, Spinners & Chaos! 🌍 #shorts",
        ])
        who = ", ".join(_nm(l) for l in T.LABELS)
        desc = (f"🌍 {n} countries race down a crazy marble tower: bumpers, spinners, pins and a tight funnel. "
                f"Pick your country before the gate opens and comment it below!\n\nIn this race: {who}.\n\n"
                "Every race is a real physics simulation — no race is ever the same.\n\n"
                "#marblerace #countryballs #shorts #satisfying #marblerun")
        tags = ["marble race", "country marble race", "countries race", "marble run", "which country wins",
                "flag race", "satisfying", "physics simulation", "shorts"] + [l.lower() for l in T.LABELS[:4]]
    else:
        trio = " vs ".join(_nm(l) for l in T.LABELS[:3])
        title = _pick([
            f"{trio}... Which Color Wins? 🎨 #shorts",
            f"{trio} + {n - 3} More: Color Marble Race 🌈 #shorts",
            f"{_nm(T.LABELS[0])}, {_nm(T.LABELS[1])} or {_nm(T.LABELS[2])}? Color Marble Race 🏁 #shorts",
            f"Pick Your Color: {trio} 🎨 #shorts",
            f"{n} Marbles, 1 Winner: {trio} #shorts",
            f"{trio}: Bumpers & Spinners! 🏆 #shorts",
            f"Satisfying Marble Race: {trio} 🌈 #shorts",
        ])
        desc = (f"🌈 {n} marbles race down a crazy tower full of bumpers, spinners and pins. Pick your color before "
                "the gate opens and comment it below!\n\nIn this race: " + ", ".join(_nm(l) for l in T.LABELS) +
                ".\n\nEvery race is a real physics simulation — no race is ever the same.\n\n"
                "#marblerace #satisfying #shorts #marblerun #colors")
        tags = ["marble race", "color marble race", "marble run", "which color wins", "satisfying", "asmr marbles",
                "physics simulation", "shorts"]
    return title[:100], desc[:4900], tags


if __name__ == "__main__":
    t, d, g = meta()
    print(t)
    print(d)
    print(g)
