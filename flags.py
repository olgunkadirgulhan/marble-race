"""Simple national flags drawn with PIL (no external assets).
draw(code) -> 512x256 RGB image; NAMES[code] = display name; HUD_RGB[code] = a representative colour."""
import math
from PIL import Image, ImageDraw

W, H = 512, 256
RED, WHITE, BLUE, GREEN, YELLOW, BLACK = (206, 17, 38), (255, 255, 255), (0, 56, 168), (0, 140, 69), (255, 206, 0), (20, 20, 20)
NAVY = (0, 40, 104)


def _hstripes(d, cols):
    h = H / len(cols)
    for i, c in enumerate(cols):
        d.rectangle((0, i * h, W, (i + 1) * h), fill=c)


def _vstripes(d, cols):
    w = W / len(cols)
    for i, c in enumerate(cols):
        d.rectangle((i * w, 0, (i + 1) * w, H), fill=c)


def _cross(d, bg, fg, inner=None):
    d.rectangle((0, 0, W, H), fill=bg)
    t = H * 0.2
    cx = W * 0.36
    d.rectangle((cx - t / 2, 0, cx + t / 2, H), fill=fg)
    d.rectangle((0, H / 2 - t / 2, W, H / 2 + t / 2), fill=fg)
    if inner:
        t2 = t * 0.5
        d.rectangle((cx - t2 / 2, 0, cx + t2 / 2, H), fill=inner)
        d.rectangle((0, H / 2 - t2 / 2, W, H / 2 + t2 / 2), fill=inner)


def _star(d, cx, cy, r, fill, rot=-90):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.4
        a = math.radians(rot + k * 36)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def _usa(d):
    for i in range(13):
        d.rectangle((0, i * H / 13, W, (i + 1) * H / 13), fill=(178, 34, 52) if i % 2 == 0 else WHITE)
    d.rectangle((0, 0, W * 0.4, H * 7 / 13), fill=(60, 59, 110))
    for r in range(5):
        for c in range(6):
            _star(d, 14 + c * 33 + (r % 2) * 8, 14 + r * 26, 8, WHITE)


def _uk(d):
    d.rectangle((0, 0, W, H), fill=(1, 33, 105))
    d.line((0, 0, W, H), fill=WHITE, width=48)
    d.line((0, H, W, 0), fill=WHITE, width=48)
    d.line((0, 0, W, H), fill=(200, 16, 46), width=16)
    d.line((0, H, W, 0), fill=(200, 16, 46), width=16)
    d.rectangle((W / 2 - 40, 0, W / 2 + 40, H), fill=WHITE)
    d.rectangle((0, H / 2 - 40, W, H / 2 + 40), fill=WHITE)
    d.rectangle((W / 2 - 24, 0, W / 2 + 24, H), fill=(200, 16, 46))
    d.rectangle((0, H / 2 - 24, W, H / 2 + 24), fill=(200, 16, 46))


def _turkey(d):
    d.rectangle((0, 0, W, H), fill=(227, 10, 23))
    d.ellipse((120, 64, 248, 192), fill=WHITE)
    d.ellipse((150, 77, 252, 179), fill=(227, 10, 23))
    _star(d, 285, 128, 34, WHITE, rot=180)


def _japan(d):
    d.rectangle((0, 0, W, H), fill=WHITE)
    d.ellipse((W / 2 - 77, H / 2 - 77, W / 2 + 77, H / 2 + 77), fill=(188, 0, 45))


def _brazil(d):
    d.rectangle((0, 0, W, H), fill=(0, 155, 58))
    d.polygon([(W / 2, 20), (W - 40, H / 2), (W / 2, H - 20), (40, H / 2)], fill=(254, 223, 0))
    d.ellipse((W / 2 - 66, H / 2 - 66, W / 2 + 66, H / 2 + 66), fill=(0, 39, 118))
    d.arc((W / 2 - 90, H / 2 - 40, W / 2 + 90, H / 2 + 120), 215, 325, fill=WHITE, width=10)


def _canada(d):
    _vstripes(d, [(216, 6, 33), WHITE, WHITE, (216, 6, 33)])
    cx, cy, s = W / 2, H / 2 + 6, 1.0
    leaf = [(0, -95), (14, -65), (30, -72), (24, -30), (52, -50), (58, -36), (86, -44), (76, -16), (90, -8), (44, 30),
            (52, 50), (8, 44), (8, 80), (-8, 80), (-8, 44), (-52, 50), (-44, 30), (-90, -8), (-76, -16), (-86, -44),
            (-58, -36), (-52, -50), (-24, -30), (-30, -72), (-14, -65)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in leaf], fill=(216, 6, 33))


def _india(d):
    _hstripes(d, [(255, 153, 51), WHITE, (19, 136, 8)])
    d.ellipse((W / 2 - 34, H / 2 - 34, W / 2 + 34, H / 2 + 34), outline=(0, 0, 128), width=6)
    for k in range(12):
        a = k * math.pi / 12
        d.line((W / 2 - 34 * math.cos(a), H / 2 - 34 * math.sin(a), W / 2 + 34 * math.cos(a), H / 2 + 34 * math.sin(a)),
               fill=(0, 0, 128), width=2)


def _korea(d):
    d.rectangle((0, 0, W, H), fill=WHITE)
    d.pieslice((W / 2 - 64, H / 2 - 64, W / 2 + 64, H / 2 + 64), 180, 360, fill=(205, 46, 58))
    d.pieslice((W / 2 - 64, H / 2 - 64, W / 2 + 64, H / 2 + 64), 0, 180, fill=(0, 71, 160))
    d.ellipse((W / 2 - 64, H / 2 - 32, W / 2, H / 2 + 32), fill=(205, 46, 58))
    d.ellipse((W / 2, H / 2 - 32, W / 2 + 64, H / 2 + 32), fill=(0, 71, 160))
    for (x, y) in ((110, 60), (400, 60), (110, 196), (400, 196)):
        for k in range(3):
            d.rectangle((x - 30, y - 22 + k * 16, x + 30, y - 14 + k * 16), fill=BLACK)


def _china(d):
    d.rectangle((0, 0, W, H), fill=(238, 28, 37))
    _star(d, 85, 70, 44, (255, 255, 0))
    for (x, y) in ((165, 28), (190, 58), (190, 98), (165, 126)):
        _star(d, x, y, 14, (255, 255, 0))


def _greece(d):
    for i in range(9):
        d.rectangle((0, i * H / 9, W, (i + 1) * H / 9), fill=(13, 94, 175) if i % 2 == 0 else WHITE)
    d.rectangle((0, 0, H * 5 / 9, H * 5 / 9), fill=(13, 94, 175))
    t = H / 9
    d.rectangle((H * 2 / 9, 0, H * 3 / 9, H * 5 / 9), fill=WHITE)
    d.rectangle((0, H * 2 / 9, H * 5 / 9, H * 3 / 9), fill=WHITE)


def _argentina(d):
    _hstripes(d, [(116, 172, 223), WHITE, (116, 172, 223)])
    d.ellipse((W / 2 - 26, H / 2 - 26, W / 2 + 26, H / 2 + 26), fill=(246, 180, 14))


def _mexico(d):
    _vstripes(d, [(0, 104, 71), WHITE, (206, 17, 38)])
    d.ellipse((W / 2 - 30, H / 2 - 30, W / 2 + 30, H / 2 + 30), fill=(140, 90, 40))


def _switz(d):
    d.rectangle((0, 0, W, H), fill=(255, 0, 0))
    d.rectangle((W / 2 - 20, H / 2 - 70, W / 2 + 20, H / 2 + 70), fill=WHITE)
    d.rectangle((W / 2 - 70, H / 2 - 20, W / 2 + 70, H / 2 + 20), fill=WHITE)


def _australia(d):
    d.rectangle((0, 0, W, H), fill=(0, 0, 139))
    sub = Image.new("RGB", (W, H))
    _uk(ImageDraw.Draw(sub))
    return sub.resize((W // 2, H // 2)), [(380, 60, 16), (330, 120, 14), (430, 115, 14), (380, 200, 18), (120, 200, 24)]


FLAGS = {
    "US": ("USA", _usa), "GB": ("UK", _uk), "TR": ("TURKEY", _turkey), "JP": ("JAPAN", _japan),
    "BR": ("BRAZIL", _brazil), "CA": ("CANADA", _canada), "IN": ("INDIA", _india), "KR": ("KOREA", _korea),
    "CN": ("CHINA", _china), "GR": ("GREECE", _greece), "AR": ("ARGENTINA", _argentina), "MX": ("MEXICO", _mexico),
    "CH": ("SWITZERLAND", _switz),
    "FR": ("FRANCE", lambda d: _vstripes(d, [(0, 35, 149), WHITE, (237, 41, 57)])),
    "IT": ("ITALY", lambda d: _vstripes(d, [(0, 146, 70), WHITE, (206, 43, 55)])),
    "DE": ("GERMANY", lambda d: _hstripes(d, [BLACK, (221, 0, 0), (255, 206, 0)])),
    "NL": ("NETHERLANDS", lambda d: _hstripes(d, [(174, 28, 40), WHITE, (33, 70, 139)])),
    "IE": ("IRELAND", lambda d: _vstripes(d, [(22, 155, 98), WHITE, (255, 136, 62)])),
    "BE": ("BELGIUM", lambda d: _vstripes(d, [BLACK, (253, 218, 36), (239, 51, 64)])),
    "PL": ("POLAND", lambda d: _hstripes(d, [WHITE, (220, 20, 60)])),
    "UA": ("UKRAINE", lambda d: _hstripes(d, [(0, 87, 183), (255, 215, 0)])),
    "ID": ("INDONESIA", lambda d: _hstripes(d, [(206, 17, 38), WHITE])),
    "AT": ("AUSTRIA", lambda d: _hstripes(d, [(237, 41, 57), WHITE, (237, 41, 57)])),
    "CO": ("COLOMBIA", lambda d: _hstripes(d, [(252, 209, 22), (252, 209, 22), (0, 56, 147), (206, 17, 38)])),
    "NG": ("NIGERIA", lambda d: _vstripes(d, [(0, 135, 81), WHITE, (0, 135, 81)])),
    "PE": ("PERU", lambda d: _vstripes(d, [(217, 16, 35), WHITE, (217, 16, 35)])),
    "SE": ("SWEDEN", lambda d: _cross(d, (0, 106, 167), (254, 204, 0))),
    "NO": ("NORWAY", lambda d: _cross(d, (186, 12, 47), WHITE, (0, 32, 91))),
    "DK": ("DENMARK", lambda d: _cross(d, (198, 12, 48), WHITE)),
    "FI": ("FINLAND", lambda d: _cross(d, WHITE, (0, 47, 108))),
    "ES": ("SPAIN", lambda d: _hstripes(d, [(170, 21, 27), (241, 191, 0), (241, 191, 0), (170, 21, 27)])),
    "EE": ("ESTONIA", lambda d: _hstripes(d, [(0, 114, 206), BLACK, WHITE])),
    "BG": ("BULGARIA", lambda d: _hstripes(d, [WHITE, (0, 150, 110), (214, 38, 18)])),
    "HU": ("HUNGARY", lambda d: _hstripes(d, [(206, 41, 57), WHITE, (71, 112, 80)])),
    "RO": ("ROMANIA", lambda d: _vstripes(d, [(0, 43, 127), (252, 209, 22), (206, 17, 38)])),
}
NAMES = {k: v[0] for k, v in FLAGS.items()}
POPULAR = ["US", "GB", "CA", "BR", "MX", "IN", "DE", "FR", "JP", "TR", "IT", "ES", "AR", "KR"]


def draw(code):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    fn = FLAGS[code][1]
    r = fn(d)
    if isinstance(r, tuple):  # australia-style canton + stars
        sub, stars = r
        img.paste(sub, (0, 0))
        for x, y, s in stars:
            _star(d, x, y, s, WHITE)
    return img


def main_rgb(code):
    """Average colour of the flag, saturated a bit, for HUD dots and glows."""
    img = draw(code).resize((16, 8))
    px = list(img.getdata())
    r = sum(p[0] for p in px) / len(px)
    g = sum(p[1] for p in px) / len(px)
    b = sum(p[2] for p in px) / len(px)
    return int(r), int(g), int(b)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "flags_sheet.png"
    codes = list(FLAGS)
    sheet = Image.new("RGB", (6 * 260, ((len(codes) + 5) // 6) * 140), (40, 40, 40))
    for i, c in enumerate(codes):
        sheet.paste(draw(c).resize((240, 120)), ((i % 6) * 260 + 10, (i // 6) * 140 + 10))
    sheet.save(out)
