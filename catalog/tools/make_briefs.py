"""Generate docs/games/*.md briefs for roadmap games. Run from the repo root: python3 catalog/tools/make_briefs.py"""
import json, os, glob
g = [x for x in json.load(open("catalog/games.json")) if x.get("roadmap")]
g.sort(key=lambda x: x["roadmap"])
d = {}
for f in sorted(glob.glob("catalog/desc_*.json")): d.update(json.load(open(f)))
ex = {}
for f in sorted(glob.glob("research/existing_*.json")): ex.update(json.load(open(f)))
maps = json.load(open("catalog/map_compat.json"))
EF = ['', 'weekend', 'small', 'medium', 'large', 'very large']
LV = ['?', 'retro-faithful', 'enhanced 2D', 'modern/premium']
for f in glob.glob("docs/games/[0-9]*.md"): os.remove(f)
idx = ["# Game briefs\n", "In build order ([../roadmap.md](../roadmap.md)). Descriptions were drafted from memory and not verified; check numbers against the originals running in an emulator.\n"]
for x in g:
    gid, n = x["id"], x["roadmap"]; dd = d.get(gid, {}); e = ex.get(gid, {})
    L = [f"# {n}. {x['name']} ({x['year']})\n",
         f"*Original: {x['dev']} · {x['platform']} · {x['genre']}. Remake effort: {EF[x['complexity']]}. Free-version gap: **{e.get('gap','?')}**.*\n",
         "The final title must be an original name (see [../legal.md](../legal.md)).\n",
         f"## Core loop\n\n{x['loop']}\n",
         f"## Gameplay\n\n{dd.get('gameplay','')}\n",
         f"## Levels\n\n{dd.get('levels','')}\n",
         f"## The challenge\n\n{dd.get('challenge','')}\n",
         f"## What makes it unique\n\n{dd.get('unique','')}\n",
         f"## Remake angle\n\n{x['pitch']}\n\n{dd.get('remake_hooks','')}\n",
         f"## Map compatibility\n\n{maps.get(gid,'')}\n",
         f"## Existing free versions\n\n{e.get('gap_note','')}\n"]
    for p in e.get("projects", []):
        L.append(f"- **{p['name']}** — {p.get('url','')} — {p.get('licence')} · {p.get('kind')} · look: {LV[p.get('visual_level') or 0]} · last activity {p.get('last_activity')} · original levels: {p.get('ships_original_levels')} · custom levels: {p.get('custom_levels')}. {p.get('note','')}")
    L.append(f"\nOfficial or commercial versions: {e.get('official_modern', x.get('modern',''))}\n")
    open(f"docs/games/{n:02d}-{gid}.md", "w").write("\n".join(L))
    idx.append(f"{n}. [{x['name']}]({n:02d}-{gid}.md): {x['year']}, effort {EF[x['complexity']]}, gap {e.get('gap')}")
open("docs/games/README.md", "w").write("\n".join(idx) + "\n")
print("wrote", len(g), "briefs")
