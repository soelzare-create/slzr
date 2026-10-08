"""Spec for «یاران سبز بوکان» — category layout (DXF metres). See references/layout-from-dxf.md for the spec format.
Fixture boxes come from the client DXF (dxf_tools.py inserts / grid); every shelf face and refrigerated unit gets one category.

NOTE ON END CAPS & PROMOTIONS (سرلاین‌ها و پیشنهادات):
All end caps and promotional items (A1N, A2N, A1S, A2S, F1, X1) must be assigned TEMPORARILY to specific items
within their category line. They rotate with promotions and are NOT permanent category slots.
Preferably assign to items that fit naturally within the category of their line.
E.g., A1N (end cap on A1 gondola, north) should feature promotional snacks, not pasta.
F1 (entrance pallet) carries rotating tempting offers / special discounts, never a fixed SKU."""
from layout_common import FAM, R, label_fit

Z = []  # (code, family, polygon, fa, en, fixture)
def z(code, fam, poly, fa, en, fix): Z.append((code, fam, poly, fa, en, fix))

# ---- 1. entrance (bottom right) and fresh
z("C1", "stap", R(30.49, 10.21, 31.42, 12.19), "روغن", "Oils", "۲ ماژول قفسهٔ نیمه‌سنگین")
z("C2", "stap", R(30.49, 12.15, 31.42, 15.10), "برنج", "Rice", "۳ ماژول قفسهٔ نیمه‌سنگین")
z("F1", "promo", R(26.50, 13.40, 28.90, 13.95), "پیشنهاد ویژه", "Special offers", "پالت‌چینی ۵ ردیفه")
# ---- 2. right pocket: service counter and wall rack
z("S1", "snack", R(26.50, 14.50, 29.20, 15.70), "آجیل و خشکبار", "Nuts & dried fruit", "پیشخوان آجیل با فروشنده")
z("W1", "snack", R(27.20, 16.10, 30.85, 16.50), "آجیل فله", "Bulk nuts", "استند آجیل ۵ طبقه")
# ---- 3. top wall: cleaning/hygiene, dairy, frozen
z("T1", "nonf", R(26.12, 16.70, 26.62, 20.56), "شوینده و بهداشتی", "Cleaning & hygiene", "قفسهٔ دیواری ۵ ماژول")
z("M1", "cold", R(22.70, 20.55, 26.40, 21.60), "شیر، ماست، پنیر، کره، تخم‌مرغ و نوشیدنی", "Dairy, eggs & drinks", "یخچال ایستاده روباز ۳٫۷۵ متر")
z("Z1", "cold", R(20.60, 20.80, 22.60, 21.60), "منجمد", "Frozen food", "فریزر دیواری ۲ متر")
# ---- 4. left gondola A1 (+ stand): grocery, breakfast, personal care
z("X1", "promo", R(20.30, 13.50, 20.90, 19.35), "پیشنهاد هفته", "Weekly offers", "پالت‌چینی ۱۰ ردیفه")
FACE = {  # code: (family, fa, en, polygon)
    "A1W": ("stap", "کنسرو و پودر کیک و ادویه", "Cans, cake flour & spices", R(21.86, 14.45, 22.37, 18.44)),
    "A1E": ("stap", "ماکارونی، پاستا، رب و سس", "Pasta, paste & sauces", R(22.37, 14.45, 22.87, 18.44)),
    "A2W": ("bfst", "چای، قهوه و صبحانه", "Tea, coffee & breakfast", R(23.96, 14.45, 24.46, 18.44)),
    "A2E": ("nonf", "بهداشتی و کاغذی", "Personal care & paper", R(24.46, 14.45, 24.97, 18.44)),
}
for code, (fam, fa, en, poly) in FACE.items():
    z(code, fam, poly, fa, en, "گوندولای دوطرفه — ۴ ماژول")
z("A1N", "promo", R(21.86, 18.44, 22.87, 19.39), "پیشنهاد", "End cap", "سرقفسهٔ ۲۲۸")
z("A1S", "stap", R(21.86, 13.51, 22.87, 14.45), "رب", "Paste", "سرقفسهٔ ۲۲۸")
z("A2N", "promo", R(23.96, 18.44, 24.97, 19.39), "پیشنهاد", "End cap", "سرقفسهٔ ۲۲۸")
z("A2S", "promo", R(23.96, 13.51, 24.97, 14.45), "پیشنهاد", "End cap", "سرقفسهٔ ۲۲۸")
# ---- 5. left wall: ice cream and snacks
z("L1", "snack", R(18.80, 16.70, 19.35, 18.70), "بیسکویت، کیک و تنقلات", "Biscuits, cakes & snacks", "قفسهٔ دیواری ۲ ماژول")
# L3 is the wall shelving mounted above the L2 freezers, running the full length between the two columns
# (y 11.32 -> 16.00); in plan it is drawn as a strip along the wall with L2 in front of it.
z("L2", "cold", R(19.25, 12.40, 19.95, 15.40), "بستنی", "Ice cream", "۲ فریزر بستنی ۱٫۵ متر")
z("L3", "snack", R(18.80, 11.32, 19.25, 16.00), "پفک، چیپس و تنقلات", "Puffs, chips & snacks", "قفسهٔ دیواری سرتاسری بالای فریزر بستنی (۵ ماژول، بین دو ستون)")
# ---- 6. bottom: serve-over meat counter, meat chiller, till impulse
z("D2", "cold", R(20.60, 10.73, 24.30, 11.75), "گوشت و مرغ سرد", "Chilled meat & poultry", "یخچال ویترینی روباز ۳٫۷۵ متر + میز ترازو")
z("D1", "cold", R(23.23, 9.10, 24.79, 9.97), "مرغ و گوشت", "Meat & poultry", "یخچال ایستاده ۲ در")
z("K1", "snack", R(24.35, 10.85, 24.75, 12.24), "شکلات", "Chocolate", "رک کنار صندوق")
z("K2", "nonf", R(28.26, 10.20, 28.88, 12.77), "باتری و کالای ریز", "Batteries & small goods", "رک کنار صندوق ۳ ماژول")

CODES = {c[0] for c in Z}
assert len(CODES) == len(Z), "duplicate code"

SHORT = {c: fa for c, fam, poly, fa, en, fix in Z}  # on-plan label = the category name itself …
SHORT.update({  # …except on narrow faces, where a shorter label keeps the plan readable (full name stays in the list)
    "A1W": "کنسرو و ادویه", "A1E": "ماکارونی و رب", "A2W": "چای و قهوه", "A2E": "بهداشتی", "T1": "شوینده",
    "X1": "پیشنهاد", "A1S": "رب", "C1": "روغن", "C2": "برنج",
})

# ---- colour-based grouping: one group per family, tint drawn over every shelf of that colour.
#      Group floor labels are suppressed (META["group_floor_labels"]=False); the legend chips carry the names.
_POLY = {c: poly for c, fam, poly, fa, en, fix in Z}
_GFA = {  # family -> group name (shown in the legend)
    "stap": "خواربار و پخت‌وپز", "snack": "تنقلات، آجیل و شیرینی", "cold": "یخچالی، لبنی و منجمد",
    "bfst": "صبحانه و نوشیدنی گرم", "nonf": "غیرغذایی و بهداشتی", "promo": "پیشنهاد و پروموشن",
}
_GEN = {"stap": "Grocery & cooking", "snack": "Snacks, nuts & sweets", "cold": "Chilled, dairy & frozen",
        "bfst": "Breakfast & hot drinks", "nonf": "Non-food & hygiene", "promo": "Offers & promotion"}
_ORDER = ["stap", "snack", "cold", "bfst", "nonf", "promo"]  # legend order

def _poly_area(p):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(p, p[1:] + p[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2

GROUPS = []  # id, family, fa, en, polygons, label (x, y), label rotation, members
for _i, _fam in enumerate(_ORDER, start=1):
    _members = [c for c, fam, poly, fa, en, fix in Z if fam == _fam]
    if not _members:
        continue
    _polys = [_POLY[c] for c in _members]
    _big = max(_members, key=lambda c: _poly_area(_POLY[c]))
    _xs = [p[0] for p in _POLY[_big]]; _ys = [p[1] for p in _POLY[_big]]
    _lab = ((min(_xs) + max(_xs)) / 2, (min(_ys) + max(_ys)) / 2)
    GROUPS.append((str(_i), _fam, _GFA[_fam], _GEN[_fam], _polys, _lab, 0, _members))

_cov = sorted(c for g in GROUPS for c in g[7])
assert _cov == sorted(CODES), set(CODES) ^ set(_cov)

# entrance: straight up, then left through the aisle between F1 and S1
FLOW = [(30.0, 9.3), (30.0, 14.22), (25.85, 14.22), (25.85, 19.65), (21.35, 19.65), (21.35, 12.65), (26.5, 12.65), (26.5, 9.3)]
SPINE = [(29.4, 9.6), (29.4, 13.0), (27.0, 12.75), (27.0, 12.4)]

META = dict(
    id="yaran-sabz-bukan", name="یاران سبز بوکان", date="۱۵ مهر ۱۴۰۵",
    eyebrow="طرح چیدمان دسته‌کالا · یاران سبز بوکان",
    h1="با همین تجهیزات، چیدمان دسته‌کالا آمادهٔ اجراست؛ نیازی به جابه‌جایی تجهیز نیست.",
    sub="بر پایهٔ همین قفسه‌ها و یخچال‌ها · مسیر پادساعتگرد از ورود تا صندوق",
    crop=(18.35, 8.2, 13.5, 14.3),
    stats=[("جایگاه دسته‌کالا", "{zones}"), ("گروه رنگی", 6), ("متر یخچال و فریزر", 14), ("گوندولا", 2)],
    group_floor_labels=False,  # grouping shown by colour tint + legend, not big floor text
    decisions=[
        "دسته‌بندی بر پایهٔ رنگ: هر خانوادهٔ کالایی یک رنگ دارد و همهٔ قفسه‌های آن رنگ یک گروه‌اند. [[C1]] [[A1W]]",
        "خواربار و پخت‌وپز (سبز): روغن، برنج، کنسرو، ماکارونی و رب. [[C1]] [[A1E]]",
        "یخچالی، لبنی و منجمد (آبی): لبنیات، بستنی، منجمد و گوشت و مرغ سرد. [[M1]] [[D2]]",
        "غیرغذایی و بهداشتی (بنفش): شوینده و بهداشتی روی دیوار بالا و گوندولای راست، جدا از خوراکی. [[T1]] [[A2E]]",
    ],
    route=[("stap", "خواربار: روغن، برنج، کنسرو، ماکارونی و رب"), ("snack", "آجیل، خشکبار، تنقلات و شیرینی"),
           ("cold", "لبنیات، منجمد، بستنی و گوشت و مرغ سرد"), ("bfst", "چای، قهوه و صبحانه"),
           ("nonf", "شوینده، بهداشتی و کاغذی"), ("promo", "پیشنهادها و پروموشن (ورودی و پالت‌ها)")],
    pro="قوت نقشه: دسته‌بندی رنگ‌محور · هر خانواده یک رنگ · ورود و خروج جدا · مسیر پادساعتگرد · راهروی اصلی ۱٫۵۹ تا ۱٫۷۰ متر",
    stations=[
        ("خواربار و پخت‌وپز", ["C1", "C2", "A1W", "A1E", "A1S"]),
        ("تنقلات، آجیل و شیرینی", ["S1", "W1", "L1", "L3", "K1"]),
        ("یخچالی، لبنی و منجمد", ["M1", "Z1", "L2", "D2", "D1"]),
        ("صبحانه و نوشیدنی گرم", ["A2W"]),
        ("غیرغذایی و بهداشتی", ["T1", "A2E", "K2"]),
        ("پیشنهاد و پروموشن", ["F1", "X1", "A1N", "A2N", "A2S"]),
    ],
    doors=[("ورود", 30.0, 8.65, False), ("خروج", 26.5, 8.65, False)],
    ghosts=[], moves=[],
    legend=dict(x=18.5, y=5.2, cols=3, dx=4.5, w=4.4, chips_per_row=4, chip_dx=3.4),
)
