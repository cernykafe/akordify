#!/usr/bin/env python3
"""Sestavení Akordify.

Zdrojem je složka public/, tedy podoba pro nasazení na web (PWA).
Skript udělá dvě věci:

1. Spočítá otisk obsahu stránky, manifestu a ikon a zapíše ho do VERSION
   v public/sw.js. Service worker podle něj po nasazení pozná novou verzi
   a smaže starou mezipaměť. Ručně se VERSION nemění.

2. Vyrobí dist/akordify.html: samostatný soubor, který jde otevřít
   dvojklikem bez serveru. Odkazy na manifest a ikony nahradí ikonou
   vloženou přímo do stránky a vynechá registraci service workeru.

Použití:
    python3 scripts/build.py           sestaví a zapíše změny
    python3 scripts/build.py --check   jen ověří, že VERSION v sw.js sedí
                                       (vrací 1, když je zastaralá)

Potřebuje jen Python 3.8+, žádné balíčky.
"""

import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
DIST = ROOT / "dist"

# Soubory, které service worker ukládá do mezipaměti (ASSETS v sw.js).
# Na jejich obsahu závisí VERSION.
HASHED = [
    "index.html",
    "manifest.webmanifest",
    "icons/favicon.svg",
    "icons/favicon-32.png",
    "icons/apple-touch-icon.png",
    "icons/icon-192.png",
    "icons/icon-512.png",
    "icons/icon-maskable-512.png",
]

VERSION_RE = re.compile(r"const VERSION = 'akordify-([0-9a-f]+)';")

# Hlavička pro web: manifest, barvy lišty, ikony a nastavení pro instalaci.
PWA_HEAD_RE = re.compile(
    r'<link rel="manifest" href="/manifest\.webmanifest">\n'
    r'(?:<meta name="theme-color"[^\n]*\n)+'
    r'(?:<link rel="(?:icon|apple-touch-icon)"[^\n]*\n)+'
    r'(?:<meta name="(?:apple-mobile-web-app|mobile-web-app)[^\n]*\n)+'
)

SW_REGISTER = (
    "<script>\n"
    "if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {\n"
    "  window.addEventListener('load', function () { navigator.serviceWorker.register('/sw.js').catch(function () {}); });\n"
    "}\n"
    "</script>\n"
)


def content_version() -> str:
    h = hashlib.sha256()
    for name in HASHED:
        data = (PUBLIC / name).read_bytes()
        h.update(name.encode() + b"\0" + len(data).to_bytes(8, "big") + data)
    return h.hexdigest()[:10]


def update_sw(check_only: bool) -> bool:
    """Vrací True, když VERSION v sw.js odpovídá obsahu (případně po zápisu)."""
    sw_path = PUBLIC / "sw.js"
    sw = sw_path.read_text(encoding="utf-8")
    m = VERSION_RE.search(sw)
    if not m:
        sys.exit("V public/sw.js chybí řádek const VERSION = 'akordify-…';")
    want = content_version()
    if m.group(1) == want:
        print(f"sw.js: VERSION akordify-{want} je aktuální")
        return True
    if check_only:
        print(f"sw.js: VERSION akordify-{m.group(1)} je zastaralá, má být akordify-{want}")
        return False
    sw_path.write_text(VERSION_RE.sub(f"const VERSION = 'akordify-{want}';", sw, count=1), encoding="utf-8")
    print(f"sw.js: VERSION akordify-{m.group(1)} → akordify-{want}")
    return True


def build_standalone() -> Path:
    html = (PUBLIC / "index.html").read_text(encoding="utf-8")
    svg = (PUBLIC / "icons/favicon.svg").read_text(encoding="utf-8").strip()
    icon = f'<link rel="icon" href="data:image/svg+xml,{quote(svg, safe="/")}">\n'

    html, n = PWA_HEAD_RE.subn(lambda _: icon, html, count=1)
    if n != 1:
        sys.exit("V index.html se nenašla hlavička pro PWA (manifest, ikony). Upravte PWA_HEAD_RE ve scripts/build.py.")
    if SW_REGISTER not in html:
        sys.exit("V index.html se nenašla registrace service workeru. Upravte SW_REGISTER ve scripts/build.py.")
    html = html.replace(SW_REGISTER, "", 1)

    DIST.mkdir(exist_ok=True)
    out = DIST / "akordify.html"
    out.write_text(html, encoding="utf-8")
    print(f"dist/akordify.html: {out.stat().st_size / 1024:.0f} kB")
    return out


def main() -> None:
    check_only = "--check" in sys.argv[1:]
    ok = update_sw(check_only)
    if check_only:
        sys.exit(0 if ok else 1)
    build_standalone()


if __name__ == "__main__":
    main()
