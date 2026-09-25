import json, urllib.request, urllib.parse, time, os, sys
UA = {"User-Agent": "renovated-games-catalog/0.1 (personal research)"}
pick = {
 "pacman":("en","File:Pac-Man gameplay (1x pixel-perfect recreation).png"),
 "boulderdash":("de","Datei:Boulder Dash 1984, Level 1.gif"),
 "cannonfodder":("en","File:Cannon Fodder Amiga Power.jpg"),
 "qix":("en","File:Qixingame.png"),
 "alleycat":("en","File:Alleycat.png"),
 "lemmings":("en","File:Amiga Lemmings.png"),
 "arkanoid":("en","File:Arkanoid.png"),
 "frogger":("en","File:Frogger game arcade.png"),
 "digdug":("en","File:Digdug.png"),
 "pengo":("en","File:ARC Pengo (Act 2).png"),
 "rickdangerous":("it","File:Rick Dangerous.png"),
 "loderunner":("en","File:Lode Runner enemies.gif"),
 "sokoban":("en","File:Sokoban (PC-8801) level 1 screenshot.png"),
 "chuckieegg":("en","File:Chuckie Egg on BBC Micro.jpg"),
 "manicminer":("en","File:Manic Miner Screenshot.png"),
 "marblemadness":("en","File:Marblemadnessscreenshot.png"),
 "supersprint":("en","File:ARC Super Sprint.png"),
 "gauntlet":("en","File:ARC Gauntlet.png"),
 "paperboy":("en","File:ARC Paperboy.png"),
 "xenon2":("en","File:Xenon II Megablast in-game screenshot (Atari ST).png"),
 "speedball2":("it","File:Speedball 2.png"),
 "pipemania":("en","File:Pipedream.png"),
 "qbert":("en","File:Qbert.png"),
 "bombjack":("en","File:Bombjack Screenshot.png"),
 "headoverheels":("en","File:Head over heels amstrad 1.png"),
 "worms":("en","File:Worms scrapyardscreenshot.png"),
 "tetris":("en","File:Tetris-VeryFirstVersion.png"),
 "z":("en","File:Z The Bitmap Brothers.PNG"),
 "rampart":("en","File:Rampart screenshot.png"),
 "chaosengine":("en","File:ChaosEngine1 s11.png"),
 "syndicate":("en","File:Syndicate screenshot.png"),
 "xcom":("en","File:Xcom2.png"),
 "themehospital":("en","File:ThemeHospital.gif"),
 "pang":("en","File:Buster Bros. Screenshot.png"),
 "spyvsspy":("en","File:Spy vs Spy A800 ingame.png"),
 "archon":("en","File:C64 Archon.png"),
 "mule":("en","File:M.U.L.E. Atari 8-bit PAL screenshot.png"),
 "rodland":("en","File:ARC Rod Land (Yōsei Monogatari Rod Land).png"),
 "lostvikings":("en","File:TheLostVikings.png"),
 "superfrog":("it","File:Superfrog Amiga.jpg"),
 "scorchedearth":("en","File:Scorched Earth gameplay.png"),
 "micromachines":("en","File:GB Micro Machines.png"),
}
meta = {}
for gid,(lang,f) in pick.items():
    url = f"https://{lang}.wikipedia.org/w/api.php?"+urllib.parse.urlencode(dict(action="query",titles=f,prop="imageinfo",iiprop="url",format="json"))
    for i in range(6):
        try: d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers=UA))); break
        except Exception as e: time.sleep(5*(i+1))
    p = next(iter(d["query"]["pages"].values()))
    ii = p["imageinfo"][0]
    src = ii["url"]; ext = os.path.splitext(src)[1].lower()
    dst = f"shots/raw_{gid}{ext}"
    for i in range(6):
        try:
            open(dst,"wb").write(urllib.request.urlopen(urllib.request.Request(src,headers=UA)).read()); break
        except Exception as e: print("retry",gid,e,file=sys.stderr); time.sleep(5*(i+1))
    meta[gid] = {"file":dst,"source":ii["descriptionurl"]}
    print(gid, dst, file=sys.stderr, flush=True); time.sleep(1)
json.dump(meta, open("shots_meta.json","w"), indent=1)
