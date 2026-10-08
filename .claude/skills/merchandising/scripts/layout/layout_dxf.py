"""Write the category layout into a copy of the client DXF.

  python3 -I layout_dxf.py SPEC.py source.dxf out.dxf

Keeps every original entity; optionally moves fixtures (spec.META["moves"]) and adds layers
DX-GROUP (floor tint + group name), DX-ZONE (category colour), DX-CODE («CODE - name»), DX-FLOW (customer path),
DX-OLD (previous position of moved fixtures) and DX-LEGEND (table below the plan).
"""
import sys, math, os, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ezdxf
from ezdxf.math import Matrix44
from ezdxf import bbox, colors
spec_path, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
_sp = importlib.util.spec_from_file_location("layout_spec", spec_path); M = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(M)
META = M.META
from layout_common import label_fit

doc = ezdxf.readfile(src); msp = doc.modelspace()

# ---- move fixtures (optional): rotate about the old centre, then translate to the new one
ghosts = META.get("ghosts", [])
for mv in META.get("moves", []):
    cx, cy = mv["old_c"]; nx, ny = mv["new_c"]
    T = Matrix44.chain(Matrix44.translate(-cx, -cy, 0), Matrix44.z_rotate(math.radians(mv.get("rot", 0))), Matrix44.translate(nx, ny, 0))
    n = 0
    for e in msp.query("INSERT"):
        if e.dxf.name in mv["blocks"]:
            e.transform(T); n += 1
    if mv.get("text_at"):
        for e in msp.query("TEXT"):
            p = e.dxf.insert
            if abs(p.x - mv["text_at"][0]) < .05 and abs(p.y - mv["text_at"][1]) < .05:
                e.transform(T); n += 1
    assert n, f"nothing moved for {mv}"
    print("moved", n, "entities")

# ---- layers
def layer(name, aci, lt="Continuous", plot=True):
    if name not in doc.layers:
        doc.layers.add(name, color=aci, linetype=lt)
for lt in ("DASHED",):
    if lt not in doc.linetypes:
        doc.linetypes.add(lt, pattern=[0.6, 0.35, -0.25], description="Dashed __ __")
layer("DX-ZONE", 8); layer("DX-CODE", 7); layer("DX-FLOW", 5); layer("DX-OLD", 8, "DASHED"); layer("DX-LEGEND", 7)
if "DX-FA" not in doc.styles:
    doc.styles.add("DX-FA", font="tahoma.ttf")

def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

# old position of moved fixtures (dashed ghost)
for o, gtxt in ghosts:
    msp.add_lwpolyline([(o[0], o[1]), (o[2], o[1]), (o[2], o[3]), (o[0], o[3])], close=True,
                       dxfattribs={"layer": "DX-OLD", "linetype": "DASHED", "ltscale": 0.3})
    msp.add_mtext(gtxt, dxfattribs={"layer": "DX-OLD", "char_height": 0.14, "style": "DX-FA",
                  "insert": ((o[0] + o[2]) / 2, (o[1] + o[3]) / 2), "attachment_point": 5})

# ---- product-group floor tint + names (drawn first, so they sit under the fixtures)
layer("DX-GROUP", 8)
FA_DIG = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
for gid, fam, gfa, gen, polys, (lx, ly), grot, members in M.GROUPS:
    col = rgb(M.FAM[fam][2])
    for poly in polys:
        hh = msp.add_hatch(dxfattribs={"layer": "DX-GROUP"}); hh.paths.add_polyline_path(poly, is_closed=True)
        hh.rgb = col; hh.transparency = 0.82
        msp.add_lwpolyline(poly, close=True, dxfattribs={"layer": "DX-GROUP", "true_color": colors.rgb2int(col), "linetype": "DASHED", "ltscale": 0.3})
    if gfa and META.get("group_floor_labels", True):
        msp.add_mtext(f"گروه کالایی {gid.translate(FA_DIG)}: {gfa}\\P{gen}", dxfattribs={"layer": "DX-GROUP", "char_height": 0.2, "style": "DX-FA",
                      "insert": (lx, ly), "attachment_point": 5, "rotation": grot, "true_color": colors.rgb2int(tuple(int(c * .55) for c in col))})

# ---- category zones + codes
for code, fam, poly, fa, en, fix in M.Z:
    col = rgb(M.FAM[fam][2])
    h = msp.add_hatch(dxfattribs={"layer": "DX-ZONE"})
    h.set_pattern_fill("SOLID") if False else None
    h.paths.add_polyline_path(poly, is_closed=True)
    h.rgb = col; h.transparency = 0.45
    msp.add_lwpolyline(poly, close=True, dxfattribs={"layer": "DX-ZONE", "true_color": colors.rgb2int(col)})
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    cxz, cyz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w, hgt = max(xs) - min(xs), max(ys) - min(ys)
    txt, fsz, vert = label_fit(code, poly, M.SHORT)
    rot = 90 if vert else 0
    msp.add_mtext(txt.replace("\n", "\\P"), dxfattribs={"layer": "DX-CODE", "char_height": fsz * 0.62,
                  "style": "DX-FA", "insert": (cxz, cyz), "attachment_point": 5, "rotation": rot})

# ---- customer path
pl = msp.add_lwpolyline(M.FLOW, dxfattribs={"layer": "DX-FLOW", "const_width": 0.06})
def arrow(p, q, lay="DX-FLOW", size=0.35):
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    a = (q[0] - size * math.cos(ang - .45), q[1] - size * math.sin(ang - .45))
    b = (q[0] - size * math.cos(ang + .45), q[1] - size * math.sin(ang + .45))
    s = msp.add_solid([q, a, b], dxfattribs={"layer": lay})
for i in range(len(M.FLOW) - 1):
    p, q = M.FLOW[i], M.FLOW[i + 1]
    if math.dist(p, q) > 3:
        mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        arrow(p, mid)
arrow(M.FLOW[-2], M.FLOW[-1])
msp.add_lwpolyline(M.SPINE, dxfattribs={"layer": "DX-FLOW", "linetype": "DASHED", "ltscale": 0.4, "const_width": 0.03})
arrow(M.SPINE[0], ((M.SPINE[0][0] + M.SPINE[1][0]) / 2, M.SPINE[0][1]), size=0.28)

# ---- legend below the building (outside the walls)
LG = META["legend"]
lines = []
fam_order = list(M.FAM)
for fam in fam_order:
    for code, f, poly, fa, en, fix in M.Z:
        if f == fam:
            lines.append(f"{code}  {en}  —  {fa}")
cols = LG["cols"]; per = math.ceil(len(lines) / cols)
x0, y0 = LG["x"], LG["y"]
msp.add_mtext(f"DaranX — {META['name']} category plan (proposal) · طرح چیدمان دسته‌کالا — پیشنهاد داران‌ایکس",
              dxfattribs={"layer": "DX-LEGEND", "char_height": 0.26, "style": "DX-FA", "insert": (x0, y0 + 0.5 + 0.4 * (math.ceil(len(fam_order) / LG["chips_per_row"]) - 1))})
for c in range(cols):
    chunk = lines[c * per:(c + 1) * per]
    msp.add_mtext("\\P".join(chunk), dxfattribs={"layer": "DX-LEGEND", "char_height": 0.13, "style": "DX-FA",
                  "insert": (x0 + c * LG["dx"], y0), "width": LG["w"], "line_spacing_factor": 1.0})
for i, fam in enumerate(fam_order):
    fx = x0 + (i % LG["chips_per_row"]) * LG["chip_dx"]; fy = y0 + 0.95 + 0.4 * (i // LG["chips_per_row"])
    fa, en, light, _ = M.FAM[fam]
    hh = msp.add_hatch(dxfattribs={"layer": "DX-LEGEND"}); hh.paths.add_polyline_path(
        [(fx, fy), (fx + .35, fy), (fx + .35, fy + .25), (fx, fy + .25)], is_closed=True)
    hh.rgb = rgb(light); hh.transparency = 0.45
    msp.add_mtext(f"{en} · {fa}", dxfattribs={"layer": "DX-LEGEND", "char_height": 0.125, "style": "DX-FA", "insert": (fx + .45, fy + .22)})
doc.saveas(out)
print("saved", out, "zones", len(M.Z))
