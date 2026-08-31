# astro2627 deployment instructions

This repository contains a generated static deployment of the Advanced
Astronomy section of `wdlinch3/wdlinch3.github.io`.

- Treat `wdlinch3.github.io` as the content and presentation source of truth.
- Treat this repository as the Director-ready delivery artifact.
- Never edit generated HTML, CSS, PDFs, notebooks, or copied assets by hand.
- Rebuild with `scripts/build_from_source.py` from an exact clean source commit.
- Require `scripts/check_site.py` and `git diff --check` before committing.
- Keep the deployable site at repository root so Director can update with
  `cd public && git pull --ff-only`.
- Preserve public routes unless a redirect or compatibility plan is explicit.
- Report source commit, deployment commit, push, Director pull, and anonymous
  live verification as separate lifecycle states.

