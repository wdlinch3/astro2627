# Advanced Astronomy Director deployment

This repository is the static deployment checkout for
<https://astro2627.sites.tjhsst.edu/>. Its `main` branch is ready to serve from
Director's `public` directory.

The course website source remains in
[`wdlinch3/wdlinch3.github.io`](https://github.com/wdlinch3/wdlinch3.github.io).
The file `SOURCE_COMMIT` records the exact source revision used for each build.

## Build

From a clean local clone of the source repository:

```sh
python3 scripts/build_from_source.py \
  --source ../wdlinch3-aa-main \
  --ref main
python3 scripts/check_site.py
```

The builder archives the exact Git commit, runs the source repository's locked
Jekyll build, extracts the Advanced Astronomy site to this repository's root,
copies its required shared assets, and rewrites `/aa/` URLs for the Director
host. It refuses a source ref with uncommitted changes because `SOURCE_COMMIT`
must describe the content exactly.

The generated website files are deployment output. Do not hand-edit them;
change the authoritative source and rebuild.

## Publish and deploy

After reviewing the generated diff and checks:

```sh
git add -A
git commit -m "Build from wdlinch3.github.io <source-sha>"
git push origin main
```

The routine Director update is then:

```sh
cd public
git pull --ff-only
```

Changing Director from Tiger's emergency snapshot repository to this one is a
one-time checkout replacement because the two repositories have unrelated Git
histories.


## Minicourse school-host mirror

The builder also includes the current public student readings under
`/teaching/minicourses/`. `scripts/minicourses.json` is an explicit delivery
allowlist of HTML, PDF, and runtime support assets; it contains no instructor
sources or notebooks. Reading and PDF associations are derived from the same exact source commit.
The catalog itself is maintained only on the Astro Lab site.

The mirror preserves current published student content and uses the source-owned
`assets/css/aa_packet_theme.css`, also used by the AA:SS readings. Generated
packet navigation points back to this host and includes a PDF link. It is separate from the Astro
Lab reader redesign and does not resolve the remaining author-review holds.
Existing MathJax/polyfill CDN references remain; no runtime assets are fetched
from GitHub Pages. Student-network access must be checked after deployment.

After building, also run:

```sh
python3 scripts/test_minicourses.py --source ../wdlinch3.github.io
```

For the initial mirror, publish this deployment before switching the Astro Lab
catalog links to the new school-host URLs. The local preview alone does not
make those URLs live.

The single minicourse catalog is the Astro Lab catalog. Reading navigation and
an automatic redirect at the former school-host catalog URL point there.
Production builds default to `https://activities.tjhsst.edu/astro/minicourses/`.
For the paired local previews, build with
`--catalog-url http://127.0.0.1:8766/astro/minicourses/`.
This sets `local_preview: true` in DEPLOYMENT.json. Rebuild without this override
before publication; never deploy output containing localhost navigation.
