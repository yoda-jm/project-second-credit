import json, urllib.request, urllib.parse, re, sys, time
UA = {"User-Agent": "renovated-games-catalog/0.1 (research)"}
def api(host="en.wikipedia.org", **p):
    p.update(format="json")
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(p)
    for i in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
            time.sleep(1.0); return r
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(5*(i+1)); continue
            raise
games = [x for x in json.load(open("games.json")) if x.get("source")!="claude" or x["id"] in ("bomberman","rickdangerous","speedball2","bubblebobble","cannonfodder")]
old = json.load(open("candidates.json"))
out = {}
bad = r"(logo|icon|cover|box|flag|symbol|commons|wiki|edit|star|question|portal|ambox|padlock|cabinet|flyer|marquee|poster|photo|geograph|advert|diskette|boingball|art of video|carrers|handheld|\.svg)"
for g in games:
    langs = {}
    for host in ["en.wikipedia.org","fr.wikipedia.org","de.wikipedia.org","it.wikipedia.org"]:
        d = api(host, action="query", titles=g["wiki"], prop="images", imlimit="max", redirects=1)
        page = next(iter(d["query"]["pages"].values()))
        c = [i["title"] for i in page.get("images", []) if re.search(r"\.(png|gif|jpe?g)$", i["title"], re.I) and not re.search(bad, i["title"], re.I)]
        langs[host]=c
        if c and host!="en.wikipedia.org": break
    if not any(langs.values()):
        d = api("commons.wikimedia.org", action="query", list="search", srsearch=g["name"]+" screenshot", srnamespace=6, srlimit=8)
        langs["commons"] = [s["title"] for s in d["query"]["search"]]
    print(g["id"], "->", langs, file=sys.stderr, flush=True)
    out[g["id"]] = langs
old.update(out); json.dump(old, open("candidates.json","w"), indent=1)
