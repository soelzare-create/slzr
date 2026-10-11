#!/usr/bin/env python3
"""Inline local <link rel=stylesheet> and <script src> files into one self-contained HTML.
Usage: python3 inline.py path/to/page.html out/index.html
Images and fonts stay as files (keep an assets/ folder next to the output)."""
import re, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
html = src.read_text(encoding="utf-8")
base = src.parent

def css(m):
    p = base / m.group(1)
    return f"<style>\n{p.read_text(encoding='utf-8')}\n</style>" if p.exists() else m.group(0)

def js(m):
    p = base / m.group(1)
    return f"<script>\n{p.read_text(encoding='utf-8')}\n</script>" if p.exists() else m.group(0)

html = re.sub(r'<link rel="stylesheet" href="(?!https?:)([^"]+)">', css, html)
html = re.sub(r'<script src="(?!https?:)([^"]+)"></script>', js, html)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
left = re.findall(r'\{\{[^}]+\}\}', html)
print(f"wrote {out} ({len(html)//1024} KB); unfilled placeholders: {len(left)}")
