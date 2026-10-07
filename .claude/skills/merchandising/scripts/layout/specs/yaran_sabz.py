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
z("C1", "stap", R(30.49, 10.21, 31.42, 12.19), "انواع روغن", "Oils", "۲ ماژول قفسهٔ نیمه‌سنگین")
z("C2", "stap", R(30.49, 12.15, 31.42, 15.10), "برنج و روغن (کیسه و گالن)", "Rice & oil", "۳ ماژول قفسهٔ نیمه‌سنگین")
z("F1", "promo", R(26.50, 13.40, 28.90, 13.95), "پیشنهاد وسوسه‌انگیز و تخفیفات ویژه", "Tempting offers & special discounts", "پالت‌چینی ۵ ردیفه")
# ---- 2. right pocket: service counter and wall rack
z("S1", "bfst", R(26.50, 14.50, 29.20, 15.70), "آجیل و خشکبار (سرو وزنی)", "Nuts & dried fruit (served)", "پیشخوان آجیل با فروشنده")
z("W1", "bfst", R(27.20, 16.10, 30.85, 16.50), "آجیل، حبوبات و ادویه جات فله", "Bulk nuts, pulses & spices", "استند آجیل ۵ طبقه")
# ---- 3. top wall: breakfast next to dairy, frozen
z("T1", "bfst", R(26.12, 16.70, 26.62, 20.56), "چای، قهوه، قند، عسل و مربا", "Tea, coffee, sugar, honey, jam", "قفسهٔ دیواری ۵ ماژول")
z("M1", "cold", R(22.70, 20.55, 26.40, 21.60), "شیر، ماست، پنیر، کره و تخم‌مرغ", "Dairy & eggs", "یخچال ایستاده روباز ۳٫۷۵ متر")
z("Z1", "cold", R(20.60, 20.80, 22.60, 21.60), "منجمد: مرغ، گوشت و سبزی", "Frozen food", "فریزر دیواری ۲ متر")
# ---- 4. left gondola A1 (+ stand): dry food and oil
z("X1", "promo", R(20.30, 13.50, 20.90, 19.35), "پیشنهاد هفته و فصلی (نوشابه و آب معدنی باکسی)", "Weekly offers (water & mineral water boxes)", "پالت‌چینی ۱۰ ردیفه")
FACE = {  # code: (family, fa, en, polygon)
    "A1W": ("bfst", "ماکارانی و انواع پودر کیک و ادویه جات", "Pasta, cake flour & spices", R(21.86, 14.45, 22.37, 18.44)),
    "A1E": ("stap", "کنسرو، رب و انواع سس", "Cans, paste & sauces", R(22.37, 14.45, 22.87, 18.44)),
    "A2W": ("nonf", "شوینده و نظافت منزل", "Cleaning", R(23.96, 14.45, 24.46, 18.44)),
    "A2E": ("nonf", "بهداشتی، سلولزی و پوشک", "Personal care & paper", R(24.46, 14.45, 24.97, 18.44)),
}
for code, (fam, fa, en, poly) in FACE.items():
    z(code, fam, poly, fa, en, "گوندولای دوطرفه — ۴ ماژول")
z("A1N", "promo", R(21.86, 18.44, 22.87, 19.39), "پیشنهاد تنقلات", "End cap", "سرقفسهٔ ۲۲۸")
z("A1S", "stap", R(21.86, 13.51, 22.87, 14.45), "رب و سس", "Paste & sauces", "سرقفسهٔ ۲۲۸")
z("A2N", "promo", R(23.96, 18.44, 24.97, 19.39), "پیشنهاد شوینده", "End cap", "سرقفسهٔ ۲۲۸")
z("A2S", "promo", R(23.96, 13.51, 24.97, 14.45), "پیشنهاد سلولزی", "End cap", "سرقفسهٔ ۲۲۸")
# ---- 5. left wall: ice cream and snacks
z("L1", "snack", R(18.80, 16.70, 19.35, 18.70), "بیسکویت، کیک، تنقلات، پفک، چیپس و انواع آلوچه", "Biscuits, cakes, snacks, chips & dried fruit", "قفسهٔ دیواری ۲ ماژول")
z("L2", "cold", R(18.85, 12.40, 19.95, 15.40), "بستنی", "Ice cream", "۲ فریزر بستنی ۱٫۵ متر")
z("L3", "snack", R(18.95, 9.90, 19.75, 13.10), "پفک، چیپس و تنقلات (اندازه خاص، طبق خط‌کشی مشتری)", "Puffs, chips & snacks (special size, per client markup)", "قفسهٔ دیواری ۲ ماژول")
# ---- 6. bottom: serve-over cold counter, drinks chiller, till impulse
z("D2", "cold", R(20.60, 10.73, 24.30, 11.75), "گوشت و مرغ سرد شده، پنیر وزنی و لبنیات سنتی", "Chilled meat & poultry, loose cheese, traditional dairy", "یخچال ویترینی روباز ۳٫۷۵ متر + میز ترازو")
z("D1", "cold", R(23.23, 9.10, 24.79, 9.97), "نوشابه و آب معدنی سرد", "Cold drinks & mineral water", "یخچال ایستاده ۲ در")
z("K1", "snack", R(24.35, 10.85, 24.75, 12.24), "شکلات و آدامس", "Till impulse", "رک کنار صندوق")
z("K2", "snack", R(28.26, 10.20, 28.88, 12.77), "باتری و آدامس", "Till impulse", "رک کنار صندوق ۳ ماژول")

CODES = {c[0] for c in Z}
assert len(CODES) == len(Z), "duplicate code"

SHORT = {"C1": "روغن", "C2": "برنج", "F1": "پیشنهاد ویژه", "S1": "آجیل و خشکبار", "W1": "آجیل فله", "T1": "چای و صبحانه",
         "M1": "لبنیات و تخم‌مرغ", "Z1": "منجمد", "X1": "پیشنهاد هفته", "A1W": "ماکارانی و ادویه", "A1E": "کنسرو و رب", "A2W": "شوینده",
         "A2E": "بهداشتی و کاغذی", "A1S": "رب", "L1": "بیسکویت و تنقلات", "L2": "بستنی", "L3": "پفک و چیپس", "D2": "گوشت و مرغ سرد", "D1": "نوشابه سرد",
         "K1": "شکلات", "K2": "باتری"}

GROUPS = [  # id, family, fa, en, polygons, label (x, y), label rotation, members
    ("1", "frsh", "ورودی: میوه، آب و برنج", "Entrance: produce & heavy goods",
     [[(29.0, 9.2), (31.65, 9.2), (31.65, 15.25), (29.0, 15.25), (29.0, 14.1), (26.4, 14.1), (26.4, 13.3), (29.0, 13.3)]], (29.35, 11.6), 90, ["C1", "C2", "F1"]),
    ("2", "bfst", "آجیل و خشکبار", "Nuts & dried fruit",
     [[(26.4, 14.15), (29.0, 14.15), (29.0, 15.3), (31.65, 15.3), (31.65, 16.6), (26.4, 16.6)]], (30.4, 15.7), 0, ["S1", "W1"]),
    ("3", "cold", "لبنیات، منجمد و صبحانه", "Dairy, frozen & breakfast",
     [[(20.5, 21.7), (26.8, 21.7), (26.8, 16.6), (26.0, 16.6), (26.0, 20.05), (20.5, 20.05)]], (23.5, 20.2), 0, ["T1", "M1", "Z1"]),
    ("4", "snack", "", "",
     [[(20.2, 13.4), (22.95, 13.4), (22.95, 19.45), (20.2, 19.45)]], (21.4, 16.4), 90, ["X1", "A1W", "A1E", "A1N", "A1S"]),
    ("5", "nonf", "بهداشتی و نظافت", "Personal care & cleaning",
     [[(23.9, 13.4), (25.05, 13.4), (25.05, 19.45), (23.9, 19.45)]], (25.4, 16.4), 90, ["A2W", "A2E", "A2N", "A2S"]),
    ("6", "stap", "بستنی و شیرینی", "Ice cream & sweets",
     [[(18.5, 11.2), (20.2, 11.2), (20.2, 18.8), (18.5, 18.8)]], (19.95, 17.2), 90, ["L1", "L2", "L3"]),
    ("7", "drnk", "یخچال سرد و صندوق", "Chillers & tills",
     [[(20.5, 9.1), (29.0, 9.1), (29.0, 13.0), (20.5, 13.0)]], (22.0, 10.3), 0, ["D1", "D2", "K1", "K2"]),
]
_cov = sorted(c for g in GROUPS for c in g[7])
assert _cov == sorted(CODES), set(CODES) ^ set(_cov)

FLOW = [(30.0, 9.3), (30.0, 13.1), (25.85, 13.1), (25.85, 19.65), (21.35, 19.65), (21.35, 12.65), (26.5, 12.65), (26.5, 9.3)]
SPINE = [(29.4, 9.6), (29.4, 13.0), (27.0, 12.75), (27.0, 12.4)]

META = dict(
    id="yaran-sabz-bukan", name="یاران سبز بوکان", date="۱۵ مهر ۱۴۰۵",
    eyebrow="طرح چیدمان دسته‌کالا · یاران سبز بوکان",
    h1="با همین تجهیزات، چیدمان دسته‌کالا آمادهٔ اجراست؛ نیازی به جابه‌جایی تجهیز نیست.",
    sub="بر پایهٔ همین قفسه‌ها و یخچال‌ها · مسیر پادساعتگرد از ورود تا صندوق",
    crop=(18.35, 8.2, 13.5, 14.3),
    stats=[("جایگاه دسته‌کالا", "{zones}"), ("گروه کالایی", 7), ("متر یخچال و فریزر", 14), ("گوندولا", 2)],
    decisions=[
        "ورودی: پالت پیشنهاد ویژه و تخفیف؛ روغن و برنج روی قفسهٔ نیمه‌سنگین دیوار راست. [[F1]] [[C1]] [[C2]]",
        "آجیل و خشکبار در پیشخوان سرو گوشهٔ راست، درست روی مسیر. [[S1]]",
        "صبحانه و چای روی دیوار بالا، کنار لبنیات و منجمد. [[T1]] [[M1]]",
        "گوندولای چپ: چیپس (قفسهٔ سبدی) و خوراکی خشک؛ گوندولای راست: بهداشتی و نظافت، جدا از خوراکی. [[A1W]] [[A2W]]",
    ],
    route=[("frsh", "ورود ← پالت پیشنهاد ویژه، روغن و برنج"), ("bfst", "آجیل و خشکبار (پیشخوان)"), ("cold", "صبحانه ← لبنیات ← منجمد (دیوار بالا)"),
           ("snack", "چیپس و خوراکی خشک (گوندولای چپ)"), ("nonf", "بهداشتی و نظافت (گوندولای راست)"),
           ("stap", "بستنی و شیرینی (دیوار چپ)"), ("drnk", "پنیر وزنی و نوشابهٔ سرد ← صندوق ← خروج")],
    pro="قوت نقشه: ورود و خروج جدا · مسیر پادساعتگرد · راهروی اصلی ۱٫۵۹ تا ۱٫۷۰ متر · یخچال بلند لبنیات روی دیوار بالا",
    stations=[
        ("ورودی: پالت پیشنهاد ویژه و قفسهٔ نیمه‌سنگین", ["F1", "C1", "C2"]),
        ("پیشخوان آجیل و خشکبار", ["S1", "W1"]),
        ("دیوار بالا: صبحانه، لبنیات و منجمد", ["T1", "M1", "Z1"]),
        ("گوندولای چپ و پالت: تنقلات و خوراکی خشک", ["X1", "A1W", "A1E", "A1N", "A1S"]),
        ("گوندولای راست: بهداشتی و نظافت", ["A2W", "A2E", "A2N", "A2S"]),
        ("دیوار چپ: بستنی و شیرینی", ["L1", "L2", "L3"]),
        ("یخچال‌های پایین و کنار صندوق", ["D2", "D1", "K1", "K2"]),
    ],
    doors=[("ورود", 30.0, 8.65, False), ("خروج", 26.5, 8.65, False)],
    ghosts=[], moves=[],
    legend=dict(x=18.5, y=5.2, cols=3, dx=4.5, w=4.4, chips_per_row=4, chip_dx=3.4),
)
