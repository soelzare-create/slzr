#!/usr/bin/env python3
"""Read a store floor plan (DXF) before designing a category layout.

  dxf_tools.py inspect  plan.dxf                    units, layers, block counts, extents
  dxf_tools.py inserts  plan.dxf [--near x,y,r]     every fixture insert with its real bbox (metres)
  dxf_tools.py grid     plan.dxf out.png x0 y0 x1 y1 px_per_m   crop render with a 1 m red grid (to read coordinates)
  dxf_tools.py base     plan.dxf out.png x0 y0 x1 y1 px_per_m   transparent black-line base for the report (no text/dims/DX-* layers)

Run with:  python3 -I dxf_tools.py ...   (needs: pip install ezdxf matplotlib pillow)
Notes (hard-won):
 * Old Persian labels are SHX-encoded and render as garbage; do not try to read them. Identify fixtures by block name
   (BSS/BSSD = wall/end-cap shelf, BDS = gondola body, BRV/BRD/BF = refrigeration, ch = cash counter), size and position.
 * Insert points can be far from the drawing (nested blocks); always use the bbox, not insert.
 * Stray entities can stretch EXTMAX to thousands of metres: crop to the building.
 * Arrow-shaped black bars near the doors are entry/exit signs; the entrance arrow points into the store.
"""
import sys, collections


def _ezdxf():
    import ezdxf
    from ezdxf import bbox
    return ezdxf, bbox


def inspect(path):
    ezdxf, bbox = _ezdxf()
    doc = ezdxf.readfile(path); msp = doc.modelspace()
    h = doc.header
    print("INSUNITS", h.get("$INSUNITS"), "(1=inch? 4=mm 6=m; check scale against a gondola ~1.0 x 4.0 m)")
    print("entities", dict(collections.Counter(e.dxftype() for e in msp)))
    for (l, t), n in sorted(collections.Counter((e.dxf.layer, e.dxftype()) for e in msp).items()):
        print(f"  {l!r:30} {t:12} {n}")
    print("INSERT blocks:", collections.Counter(e.dxf.name for e in msp.query("INSERT")).most_common(40))
    ext = bbox.extents(msp)
    print("extents", ext.extmin, ext.extmax)


def inserts(path, near=None):
    ezdxf, bbox = _ezdxf()
    doc = ezdxf.readfile(path); msp = doc.modelspace()
    for e in msp.query("INSERT"):
        b = bbox.extents([e])
        if not b.has_data or b.extmin.x != b.extmin.x or abs(b.extmin.x) == float("inf"):
            continue
        cx, cy = (b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2
        if near and ((cx - near[0]) ** 2 + (cy - near[1]) ** 2) ** .5 > near[2]:
            continue
        print(f"{e.dxf.name:22} L={e.dxf.layer:12} rot={e.dxf.rotation:6.1f} bbox=({b.extmin.x:7.2f},{b.extmin.y:7.2f})-({b.extmax.x:7.2f},{b.extmax.y:7.2f}) size={b.size.x:5.2f}x{b.size.y:5.2f}")


def render(path, out, x0, y0, x1, y1, ppm, grid=True, base=False):
    ezdxf, _ = _ezdxf()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
    doc = ezdxf.readfile(path); msp = doc.modelspace()
    if base:
        drop = ("TEXT", "MTEXT", "DIMENSION", "ATTRIB")
        for e in list(msp):
            if e.dxf.layer.startswith("DX-") or e.dxftype() in drop:
                msp.delete_entity(e)
        for blk in doc.blocks:
            for e in list(blk):
                if e.dxftype() in drop:
                    blk.delete_entity(e)
    fig = plt.figure(figsize=((x1 - x0) * ppm / 100, (y1 - y0) * ppm / 100)); ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.OFF if base else BackgroundPolicy.WHITE,
                        color_policy=ColorPolicy.BLACK, min_lineweight=0.12 if base else 0.2)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp, finalize=False)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
    if grid:
        for gx in range(int(x0), int(x1) + 1):
            ax.axvline(gx, color=(1, 0, 0, .18), lw=.5); ax.text(gx + .05, y0 + .1, str(gx), color="red", fontsize=6)
        for gy in range(int(y0), int(y1) + 1):
            ax.axhline(gy, color=(1, 0, 0, .18), lw=.5); ax.text(x0 + .05, gy + .05, str(gy), color="red", fontsize=6)
    fig.savefig(out, dpi=100, transparent=base)
    if base:  # keep only an alpha mask (black lines) so the page can recolour it for dark mode
        from PIL import Image
        im = Image.open(out); g = Image.new("L", im.size, 0)
        Image.merge("LA", (g, im.getchannel("A"))).save(out, optimize=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("inspect", "inserts", "grid", "base"):
        sys.exit(__doc__)
    if a[0] == "inspect": inspect(a[1])
    elif a[0] == "inserts":
        near = tuple(map(float, a[a.index("--near") + 1].split(","))) if "--near" in a else None
        inserts(a[1], near)
    else:
        x0, y0, x1, y1, ppm = map(float, a[3:8])
        render(a[1], a[2], x0, y0, x1, y1, ppm, grid=(a[0] == "grid"), base=(a[0] == "base"))
