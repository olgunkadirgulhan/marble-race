"""What a race is about (pure python: imported by Blender and by the HUD pass).

RACE_CFG = short:YYYY-MM-DD:K  -> theme, entrants and course seed for that slot.
RACE_VARIANT = n               -> start order / spinner speed (several are simulated, the most exciting is kept)."""
import datetime, os, random

CFG = os.environ.get("RACE_CFG", "short:2026-10-07:1")
TAG = CFG.replace(":", "_")
_p = CFG.split(":")
KIND = _p[0]
DATE = datetime.date.fromisoformat(_p[1])
SLOT = int(_p[2]) if len(_p) > 2 else 0
SEED = DATE.toordinal() * 10 + SLOT

COLORS = {"RED": (235, 40, 40), "BLUE": (40, 110, 255), "GREEN": (40, 200, 70), "YELLOW": (255, 205, 20),
          "PURPLE": (150, 60, 235), "ORANGE": (255, 125, 20), "PINK": (255, 90, 160), "CYAN": (20, 210, 235),
          "WHITE": (235, 235, 245), "BLACK": (40, 40, 48), "LIME": (160, 240, 40), "BROWN": (140, 80, 40)}
FLAG_CODES = ["US", "GB", "TR", "JP", "BR", "CA", "IN", "KR", "CN", "GR", "AR", "MX", "CH", "FR", "IT", "DE", "NL", "IE",
              "BE", "PL", "UA", "ID", "AT", "CO", "NG", "PE", "SE", "NO", "DK", "FI", "ES", "EE", "BG", "HU", "RO"]
NAMES = {"US": "USA", "GB": "UK", "TR": "TURKEY", "JP": "JAPAN", "BR": "BRAZIL", "CA": "CANADA", "IN": "INDIA",
         "KR": "KOREA", "CN": "CHINA", "GR": "GREECE", "AR": "ARGENTINA", "MX": "MEXICO", "CH": "SWISS", "FR": "FRANCE",
         "IT": "ITALY", "DE": "GERMANY", "NL": "NETHERLANDS", "IE": "IRELAND", "BE": "BELGIUM", "PL": "POLAND",
         "UA": "UKRAINE", "ID": "INDONESIA", "AT": "AUSTRIA", "CO": "COLOMBIA", "NG": "NIGERIA", "PE": "PERU",
         "SE": "SWEDEN", "NO": "NORWAY", "DK": "DENMARK", "FI": "FINLAND", "ES": "SPAIN", "EE": "ESTONIA",
         "BG": "BULGARIA", "HU": "HUNGARY", "RO": "ROMANIA"}
# rough flag colours for HUD accents
FLAG_RGB = {"US": (60, 59, 110), "GB": (1, 33, 105), "TR": (227, 10, 23), "JP": (188, 0, 45), "BR": (0, 155, 58),
            "CA": (216, 6, 33), "IN": (255, 153, 51), "KR": (0, 71, 160), "CN": (238, 28, 37), "GR": (13, 94, 175),
            "AR": (116, 172, 223), "MX": (0, 104, 71), "CH": (255, 0, 0), "FR": (0, 35, 149), "IT": (0, 146, 70),
            "DE": (221, 0, 0), "NL": (174, 28, 40), "IE": (22, 155, 98), "BE": (253, 218, 36), "PL": (220, 20, 60),
            "UA": (0, 87, 183), "ID": (206, 17, 38), "AT": (237, 41, 57), "CO": (252, 209, 22), "NG": (0, 135, 81),
            "PE": (217, 16, 35), "SE": (0, 106, 167), "NO": (186, 12, 47), "DK": (198, 12, 48), "FI": (0, 47, 108),
            "ES": (170, 21, 27), "EE": (0, 114, 206), "BG": (0, 150, 110), "HU": (71, 112, 80), "RO": (0, 43, 127)}
POPULAR = ["US", "GB", "CA", "BR", "MX", "IN", "DE", "FR", "JP", "TR", "IT", "ES", "AR", "KR"]

_r = random.Random(SEED)
THEME = ["countries", "colors", "countries"][(DATE.toordinal() + SLOT) % 3]
N = 10 if THEME == "countries" else 8
if THEME == "countries":
    pop = _r.sample(POPULAR, 5)
    rest = _r.sample([c for c in FLAG_CODES if c not in pop], N - len(pop))
    if "US" not in pop and _r.random() < 0.6:
        pop[0] = "US"
    ENTRANTS = pop + rest
    LABELS = [NAMES[c] for c in ENTRANTS]
    RGB = [FLAG_RGB[c] for c in ENTRANTS]
else:
    ENTRANTS = _r.sample(list(COLORS), N)
    LABELS = ENTRANTS
    RGB = [COLORS[c] for c in ENTRANTS]

TITLE_HUD = "WHICH COUNTRY WINS?" if THEME == "countries" else "WHICH COLOR WINS?"
PICK_HUD = "PICK YOUR COUNTRY!" if THEME == "countries" else "PICK YOUR COLOR!"
COMMENT_HUD = "COMMENT YOUR COUNTRY!" if THEME == "countries" else "COMMENT YOUR COLOR!"
