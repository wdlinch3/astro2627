#!/usr/bin/env python3
"""Verify mirror fidelity against the exact recorded source commit."""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True, type=Path)
args = parser.parse_args()
commit = (ROOT / 'SOURCE_COMMIT').read_text().strip()
catalog_url = json.loads((ROOT / 'DEPLOYMENT.json').read_text())['minicourse_catalog_url']
manifest = json.loads((ROOT / 'scripts/minicourses.json').read_text())
def normalized(text):
    return '\n'.join(line.rstrip() for line in text.splitlines()).rstrip() + '\n'

html_count = pdf_count = 0
for name in manifest['files']:
    original = subprocess.check_output(['git', 'show', f'{commit}:{name}'], cwd=args.source)
    actual = (ROOT / name).read_bytes()
    if name.endswith('.html'):
        expected = original.decode().replace('href="/teaching/"', 'href="/"').replace('href="https://wdlinch3.github.io/teaching/minicourses/', 'href="/teaching/minicourses/')
        # Strip only the intended presentation layer before exact content comparison.
        restored = actual.decode().replace('<link rel="stylesheet" href="/assets/css/aa_packet_theme.css">\n', '')
        original_navs = re.findall(r'<nav class="minicourse-site-nav"[^>]*>.*?</nav>', expected, re.S)
        replacements = iter(original_navs)
        restored = re.sub(r'<nav class="packet-nav"[^>]*>.*?</nav>', lambda match: next(replacements) if original_navs else '', restored, flags=re.S)
        assert normalized(restored) == normalized(expected), f'Unexpected lesson change: {name}'
        assert actual.decode().count('href="/assets/css/aa_packet_theme.css"') == 1
        assert actual.decode().count('class="packet-nav"') == 2
        assert actual.decode().count(f'href="{catalog_url}"') == 2
        assert 'href="/teaching/minicourses/"' not in actual.decode()
        assert 'https://wdlinch3.github.io' not in actual.decode(), name
        html_count += 1
    else:
        if Path(name).suffix in {'.css', '.js', '.xml', '.txt'}:
            assert actual.decode() == normalized(original.decode()), name
        else:
            assert actual == original, f'Artifact changed: {name}'
        pdf_count += name.endswith('.pdf')
assert html_count == 8 and pdf_count == 9
assert not list((ROOT / 'teaching').rglob('*.ipynb'))
assert not list((ROOT / 'teaching').rglob('*.qmd'))
print(f'Mirror fidelity passed: {html_count} readings, {pdf_count} PDFs, {len(manifest["files"])} allowlisted files; only navigation and shared theme changed.')
