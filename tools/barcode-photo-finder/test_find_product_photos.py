"""Offline tests: the store sites are mocked, no network needed.  run: pytest -q"""
import io
import json

import pytest
from openpyxl import Workbook, load_workbook
from PIL import Image

import find_product_photos as fp


def _png(color=(200, 30, 30)):
    b = io.BytesIO()
    Image.new("RGB", (400, 400), color).save(b, "JPEG", quality=95)
    data = b.getvalue()
    return data + b"\0" * max(0, 3500 - len(data))  # make it look like a real file size


class FakeResp:
    def __init__(self, url, status=200, text="", content=b"", ctype="text/html", js=None):
        self.url, self.status_code, self.text, self.content = url, status, text, content
        self.headers = {"content-type": ctype}
        self._js = js

    def json(self):
        if self._js is None:
            raise ValueError
        return self._js


ROUTES = {}


def fake_get(self, url, **kw):
    for prefix, resp in ROUTES.items():
        if url.startswith(prefix):
            if isinstance(resp, Exception):
                raise resp
            return resp(url) if callable(resp) else resp
    return FakeResp(url, status=404)


@pytest.fixture(autouse=True)
def mock_http(monkeypatch):
    ROUTES.clear()
    monkeypatch.setattr(fp.Http, "get", fake_get)


def test_text_helpers():
    assert fp.ean_ok("6260257500799")
    assert not fp.ean_ok("6260257500798")
    assert fp.clean_barcode(6260257500799.0) == "6260257500799"
    assert fp.clean_barcode("۶۲۶۰۲۵۷۵۰۰۷۹۹") == "6260257500799"
    assert fp.sizes("بیفتک ۴۸۰ گرم ب آ") == {"w": {480.0}}
    assert fp.sizes("هوفنبرگ سودا 1لیتر") == {"v": {1000.0}}
    assert fp.size_match("فیله مرغ ۱ کیلویی", "فیله مرغ 1000 گرمی") is True
    assert fp.size_match("پنیر ۴۰۰ گرم", "پنیر 250 گرم") is False
    assert fp.name_score("سبزی قلیه ۴۰۰ گرم نوبر سبز", "سبزی قلیه منجمد نوبر سبز 400 گرم") == 1.0


def test_daychi_exact_barcode(tmp_path):
    code = "6260257500799"
    page = (f'<meta property="og:title" content="سبزی قلیه 400 گرمی نوبر سبز">'
            f'<img src="https://www.daychi.com/storage/media/x/{code}.jpg">')
    ROUTES[f"https://www.daychi.com/products/{code}"] = FakeResp(f"https://www.daychi.com/products/{code}", text=page)
    ROUTES["https://www.daychi.com/storage/"] = FakeResp("img", content=_png(), ctype="image/jpeg")
    r = fp.lookup(fp.Http(0), code, "سبزی قلیه ۴۰۰ گرم نوبر سبز", ["daychi", "digikala"], set(),
                  str(tmp_path), 0.6, False)
    assert r.status == fp.HIGH and r.source == "daychi" and r.image_file
    assert r.sources_tried == ["daychi"]  # stopped after a high-confidence hit


def test_name_search_rejects_wrong_size_and_blocks(tmp_path):
    ROUTES["https://api.digikala.com/"] = FakeResp("dk", ctype="application/json", js={"data": {"products": [
        {"id": 1, "title_fa": "پنیر چدار آلیما 250 گرم", "images": {"main": {"url": ["https://dk/a.jpg?x"]}}},
        {"id": 2, "title_fa": "پنیر چدار ورقه ای آلیما 400 گرم", "images": {"main": {"url": ["https://dk/b.jpg?x"]}}},
    ]}})
    ROUTES["https://dk/b.jpg"] = FakeResp("img", content=_png(), ctype="image/jpeg")
    ROUTES["https://api.torob.com/"] = fp.SourceBlocked("HTTP 429")
    blocked = set()
    r = fp.lookup(fp.Http(0), "6261307404128", "پنیر چدار ۴۰۰ گرم آلیما", ["torob", "digikala"], blocked,
                  str(tmp_path), 0.6, False)
    assert blocked == {"torob"}
    assert r.source == "digikala" and r.image_url == "https://dk/b.jpg"
    assert r.status in (fp.MEDIUM, fp.LOW)


def test_not_found(tmp_path):
    r = fp.lookup(fp.Http(0), "6260859004275", "بیفتک ۴۸۰ گرم ب آ", list(fp.SOURCES), set(),
                  str(tmp_path), 0.6, False)
    assert r.status == fp.NOT_FOUND and not r.image_file


def test_end_to_end_excel(tmp_path, monkeypatch):
    wb = Workbook()
    ws = wb.active
    ws.append(["شناسهٔ محصول", "نام محصول", "بارکد", "کد کالا", "آدرس عکس اصلی", "نوع نقص"])
    ws.append(["a", "سبزی قلیه ۴۰۰ گرم نوبر سبز", "6260257500799", "6260257500799", None, "بدون عکس اصلی"])
    ws.append(["b", "بیفتک ۴۸۰ گرم ب آ", 6260859004275, "6260859004275", None, "بدون عکس اصلی"])
    inp = tmp_path / "in.xlsx"
    wb.save(inp)
    code = "6260257500799"
    ROUTES[f"https://www.daychi.com/products/{code}"] = FakeResp(
        f"https://www.daychi.com/products/{code}",
        text='<h1>سبزی قلیه نوبر سبز 400 گرم</h1><meta property="og:image" content="https://www.daychi.com/storage/media/1.webp">')
    ROUTES["https://www.daychi.com/storage/"] = FakeResp("img", content=_png(), ctype="image/webp")
    monkeypatch.setattr(fp.time, "sleep", lambda s: None)
    out = tmp_path / "out.xlsx"
    fp.main([str(inp), "-o", str(out), "--delay", "0"])

    wb2 = load_workbook(out)
    ws2 = wb2["محصولات و عکس"]
    assert ws2.sheet_view.rightToLeft
    assert len(ws2._images) == 1
    hdr = [c.value for c in ws2[1]]
    assert hdr[-1] == "تصویر کالا"
    assert ws2.cell(2, hdr.index("اطمینان") + 1).value == fp.HIGH
    assert ws2.cell(2, hdr.index("آدرس عکس اصلی") + 1).value.endswith("1.webp")
    assert ws2.cell(3, hdr.index("بارکد") + 1).value == "6260859004275"  # text, not 6.26E+12
    assert ws2.cell(3, hdr.index("تصویر کالا") + 1).value == "تصویر موجود نیست"
    assert "راهنما" in wb2.sheetnames

    # second run resumes from cache without hitting the network
    ROUTES.clear()
    fp.main([str(inp), "-o", str(out), "--delay", "0"])
    assert len(load_workbook(out)["محصولات و عکس"]._images) == 1
    cache = json.load(open(tmp_path / "out_cache.json", encoding="utf-8"))
    assert len(cache) == 2


def test_auto_input(tmp_path):
    (tmp_path / "products.xlsx").write_bytes(b"x")
    (tmp_path / "products-with-photos.xlsx").write_bytes(b"x")
    (tmp_path / "~$products.xlsx").write_bytes(b"x")
    assert fp.auto_input(str(tmp_path)).endswith("products.xlsx")
    (tmp_path / "other.xlsx").write_bytes(b"x")
    with pytest.raises(SystemExit):
        fp.auto_input(str(tmp_path))
