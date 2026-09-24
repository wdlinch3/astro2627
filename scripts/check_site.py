#!/usr/bin/env python3
"""Validate the flattened Director AA deployment."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "index.html",
    "ss/2026-2027/index.html",
    "ss/2026-2027/celestial-navigation/part-1/index.html",
    "ss/2026-2027/celestial-navigation/part-2/index.html",
    "ss/aristarchus/index.html",
    "ss/kepler1/index.html",
    "assignments/ss_kepler1.zip",
    "x/geometry/index.html",
    "tj/adv_astro/jupyter_instructions/index.html",
    "tj/adv_astro/latex_instructions/index.html",
    "tj/adv_astro/latex_instructions/images/jim-hefferon-latex-math-for-undergrads.pdf",
    "tj/adv_astro/python_instructions/index.html",
    "tj/adv_astro/python_instructions/index_files/libs/quarto-contrib/live-runtime/live-runtime.js",
    "tj/adv_astro/python_instructions/index_files/libs/quarto-contrib/live-runtime/pyodide-worker.js",
    "assets/css/style.css",
    "assets/css/aa.css",
    "assets/css/aa_ss_theme.css",
    "vlo/ss/vlo_aa_ss.pdf",
    "vlo/x/vlo_aa_x.pdf",
    "SOURCE_COMMIT",
    "DEPLOYMENT.json",
)
EXPECTED_CLASS_TEXT = (
    "ION",
    "Astronomy Club",
    "Astronomy Team",
    "Software help",
    "Jupyter",
    "LaTeX",
    "Python",
    "Geometry",
    "Celestial Navigation",
    "Part I reading",
    "Part II reading",
    "Aristarchus",
    "Kepler’s Laws (Part I)",
    "Course textbook: Astronomy 2e",
    "Download textbook (PDF)",
)
CSS_URL = re.compile(r"url\(\s*['\"]?(/[^)'\"]+)")


class Targets(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.targets.append(value)


def resolves(url: str, source: Path) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or url.startswith(("mailto:", "tel:", "//", "#")):
        return True
    raw_path = unquote(parsed.path)
    if not raw_path:
        return True
    candidate = (
        ROOT / raw_path.lstrip("/")
        if raw_path.startswith("/")
        else source.parent / raw_path
    )
    if candidate.is_dir():
        candidate = candidate / "index.html"
    elif not candidate.suffix:
        candidate = candidate / "index.html"
    return candidate.exists()


def main() -> None:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    source_commit = (ROOT / "SOURCE_COMMIT").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        errors.append("SOURCE_COMMIT is not a full Git SHA")

    class_page = ROOT / "ss/2026-2027/index.html"
    if class_page.is_file():
        class_text = class_page.read_text(encoding="utf-8")
        for expected in EXPECTED_CLASS_TEXT:
            if expected not in class_text:
                errors.append(f"class page is missing expected text: {expected}")
        if "{{" in class_text or "{%" in class_text:
            errors.append("class page still contains Liquid source markers")
        if "https://activities.tjhsst.edu/astroteam/" not in class_text:
            errors.append("class page does not contain the live Astro Team link")

    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?:href|src|action)=[\"']/aa/", text):
            errors.append(f"unrewritten /aa/ URL: {path.relative_to(ROOT)}")
        parser = Targets()
        parser.feed(text)
        for target in parser.targets:
            if not resolves(target, path):
                errors.append(f"missing local target in {path.relative_to(ROOT)}: {target}")

    for path in ROOT.rglob("*.css"):
        text = path.read_text(encoding="utf-8")
        for target in CSS_URL.findall(text):
            if not resolves(target, path):
                errors.append(f"missing CSS asset in {path.relative_to(ROOT)}: {target}")

    if errors:
        raise SystemExit("\n".join(errors))
    html_count = sum(1 for _ in ROOT.rglob("*.html"))
    print(f"site checks passed: {html_count} HTML pages; source {source_commit}")


if __name__ == "__main__":
    main()
