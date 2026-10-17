# Method, formulas and rules of thumb

Read this file when you need to explain a number to the user or to judge whether a result makes sense.

## Formulas used by link_calc.py

| Quantity | Formula | Units |
|---|---|---|
| Distance | Haversine on a 6371 km sphere | m |
| Azimuth | initial great-circle bearing, from true north | ° |
| Earth bulge | `h = d1·d2 / (2·k·R)`, with k = 4/3 (standard atmosphere) | m |
| First Fresnel radius | `r = 17.32·√(d1·d2 / (f·D))` | d in km, f in GHz, r in m |
| Free-space path loss | `FSPL = 92.45 + 20·log10(f) + 20·log10(d)` | f in GHz, d in km, dB |
| Received level | `Prx = Ptx + Gtx + Grx − FSPL − cable − 2 dB (alignment/radome)` | dBm |
| Fade margin | `Prx − sensitivity(MCS, width)` | dB |
| Tilt | `atan(Δh / D) − D / (2·k·R)` | ° |
| Real throughput | `PHY rate × 0.6`, capped by the radio and its port | Mbps |

- **Clearance target.** Keep 60 % of the first Fresnel zone free of obstacles. Use 100 % for critical links or when the obstacle heights are guesses.
- **Fade margin target.** The calculator uses 15 dB under 5 km, 20 dB for 5–15 km and 25 dB beyond 15 km.
- **Receiver sensitivity.** These are typical 2×2 802.11ac figures at 20 MHz, from MCS0 to MCS9: −95, −93, −91, −88, −85, −81, −79, −77, −72, −70 dBm. Each doubling of channel width costs 3 dB.
- **Transmit power** drops by 2 to 5 dB at the highest MCS.

## How mast height is chosen

The calculator tries every whole-metre pair of masts, up to the limit. It keeps the pair with the smallest taller mast, then the smallest total. The reason: two moderate masts are cheaper and steadier than one very tall one.

- A mast is measured **above the roof** (`building_m`).
- Antenna height above ground = `building_m` + mast.
- An existing mast is subtracted, so the report shows how many metres are actually new.

## Buildings in the corridor (OpenStreetMap)

The radio corridor is the strip along the path that is as wide as the first Fresnel zone at mid-path, plus 30 m.

- For each OSM building in the corridor, the height comes from the `height` tag, or from `building:levels` × 3.2 m.
- A building beside the line at lateral offset `x` intrudes into the clearance zone (radius `rr = 0.6·F1`) only if `x < rr`.
- It is then entered as a centre-line obstacle of height `h + rr − √(rr² − x²)`, which keeps the same clearance test.
- A footprint that straddles the line is treated as `x = 0`.

## Explaining it in plain Persian

| Term | How to say it |
|---|---|
| Fresnel zone | «سیگنال مثل یک دوک یا بادکنک کشیده بین دو آنتن پخش می‌شود، نه یک خط باریک. اگر بیش از ۴۰٪ آن را مانع بگیرد، سیگنال ضعیف و ناپایدار می‌شود.» |
| Earth bulge | «زمین گرد است؛ در وسط یک مسیر ۱۰ کیلومتری حدود ۱٫۵ متر بالا می‌آید.» |
| Fade margin | «ذخیرهٔ سیگنال برای روزهای گردوخاکی، گرما و جابه‌جایی جزئی آنتن.» |
| EIRP | «توان مؤثری که آنتن در جهت لینک می‌فرستد؛ سقف قانونی دارد.» |

## Choosing the band

| Band | Use when | Watch out for |
|---|---|---|
| 5 GHz (5.15–5.85) | almost every link up to about 30 km | crowded in cities; scan for a free channel and prefer 20/40 MHz width |
| 60 GHz | under 1.5 km, gigabit, no interference | oxygen absorption, rain and heavy dust; pick a model with 5 GHz backup when outages are not acceptable |
| 2.4 GHz | only through light foliage at short range | crowded, low capacity; avoid for backhaul |

Check the bands and the maximum EIRP allowed in Iran against the current rules of the regulator (سازمان تنظیم مقررات و ارتباطات رادیویی) before final design. They change, and the calculator does not enforce them.

## Iranian market notes

- **MikroTik and Ubiquiti dominate** and are the easiest to service and resell. TP-Link CPE is the budget option. Cambium is good but harder to find.
- **Do not mix ecosystems on one link.** MikroTik Nv2, Ubiquiti airMAX and TP-Link MAXtream do not interoperate. Both ends of a PtP link should be the same model. A PtMP AP and its clients must share an ecosystem.
- **Prices move with the dollar rate.** Always search on the day and show the date. Typical sources: torob.com (price comparison), digikala.com and specialised network shops. Check that the shop has stock and offers a warranty (گارانتی).
- **Counterfeit and refurbished units circulate.** Recommend shops with a warranty and serial check.

## Khuzestan field notes

- **Summer roof temperatures pass 60 °C.** Prefer radios rated to +70 °C, leave airflow behind the unit, and keep the PoE adapter indoors.
- **Dust storms** add loss at 60 GHz and coat radomes. Keep at least 3 dB above the target margin on 5 GHz links.
- **Ground** is flat (about 15–25 m above sea level in Ahvaz). Buildings set the mast height, so ask carefully about tall buildings near the path centre, where the Fresnel zone is widest.
- **Magnetic declination** is about +3° (east). A compass reads about 3° less than the true azimuth in the report.

## Field checklist (also in the report)

1. Line-of-sight check from the roof with binoculars, a drone or a mirror flash.
2. Interference scan (MikroTik Scan / Ubiquiti airView), then pick the channel and width.
3. Rigid mast with guy wires; narrow beams (≤ 5°) do not tolerate sway.
4. Outdoor shielded CAT6, waterproof connectors, mast earthing, PoE surge protector, UPS.
5. Align for the best signal at both ends, then confirm the measured signal is within about 5 dB of the predicted `rx_dbm`. A larger gap means misalignment or a hidden obstacle.
