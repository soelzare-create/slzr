#!/usr/bin/env python3
"""Merchandising calculator — deterministic retail-math and retail-execution KPIs.

Standard library only. Money uses Decimal (Rial amounts are large integers);
percentages are printed with two decimals. Each sub-command prints
``key: value`` lines (or JSON with ``--json``) so output is easy to paste into
a report or a test.

Examples:
    python merch_calc.py markup-margin --cost 70 --price 100
    python merch_calc.py price --cost 1200000 --margin 25
    python merch_calc.py gmroi --gross-margin 450000000 --avg-inventory-cost 300000000
    python merch_calc.py sell-through --sold 80 --beginning 100 --received 20
    python merch_calc.py turnover --cogs 1200 --avg-inventory 300
    python merch_calc.py wos --on-hand 240 --weekly-sales 60
    python merch_calc.py otb --planned-sales 500 --planned-markdowns 30 \
        --planned-eom 800 --planned-bom 700 --on-order 50
    python merch_calc.py imu --expenses 25 --profit 10 --reductions 8 --net-sales 100
    python merch_calc.py sos --brand-facings 18 --total-facings 60 --market-share 25
    python merch_calc.py osa --available 46 --checked 50
    python merch_calc.py compliance --passed 17 --audited 20
    python merch_calc.py perfect-store --component osa=92:40 --component pog=80:30 \
        --component price=100:20 --component posm=50:10
    python merch_calc.py visit-cost --monthly-cost 300000000 --working-days 24 \
        --visits-per-day 6 --travel-per-visit 150000 --price-per-visit 3500000
    python merch_calc.py occupancy --gross 1422 --sales 1206 --checkouts 6 \
        --gondola-area 100.8 --block-area 273.5 --gondola-depth 1 --aisle 1.8
    python merch_calc.py selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().prec = 28
HUNDRED = Decimal("100")


def D(value) -> Decimal:
    return Decimal(str(value))


def pct(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def ratio(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _require_positive(name: str, value: Decimal) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be > 0 (got {value})")


# --- Pricing ---------------------------------------------------------------
def markup_margin(cost=None, price=None, markup=None, margin=None) -> dict:
    """Markup is profit/cost; margin is profit/price. Give cost+price, or one %."""
    if cost is not None and price is not None:
        cost, price = D(cost), D(price)
        _require_positive("cost", cost)
        _require_positive("price", price)
        profit = price - cost
        return {
            "profit": money(profit),
            "markup_pct": pct(profit / cost * HUNDRED),
            "margin_pct": pct(profit / price * HUNDRED),
        }
    if markup is not None:
        m = D(markup) / HUNDRED
        return {"markup_pct": pct(m * HUNDRED), "margin_pct": pct(m / (1 + m) * HUNDRED)}
    if margin is not None:
        g = D(margin) / HUNDRED
        if g >= 1:
            raise ValueError("margin must be < 100%")
        return {"margin_pct": pct(g * HUNDRED), "markup_pct": pct(g / (1 - g) * HUNDRED)}
    raise ValueError("give --cost and --price, or --markup, or --margin")


def price_from(cost, markup=None, margin=None) -> dict:
    """Selling price that achieves a target markup (on cost) or margin (on price)."""
    cost = D(cost)
    _require_positive("cost", cost)
    if markup is not None:
        price = cost * (1 + D(markup) / HUNDRED)
    elif margin is not None:
        g = D(margin) / HUNDRED
        if g >= 1:
            raise ValueError("margin must be < 100%")
        price = cost / (1 - g)
    else:
        raise ValueError("give --markup or --margin")
    out = {"price": money(price)}
    out.update(markup_margin(cost=cost, price=money(price)))
    return out


def imu(expenses, profit, reductions, net_sales) -> dict:
    """Initial markup % = (expenses + profit + reductions) / (net sales + reductions)."""
    expenses, profit, reductions, net_sales = map(D, (expenses, profit, reductions, net_sales))
    denom = net_sales + reductions
    _require_positive("net_sales + reductions", denom)
    return {"imu_pct": pct((expenses + profit + reductions) / denom * HUNDRED)}


# --- Inventory productivity --------------------------------------------------
def gmroi(gross_margin, avg_inventory_cost) -> dict:
    """Gross margin earned per 1 unit of money tied up in inventory (at cost)."""
    gm, inv = D(gross_margin), D(avg_inventory_cost)
    _require_positive("avg_inventory_cost", inv)
    return {"gmroi": ratio(gm / inv)}


def sell_through(sold, beginning, received=0) -> dict:
    """Sell-through % = units sold / (beginning on hand + units received)."""
    sold, available = D(sold), D(beginning) + D(received)
    _require_positive("beginning + received", available)
    return {"sell_through_pct": pct(sold / available * HUNDRED),
            "units_left": D(beginning) + D(received) - sold}


def turnover(cogs, avg_inventory, days=365) -> dict:
    """Stock turn = COGS / average inventory (both at cost); days of supply = days/turn."""
    cogs, inv = D(cogs), D(avg_inventory)
    _require_positive("avg_inventory", inv)
    turns = cogs / inv
    out = {"turns": ratio(turns)}
    if turns > 0:
        out["days_of_inventory"] = ratio(D(days) / turns)
    return out


def weeks_of_supply(on_hand, weekly_sales) -> dict:
    on_hand, rate = D(on_hand), D(weekly_sales)
    _require_positive("weekly_sales", rate)
    return {"weeks_of_supply": ratio(on_hand / rate)}


def open_to_buy(planned_sales, planned_markdowns, planned_eom, planned_bom, on_order=0) -> dict:
    """OTB = planned sales + planned markdowns + planned EOM − planned BOM − on order."""
    otb = (D(planned_sales) + D(planned_markdowns) + D(planned_eom)
           - D(planned_bom) - D(on_order))
    return {"open_to_buy": money(otb), "over_bought": otb < 0}


# --- Retail execution (shelf) --------------------------------------------------
def share_of_shelf(brand, total, market_share=None) -> dict:
    """SoS % = brand facings (or linear cm) / category total. Fair-share index = SoS / market share."""
    brand, total = D(brand), D(total)
    _require_positive("total", total)
    sos = brand / total * HUNDRED
    out = {"share_of_shelf_pct": pct(sos)}
    if market_share is not None:
        ms = D(market_share)
        _require_positive("market_share", ms)
        out["fair_share_index"] = ratio(sos / ms)  # 1.00 = shelf matches sales share
    return out


def osa(available, checked) -> dict:
    """On-shelf availability % = SKU-store checks found on shelf / checks made."""
    available, checked = D(available), D(checked)
    _require_positive("checked", checked)
    rate = available / checked * HUNDRED
    return {"osa_pct": pct(rate), "oos_pct": pct(HUNDRED - rate)}


def compliance(passed, audited) -> dict:
    """Generic compliance % (planogram, price-tag, POSM, display build)."""
    passed, audited = D(passed), D(audited)
    _require_positive("audited", audited)
    return {"compliance_pct": pct(passed / audited * HUNDRED)}


def perfect_store(components: dict[str, tuple[Decimal, Decimal]]) -> dict:
    """Weighted composite of component scores (0–100) with weights (any scale)."""
    if not components:
        raise ValueError("give at least one --component name=score:weight")
    total_w = sum(w for _, w in components.values())
    _require_positive("sum of weights", total_w)
    score = sum(s * w for s, w in components.values()) / total_w
    out = {"perfect_store_score": pct(score)}
    for name, (s, w) in components.items():
        out[f"{name}_contribution"] = pct(s * w / total_w)
    return out


# --- Field-team economics ------------------------------------------------------
def visit_cost(monthly_cost, working_days, visits_per_day, travel_per_visit=0,
               price_per_visit=None) -> dict:
    """Fully loaded cost of one store visit by one merchandiser, and margin vs a price."""
    monthly_cost, days, vpd = D(monthly_cost), D(working_days), D(visits_per_day)
    _require_positive("working_days", days)
    _require_positive("visits_per_day", vpd)
    visits = days * vpd
    cost = monthly_cost / visits + D(travel_per_visit)
    out = {"visits_per_month": visits, "cost_per_visit": money(cost)}
    if price_per_visit is not None:
        price = D(price_per_visit)
        _require_positive("price_per_visit", price)
        out["margin_per_visit"] = money(price - cost)
        out["margin_pct"] = pct((price - cost) / price * HUNDRED)
    return out


# --- Space occupancy (whole-store plan) ----------------------------------------
# Reference points (US industry data / design guides — see references/store-layout.md §8):
FMI_SALES_SHARE = Decimal("72.4")          # % of total store area that is selling space
FMI_SALES_M2_PER_LANE = Decimal("324")      # ≈ 48,175 ft² × 72.4% / 10 checkout lanes
AISLE_STD_M = (Decimal("1.5"), Decimal("1.8"))  # two-trolley aisle range


def occupancy(gross, sales, checkouts=None, offices_front=None, gondola_area=None,
              block_area=None, gondola_depth=None, aisle=None) -> dict:
    """Area-use ratios of a store plan and their gap to reference values.

    gross/sales/offices_front/gondola_area/block_area in m²; gondola_depth/aisle in m.
    """
    gross, sales = D(gross), D(sales)
    _require_positive("gross", gross)
    _require_positive("sales", sales)
    share = sales / gross * HUNDRED
    out = {"sales_share_pct": pct(share), "ref_sales_share_pct": FMI_SALES_SHARE,
           "sales_share_gap_pts": pct(share - FMI_SALES_SHARE),
           "non_sales_m2": money(gross - sales)}
    if checkouts is not None:
        lanes = D(checkouts)
        _require_positive("checkouts", lanes)
        out["sales_m2_per_checkout"] = money(sales / lanes)
        out["ref_sales_m2_per_checkout"] = FMI_SALES_M2_PER_LANE
    if offices_front is not None:
        out["front_offices_pct_of_gross"] = pct(D(offices_front) / gross * HUNDRED)
    if gondola_area is not None and block_area is not None:
        out["center_block_density_pct"] = pct(D(gondola_area) / D(block_area) * HUNDRED)
    if gondola_depth is not None:
        g = D(gondola_depth)
        lo = g / (g + AISLE_STD_M[1]) * HUNDRED
        hi = g / (g + AISLE_STD_M[0]) * HUNDRED
        out["ref_center_density_pct"] = f"{pct(lo)}-{pct(hi)}"
    if aisle is not None:
        a = D(aisle)
        out["aisle_within_std"] = AISLE_STD_M[0] <= a <= AISLE_STD_M[1]
    return out


# --- CLI -----------------------------------------------------------------------
def _parse_components(raw: list[str]) -> dict[str, tuple[Decimal, Decimal]]:
    out = {}
    for item in raw or []:
        try:
            name, rest = item.split("=", 1)
            score, weight = rest.split(":", 1)
            out[name.strip()] = (D(score), D(weight))
        except ValueError as exc:
            raise ValueError(f"bad --component '{item}', expected name=score:weight") from exc
    return out


def selftest() -> dict:
    assert markup_margin(cost=70, price=100) == {
        "profit": D(30), "markup_pct": D("42.86"), "margin_pct": D("30.00")}
    assert markup_margin(markup=25)["margin_pct"] == D("20.00")
    assert markup_margin(margin=20)["markup_pct"] == D("25.00")
    assert price_from(1000, margin=20)["price"] == D(1250)
    assert price_from(1000, markup=5)["price"] == D(1050)
    assert imu(25, 10, 8, 100)["imu_pct"] == D("39.81")
    assert gmroi(450, 300)["gmroi"] == D("1.50")
    assert sell_through(80, 100, 20)["sell_through_pct"] == D("66.67")
    assert turnover(1200, 300) == {"turns": D("4.00"), "days_of_inventory": D("91.25")}
    assert weeks_of_supply(240, 60)["weeks_of_supply"] == D("4.00")
    assert open_to_buy(500, 30, 800, 700, 50)["open_to_buy"] == D(580)
    assert share_of_shelf(18, 60, 25) == {
        "share_of_shelf_pct": D("30.00"), "fair_share_index": D("1.20")}
    assert osa(46, 50) == {"osa_pct": D("92.00"), "oos_pct": D("8.00")}
    assert compliance(17, 20)["compliance_pct"] == D("85.00")
    ps = perfect_store({"osa": (D(92), D(40)), "pog": (D(80), D(30)),
                        "price": (D(100), D(20)), "posm": (D(50), D(10))})
    assert ps["perfect_store_score"] == D("85.80")
    vc = visit_cost(300_000_000, 24, 6, 150_000, 3_500_000)
    assert vc["cost_per_visit"] == D(2_233_333) and vc["margin_pct"] == D("36.19")
    oc = occupancy(1422, 1206, checkouts=6, offices_front=75, gondola_area=100.8,
                   block_area=273.5, gondola_depth=1, aisle=1.8)
    assert oc["sales_share_pct"] == D("84.81") and oc["sales_m2_per_checkout"] == D(201)
    assert oc["center_block_density_pct"] == D("36.86") and oc["ref_center_density_pct"] == "35.71-40.00"
    assert oc["aisle_within_std"] is True
    return {"selftest": "ok"}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Merchandising KPI calculator")
    p.add_argument("--json", action="store_true", help="print JSON instead of key: value")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("markup-margin", help="convert markup ↔ margin")
    s.add_argument("--cost"); s.add_argument("--price")
    s.add_argument("--markup"); s.add_argument("--margin")

    s = sub.add_parser("price", help="price for a target markup or margin")
    s.add_argument("--cost", required=True)
    s.add_argument("--markup"); s.add_argument("--margin")

    s = sub.add_parser("imu", help="initial markup %")
    for a in ("--expenses", "--profit", "--reductions", "--net-sales"):
        s.add_argument(a, required=True)

    s = sub.add_parser("gmroi"); s.add_argument("--gross-margin", required=True)
    s.add_argument("--avg-inventory-cost", required=True)

    s = sub.add_parser("sell-through"); s.add_argument("--sold", required=True)
    s.add_argument("--beginning", required=True); s.add_argument("--received", default=0)

    s = sub.add_parser("turnover"); s.add_argument("--cogs", required=True)
    s.add_argument("--avg-inventory", required=True); s.add_argument("--days", default=365)

    s = sub.add_parser("wos", help="weeks of supply"); s.add_argument("--on-hand", required=True)
    s.add_argument("--weekly-sales", required=True)

    s = sub.add_parser("otb", help="open-to-buy")
    for a in ("--planned-sales", "--planned-markdowns", "--planned-eom", "--planned-bom"):
        s.add_argument(a, required=True)
    s.add_argument("--on-order", default=0)

    s = sub.add_parser("sos", help="share of shelf")
    s.add_argument("--brand-facings", required=True, help="facings or linear cm")
    s.add_argument("--total-facings", required=True, help="category total, same unit")
    s.add_argument("--market-share", help="brand sales share %% for fair-share index")

    s = sub.add_parser("osa", help="on-shelf availability")
    s.add_argument("--available", required=True); s.add_argument("--checked", required=True)

    s = sub.add_parser("compliance", help="planogram/price/POSM compliance")
    s.add_argument("--passed", required=True); s.add_argument("--audited", required=True)

    s = sub.add_parser("perfect-store", help="weighted composite score")
    s.add_argument("--component", action="append", help="name=score:weight (repeatable)")

    s = sub.add_parser("visit-cost", help="cost per merchandiser visit")
    s.add_argument("--monthly-cost", required=True, help="salary+insurance+overhead per merchandiser")
    s.add_argument("--working-days", required=True)
    s.add_argument("--visits-per-day", required=True)
    s.add_argument("--travel-per-visit", default=0)
    s.add_argument("--price-per-visit")

    s = sub.add_parser("occupancy", help="area-use ratios of a store plan vs reference values")
    s.add_argument("--gross", required=True, help="total store area m²")
    s.add_argument("--sales", required=True, help="customer-accessible selling area m²")
    s.add_argument("--checkouts"); s.add_argument("--offices-front", help="office area in the sales/entry zone m²")
    s.add_argument("--gondola-area", help="footprint of centre gondolas m²")
    s.add_argument("--block-area", help="centre block area m² (gondolas + aisles)")
    s.add_argument("--gondola-depth", help="gondola depth m (for reference density)")
    s.add_argument("--aisle", help="typical secondary aisle width m")

    sub.add_parser("selftest")
    return p


def run(args) -> dict:
    c = args.cmd
    if c == "markup-margin":
        return markup_margin(args.cost if args.price else None,
                             args.price if args.cost else None, args.markup, args.margin)
    if c == "price":
        return price_from(args.cost, args.markup, args.margin)
    if c == "imu":
        return imu(args.expenses, args.profit, args.reductions, args.net_sales)
    if c == "gmroi":
        return gmroi(args.gross_margin, args.avg_inventory_cost)
    if c == "sell-through":
        return sell_through(args.sold, args.beginning, args.received)
    if c == "turnover":
        return turnover(args.cogs, args.avg_inventory, args.days)
    if c == "wos":
        return weeks_of_supply(args.on_hand, args.weekly_sales)
    if c == "otb":
        return open_to_buy(args.planned_sales, args.planned_markdowns, args.planned_eom,
                           args.planned_bom, args.on_order)
    if c == "sos":
        return share_of_shelf(args.brand_facings, args.total_facings, args.market_share)
    if c == "osa":
        return osa(args.available, args.checked)
    if c == "compliance":
        return compliance(args.passed, args.audited)
    if c == "perfect-store":
        return perfect_store(_parse_components(args.component))
    if c == "visit-cost":
        return visit_cost(args.monthly_cost, args.working_days, args.visits_per_day,
                          args.travel_per_visit, args.price_per_visit)
    if c == "occupancy":
        return occupancy(args.gross, args.sales, args.checkouts, args.offices_front,
                         args.gondola_area, args.block_area, args.gondola_depth, args.aisle)
    if c == "selftest":
        return selftest()
    raise ValueError(f"unknown command {c}")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
    except (ValueError, ArithmeticError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({k: str(v) if isinstance(v, Decimal) else v for k, v in result.items()},
                         ensure_ascii=False, indent=2))
    else:
        for k, v in result.items():
            print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
