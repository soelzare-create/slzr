---
name: p2p-radio-connection
description: P2P Radio Connection. Plans point-to-point and point-to-multipoint wireless (radio) links between two or more locations. It takes Google Maps links or coordinates and calculates distance, azimuth, ground-elevation difference, earth curvature, Fresnel clearance, the mast height each end needs, and the link budget. It then recommends radios available in the Iranian market (MikroTik, Ubiquiti, TP-Link, Cambium) at three price tiers with live prices, and delivers a cinematic Persian HTML report. Use this skill whenever the user wants to connect buildings, branches, cameras, a warehouse or a remote site wirelessly, asks about "لینک رادیویی", "ارتباط رادیویی", "وایرلس نقطه به نقطه", "PtP", "PtMP", "دکل", "آنتن دیش", "Fresnel", "line of sight", or mast height, or pastes two or more map locations and asks how to link them, even if they never say "skill".
---

# P2P Radio Connection

Design a wireless link the way a field engineer does: measure, check the path, size the masts, prove the signal arrives with margin, then pick hardware the customer can actually buy in Iran at today's price. Finish with a report the customer can read without being an RF engineer.

Talk to the user in Persian. Keep the numbers exact and say where each one came from.

## 1. Collect the inputs (one message, with defaults)

Ask for everything below in a single message, so the user answers once. Offer the default in brackets for anything they may not know. Do not block on optional items.

1. **Locations:** a Google Maps link or `lat, lon` for each point, plus a short name (e.g. «دفتر مرکزی»). Shortened `maps.app.goo.gl` links work when the network allows; otherwise ask for the full link.
2. **Where the antenna sits:** building height or roof height in metres at each point, and any existing mast on it. [Default: single-storey building, 4 m]
3. **Obstacles along the path:** tall buildings, towers, trees, hills, with their approximate height and position (distance from one end, or a map link). Also the typical building height of the neighbourhood (clutter). [Default clutter: 9 m in city areas, 0 m in open land]
4. **Required throughput** in real Mbps and what it carries: internet, CCTV cameras (about 4–8 Mbps per 1080p camera), VoIP, or a mix. [Default: 50 Mbps]
5. **Topology** when there are more than two points: one central point linking to the others (star), a chain, or a separate link for each pair. [Default: star from the most central point, which the script picks]
6. **Budget preference:** economy, balanced or professional. [Default: show all three]
7. **Limits:** the highest mast allowed on each roof, and whether a short outage in dust storms is acceptable (this decides whether 60 GHz is an option). [Default: up to 36 m mast; outages not acceptable]

The ground elevation comes from the terrain data, so do not ask for it unless the online lookup fails.

**Why ask about buildings and obstacles:** satellite elevation models are bare earth plus a smoothed surface. They miss most buildings, new towers and trees. In flat cities such as Ahvaz the buildings, not the terrain, decide the mast height. A wrong building height gives a wrong mast height.

## 2. Write the project file and run the calculator

Write `project.json` in the working or scratchpad directory. The full schema is in the docstring of `scripts/link_calc.py`. Minimal example:

```json
{
  "project": "دفتر مرکزی به انبار",
  "freq_ghz": 5.8,
  "required_mbps": 80,
  "clutter_m": 9,
  "sites": [
    {"id": "A", "name": "دفتر مرکزی", "loc": "https://maps.google.com/maps?q=31.3251%2C48.6282", "building_m": 15},
    {"id": "B", "name": "انبار", "loc": "31.2895, 48.6851", "building_m": 6, "existing_mast_m": 3}
  ],
  "obstacles": [{"link": "A-B", "at_km": 2.5, "height_m": 30, "name": "برج مسکونی"}]
}
```

Then run:

```bash
python3 <skill>/scripts/link_calc.py project.json -o results.json
```

What the script does:

- It parses the map links.
- It samples the terrain every ~25 m along the path. It tries OpenTopoData SRTM 30 m, then Open-Meteo Copernicus, then Open-Elevation.
- It adds clutter, obstacles and earth bulge (k = 4/3).
- It finds the lowest pair of masts that keeps 60 % of the first Fresnel zone clear. It also reports the line-of-sight-only and 100 % Fresnel answers.
- It computes azimuth and tilt for each end.
- It runs a link budget for every radio in `references/radios.json`, picks the highest modulation that keeps the fade margin, and returns three picks: `economy`, `balanced` and `pro`.
- For a star it also checks the azimuth spread at the hub and suggests sector antennas.

**If the elevation lookup fails** (no internet, blocked host), the script warns on stderr and marks `terrain_ok: false`. Then:

- Tell the user.
- Ask for the ground elevation at each end. They can read it in Google Earth at the bottom of the screen. Put the values in `ground_m` for each site.
- Re-run with `--offline`. The report then shows a visible `[NEED]` chip so nobody mistakes it for a full terrain study.

## 3. Read the results like an engineer

Before writing anything for the user, sanity-check `results.json`:

- **Mast taller than about 12 m on a roof** is expensive and needs guy wires. Look at `critical_point_m` and the obstacles. Often a different roof, a relay on a tall building near the middle, or moving the antenna to the other side of the roof is cheaper. Say so.
- **`feasible: false`** means no mast within the limit clears the path. Propose a relay point: ask the user for a tall building near the blocked section. A link to that point is a new pair; add it to `links`.
- **Margin barely above target** (within 3 dB): recommend the next tier up or a narrower channel. Dust, heat and alignment error eat a few dB in Khuzestan.
- **Distance under 1.5 km with high throughput:** mention 60 GHz (gigabit, no interference). If outages are not acceptable, recommend only models with 5 GHz backup.
- **Star topology:** if `advice` is `ptp` (two clients or fewer, or heavy traffic per client), separate PtP links are better than one sector. Explain why: the clients share one sector's airtime.

For the formulas, rules of thumb and how to explain them in Persian, see `references/method.md`.

## 4. Look up live prices (never invent them)

Prices in Iran change week to week, so the catalog holds no prices. For every model in `picks` (and the AP/CPE pair for a star), search the web for today's price. Use the `search` field of the catalog, for example `قیمت MikroTik LHG 5 ac` or `site:torob.com LHG 5 ac`. Good sources are torob.com (it lists many shops), digikala.com and specialised network shops.

Write `prices.json`:

```json
{"date": "1405/07/25",
 "items": {"mikrotik-lhg5ac": {"price": "۹٬۲۰۰٬۰۰۰ تومان", "unit": "هر عدد؛ برای لینک ۲ عدد لازم است", "source": "https://torob.com/...", "shop": "ترب"}}}
```

Rules:

- Note whether the price is for one unit or a pair. A PtP link needs two units unless the product is sold as a kit.
- Use the Jalali date.
- If you find no trustworthy price, leave the model out. The report then shows `[NEED: قیمت روز]`. A wrong price is worse than a missing one.
- If web search is not available, say so and leave prices empty.

## 5. Build the cinematic report

```bash
python3 <skill>/scripts/build_report.py results.json --prices prices.json -o report.html
```

This produces one self-contained Persian RTL HTML file (about 350 KB: font, GSAP and the cinematic-story engine are inlined), so it opens offline and can be sent on WhatsApp or Telegram. It follows the cinematic-story-site method: one scroll gesture plays one scene.

- **Act 1, map:** the sites appear, the link lines draw with their distance, then the antenna bearings appear.
- **Act 2, path profile (one per link, up to 4):** terrain, then obstacles, then earth bulge, then the masts rise, then the Fresnel zone appears with its clearance %.
- **Act 3, link budget:** transmit power, then path loss, then received signal, then fade margin against receiver sensitivity.
- **Sections:** a plain summary, three equipment tiers per link with prices, PtMP sector advice, the installation sheet (coordinates, mast, antenna height, azimuth, tilt), the field checklist and the assumptions.

With reduced motion it falls back to a static, fully readable layout.

Optional QA, when Playwright is available:

```bash
node <cinematic-story-site>/scripts/qa.js report.html qa-out
```

Look at the screenshots and fix any label that sits on a shape.

Deliver the HTML file to the user: send it as a file and/or publish it as an artifact if those tools exist. Then give a short summary in chat.

## 6. The chat summary

Keep it short. The report carries the detail. Include:

- One line per link: distance, ground-elevation difference, mast at each end, azimuths.
- The recommended (balanced) radio with its real throughput, margin and price.
- What is still open: `[NEED]` items, missing prices, and assumptions the user should confirm (building heights, obstacles).
- Before anyone buys hardware: a site survey with line-of-sight from the roof, an interference scan, and the regulator's (سازمان تنظیم مقررات) band and EIRP limits.

## Files

- `scripts/link_calc.py`: all calculations, standard library only (Python 3.8+).
- `scripts/build_report.py`: the cinematic HTML report.
- `references/radios.json`: radio catalog with gain, power, channel width, real throughput, range, price rank and search terms. Update it when the market changes; values are typical datasheet figures.
- `references/method.md`: formulas, rules of thumb, band choice, Iranian market notes and Persian explanations.
- `assets/engine`, `assets/vendor`, `assets/fonts`: the cinematic-story engine (GSAP, free licence), base CSS and the Vazirmatn font (OFL).
