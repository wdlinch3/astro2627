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

