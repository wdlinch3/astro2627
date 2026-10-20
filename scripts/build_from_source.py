#!/usr/bin/env python3
"""Build the Director-ready AA static site from an exact website commit."""

from __future__ import annotations

import argparse
import json
import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_TOP_LEVEL = (
    "teaching",
    "index.html",
    "aa@tj.pdf",
    "ss_emphasis.pdf",
    "u_emphasis.pdf",
    "packets",
    "assignments",
    "ss",
    "u",
    "vlo",
    "x",
    "assets",
    "tj",
    "aatj",
    "SOURCE_COMMIT",
    "DEPLOYMENT.json",
)
TEXT_SUFFIXES = {".html", ".css", ".js", ".xml", ".txt"}


def run(command: list[str], *, cwd: Path, capture: bool = False) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def resolve_bundle(explicit: str | None) -> str:
    if explicit:
        return explicit
    preferred = Path.home() / ".rubies/ruby-3.3.4/bin/bundle"
    if preferred.is_file():
        return str(preferred)
    discovered = shutil.which("bundle")
    if not discovered:
        raise SystemExit("Bundler was not found; pass --bundle /path/to/bundle")
    return discovered


def rewrite_urls(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        original = text

        # Preserve links that originally meant the personal-site root before
        # turning the AA subtree into the deployment root.
        text = re.sub(
            r"href=([\"'])/\1",
            lambda match: f"href={match.group(1)}https://wdlinch3.github.io/{match.group(1)}",
            text,
        )
        text = text.replace('href="/teaching/"', 'href="https://wdlinch3.github.io/teaching/"')
        text = text.replace("href='/teaching/'", "href='https://wdlinch3.github.io/teaching/'")
        text = re.sub(r"((?:href|src|action)=[\"'])/aa/", r"\1/", text)

        if text != original:
            path.write_text(text, encoding="utf-8")


def style_minicourse(text: str, pdf: str, catalog_url: str) -> str:
    """Use the existing source-owned AA packet theme without changing lesson content."""
    text = text.replace('</head>', '<link rel="stylesheet" href="/assets/css/aa_packet_theme.css">\n</head>', 1)
    navigation = ('<nav class="packet-nav" aria-label="Packet navigation">'
                  '<a href="/">Advanced Astronomy</a>'
                  f'<a href="{html.escape(catalog_url, quote=True)}">Minicourses</a>'
                  f'<a href="/{html.escape(pdf, quote=True)}">PDF</a>'
                  '<span>Minicourse</span></nav>')
    text, count = re.subn(r'<nav class="minicourse-site-nav"[^>]*>.*?</nav>', navigation, text, flags=re.S)
    if count == 0:
        text, main_count = re.subn(r'(<main\b[^>]*>)', lambda match: match.group(1) + navigation, text, count=1)
        if main_count != 1:
            raise SystemExit("Expected a reading main element")
        text = text.replace('</main>', navigation + '</main>', 1)
    elif count != 2:
        raise SystemExit("Expected top and bottom minicourse navigation")
    return text


def add_minicourses(built: Path, stage: Path, catalog_url: str) -> None:
    """Mirror only allowlisted current public readings, PDFs and runtime assets."""
    manifest = json.loads((REPO_ROOT / "scripts/minicourses.json").read_text())
    for relative in manifest["files"]:
        source = built / relative
        if not source.is_file():
            raise SystemExit(f"Missing minicourse artifact: {relative}")
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    pdfs = {}
    source_catalog = (built / "teaching/minicourses/index.html").read_text()
    sections = re.findall(r'<section class="section-card" id="[^"]+">(.*?)</section>', source_catalog, re.S)
    if len(sections) != 8:
        raise SystemExit("Minicourse catalog changed; review the deployment allowlist")
    for section in sections:
        links = re.findall(r'href="([^"]+)"', section)
        reading = next(link for link in links if link.endswith('.html')).lstrip('/')
        pdf = next(link for link in links if link.endswith('.pdf')).lstrip('/')
        if not {reading, pdf}.issubset(manifest["files"]):
            raise SystemExit("Catalog reading/PDF missing from deployment allowlist")
        pdfs[reading] = pdf
    catalog = stage / "teaching/minicourses/index.html"
    destination = html.escape(catalog_url, quote=True)
    catalog.write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={destination}"><title>Minicourses</title></head><body><p><a href="{destination}">Open the Minicourses catalog</a></p></body></html>\n', encoding="utf-8")
    for page in (stage / "teaching/minicourses").rglob("*.html"):
        text = page.read_text()
        # Generated navigation adaptation only; student prose and mathematics stay intact.
        text = text.replace('href="/teaching/"', 'href="/"')
        text = text.replace('href="https://wdlinch3.github.io/teaching/minicourses/', 'href="/teaching/minicourses/')
        relative = page.relative_to(stage).as_posix()
        if relative in pdfs:
            text = style_minicourse(text, pdfs[relative], catalog_url)
        page.write_text(text)
    # Quarto/vendor output includes trailing whitespace; normalize generated text.
    for asset in (stage / "teaching/minicourses").rglob("*"):
        if asset.is_file() and asset.suffix in TEXT_SUFFIXES:
            asset.write_text('\n'.join(line.rstrip() for line in asset.read_text().splitlines()).rstrip() + '\n')


def replace_generated_tree(stage: Path) -> None:
    for name in GENERATED_TOP_LEVEL:
        destination = REPO_ROOT / name
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        elif destination.exists() or destination.is_symlink():
            destination.unlink()

    for child in stage.iterdir():
        destination = REPO_ROOT / child.name
        if child.is_dir():
            shutil.copytree(child, destination)
        else:
            shutil.copy2(child, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--bundle")
    parser.add_argument("--catalog-url", default="https://activities.tjhsst.edu/astro/minicourses/", help="Catalog destination; use localhost only for a local preview")
    args = parser.parse_args()

    source = args.source.resolve()
    if not (source / ".git").exists():
        raise SystemExit(f"not a Git checkout: {source}")

    status = run(["git", "status", "--porcelain"], cwd=source, capture=True)
    if status:
        raise SystemExit("source checkout has uncommitted changes")

    commit = run(
        ["git", "rev-parse", "--verify", f"{args.ref}^{{commit}}"],
        cwd=source,
        capture=True,
    )
    bundle = resolve_bundle(args.bundle)

    with tempfile.TemporaryDirectory(prefix="astro2627-build-") as temp_name:
        temp = Path(temp_name)
        archived_source = temp / "source"
        built = temp / "built"
        stage = temp / "stage"
        archived_source.mkdir()
        built.mkdir()
        stage.mkdir()

        archive = subprocess.Popen(
            ["git", "archive", "--format=tar", commit],
            cwd=source,
            stdout=subprocess.PIPE,
        )
        assert archive.stdout is not None
        extract = subprocess.run(
            ["tar", "-xf", "-", "-C", str(archived_source)],
            stdin=archive.stdout,
            check=True,
        )
        archive.stdout.close()
        if archive.wait() != 0 or extract.returncode != 0:
            raise SystemExit("could not archive the selected source commit")

        run(
            [bundle, "exec", "jekyll", "build", "--destination", str(built)],
            cwd=archived_source,
        )

        shutil.copytree(built / "aa", stage, dirs_exist_ok=True)
        for shared in ("assets", "tj", "aatj"):
            shutil.copytree(built / shared, stage / shared)

        rewrite_urls(stage)
        add_minicourses(built, stage, args.catalog_url)
        (stage / "SOURCE_COMMIT").write_text(f"{commit}\n", encoding="utf-8")
        metadata = {
            "source_commit": commit,
            "minicourses": "scripts/minicourses.json",
            "minicourse_catalog_url": args.catalog_url,
            "local_preview": args.catalog_url.startswith("http://127.0.0.1:"),
            "source_repository": "https://github.com/wdlinch3/wdlinch3.github.io",
        }
        (stage / "DEPLOYMENT.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        replace_generated_tree(stage)

    run(["python3", "scripts/check_site.py"], cwd=REPO_ROOT)
    print(f"built Director site from {commit}")


if __name__ == "__main__":
    main()
