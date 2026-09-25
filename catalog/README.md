# Candidate catalog

Source for a single-page catalog of 49 games considered for remakes, with screenshots, gameplay notes, build
order and the survey of existing free versions.

- `games.json`: core data (year, platform, loop, pitch, effort 1–5, `roadmap` position, `adds` to the stack)
- `desc_*.json`: gameplay / levels / challenge / unique / remake_hooks per game (drafted from memory, unverified)
- `map_compat.json`: map compatibility notes for the roadmap games
- `shots_meta.json`: screenshot source pages (Wikipedia / Wikimedia)
- `template.html` + `build.py`: `python3 build.py` embeds everything into `index.html`
- `tools/`: one-off scripts used to fetch screenshots from Wikipedia, and `make_briefs.py` for `docs/games/`

`shots/` and `index.html` are **git-ignored**. The screenshots are fair-use captures of the original games, kept
for private reference only. On a fresh clone, re-fetch them with the scripts in `tools/` (run from `catalog/`),
or build without them (cards show "NO SIGNAL").
