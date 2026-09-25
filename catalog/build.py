import json, base64, os, glob
games = json.load(open("games.json"))
desc = {}
for f in sorted(glob.glob("desc_*.json")): desc.update(json.load(open(f)))
meta = json.load(open("shots_meta.json"))
# pick order: your picks in the order you named them
for g in games:
    g["desc"] = desc.get(g["id"], {})
    if g["id"] == "bomberman": g.setdefault("desc",{})
ex = {}
for k in "ABC":
    if os.path.exists(f"../research/existing_{k}.json"): ex.update(json.load(open(f"../research/existing_{k}.json")))
for g in games:
    if g["id"] in ex: g["existing"] = ex[g["id"]]
games.sort(key=lambda g: g.get("roadmap", 99))
def uri(gid):
    return "data:image/webp;base64," + base64.b64encode(open(f"shots/{gid}.webp","rb").read()).decode()
tags = {"z":"Box art · no gameplay capture yet","alleycat":"IBM PC · the alley","alleycat_a8":"Atari 8-bit · a window room",
        "bomberman":"Bomberman (PC Engine, 1990) — Dyna Blaster in Europe","pipemania":"Commodore 64 port","micromachines":"Game Boy port",
        "qbert":"Arcade","xcom":"Battlescape","speedball2":"Amiga","tetris":"The 1984 original","fruityfrank":"Box art · no gameplay capture yet","wintergames":"C64 · ski jump"}
shots = {}
for key in meta:
    gid = key.split("_")[0]
    if not os.path.exists(f"shots/{key}.webp"): continue
    shots.setdefault(gid, []).append({"src": uri(key), "source": meta[key]["source"], "tag": tags.get(key, "")})
tpl = open("template.html").read()
safe = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
open("index.html","w").write(tpl.replace("__GAMES__", safe(games)).replace("__SHOTS__", safe(shots)))
print("games", len(games), "with shots", len(shots), "size", os.path.getsize("index.html")//1024, "KB")
