import json, urllib.request, urllib.parse, time, os, sys
UA={"User-Agent":"renovated-games-catalog/0.1 (personal research)"}
pick={"alleycat":("it","File:Alley Cat.png"),"alleycat_a8":("ru","Файл:A8-AlleyCat gameplay.gif"),"cannonfodder":("it","File:Cannon Fodder.png"),
"z":("ru","Файл:Z game.png"),"pipemania":("it","File:Pipe Mania.png"),"bomberman":("it","File:Bomberman (videogioco 1990).png"),
"northsouth":("it","File:North & South.png")}
meta=json.load(open("shots_meta.json"))
for gid,(lang,f) in pick.items():
    url=f"https://{lang}.wikipedia.org/w/api.php?"+urllib.parse.urlencode(dict(action="query",titles=f,prop="imageinfo",iiprop="url",format="json"))
    for i in range(6):
        try: d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers=UA))); break
        except Exception: time.sleep(8*(i+1))
    ii=next(iter(d["query"]["pages"].values()))["imageinfo"][0]
    src=ii["url"]; ext=os.path.splitext(urllib.parse.urlparse(src).path)[1].lower()
    for f2 in os.listdir("shots"):
        if f2.startswith(f"raw_{gid}.") : os.remove("shots/"+f2)
    dst=f"shots/raw_{gid}{ext}"
    for i in range(6):
        try: open(dst,"wb").write(urllib.request.urlopen(urllib.request.Request(src,headers=UA)).read()); break
        except Exception as e: time.sleep(8*(i+1))
    meta[gid]={"file":dst,"source":ii["descriptionurl"]}; print(gid,dst,file=sys.stderr); time.sleep(2)
json.dump(meta,open("shots_meta.json","w"),indent=1)
