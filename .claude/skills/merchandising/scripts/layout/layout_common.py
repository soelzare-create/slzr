"""Shared by the layout specs and the builders."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# family: (fa, en, light, dark): validated categorical slots (dataviz palette), fixed order, one family = one colour
FAM = {  # family: (fa, en, light, dark) — validated categorical slots, fixed order
    "cold":  ("یخچالی و لبنی", "Chilled & dairy", "#2a78d6", "#3987e5"),
    "snack": ("تنقلات و شیرینی", "Snacks & sweets", "#eb6834", "#d95926"),
    "stap":  ("پخت‌وپز", "Cooking staples", "#1baf7a", "#199e70"),
    "bfst":  ("صبحانه و نوشیدنی گرم", "Breakfast & hot drinks", "#eda100", "#c98500"),
    "drnk":  ("نوشیدنی", "Drinks", "#e87ba4", "#d55181"),
    "frsh":  ("تازه: میوه، سبزی، نان", "Fresh: produce & bread", "#008300", "#008300"),
    "nonf":  ("غیرغذایی", "Non-food", "#4a3aa7", "#9085e9"),
    "promo": ("پروموشن", "Promotion", "#8a8f98", "#9aa3ad"),
}


def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def label_fit(code, poly, short):
    """(text, font size in m, vertical?) for the on-map label «CODE - name»; falls back to the bare code if it does not fit."""
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    vert = h > 2.2 * w and w < 0.7
    L, T = (h, w) if vert else (w, h)
    diagonal = len(poly) == 4 and poly[0][0] != poly[1][0] and poly[0][1] != poly[1][1]   # rotated rectangles stay code-only
    sh = short.get(code)
    if sh and not diagonal:
        txt = f"{code} - {sh}"
        fs = min(0.30, L * 0.92 / (len(txt) * 0.52), T * 0.78)
        if fs >= 0.17:
            return txt, fs, vert
        fs = min(0.26, L * 0.92 / (max(len(code), len(sh)) * 0.52), T * 0.78 / 2.3)   # two lines: code / name
        if fs >= 0.13:
            return f"{code}\n{sh}", fs, vert
    fs = 0.26 if diagonal else (0.30 if (w > 0.9 or vert) else 0.24)
    return code, fs, vert
