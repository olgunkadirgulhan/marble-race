"""Title / description / tags for a race (English, general audience). Never spoils the winner."""
import theme as T


def _pick(options, k=0):
    return options[(T.SEED + k) % len(options)]


def meta():
    n = T.N
    if T.THEME == "countries":
        star = next((l for c, l in zip(T.ENTRANTS, T.LABELS) if c in ("US", "GB", "CA", "BR", "MX", "IN", "TR")), T.LABELS[0])
        title = _pick([
            "Which Country Wins? 🏁 Marble Race #shorts",
            f"{n} Countries, Only 1 Winner! 🌍 Marble Race #shorts",
            f"Can {star.title()} Win This Marble Race? 🏁 #shorts",
            "Country Marble Race 🌍 Pick Your Flag! #shorts",
            "Marble Race of Nations 🏆 Who Wins? #shorts",
            "Country Marble Race: Bumpers, Spinners & Chaos! 🌍 #shorts",
        ])
        who = ", ".join(l.title() for l in T.LABELS)
        desc = (f"🌍 {n} countries race down a crazy marble tower: bumpers, spinners, pins and a tight funnel. "
                f"Pick your country before the gate opens and comment it below!\n\nIn this race: {who}.\n\n"
                "Every race is a real physics simulation — no race is ever the same.\n\n"
                "#marblerace #countryballs #shorts #satisfying #marblerun")
        tags = ["marble race", "country marble race", "countries race", "marble run", "which country wins",
                "flag race", "satisfying", "physics simulation", "shorts"] + [l.lower() for l in T.LABELS[:4]]
    else:
        title = _pick([
            "Which Color Wins? 🏁 Marble Race #shorts",
            "Pick Your Color! 🎨 Satisfying Marble Race #shorts",
            f"{n} Marbles, 1 Winner! Which Color? #shorts",
            "Color Marble Race 🏆 Bumpers & Spinners! #shorts",
            "Satisfying Marble Race 🌈 Who Wins? #shorts",
        ])
        desc = (f"🌈 {n} marbles race down a crazy tower full of bumpers, spinners and pins. Pick your color before "
                "the gate opens and comment it below!\n\nIn this race: " + ", ".join(l.title() for l in T.LABELS) +
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
