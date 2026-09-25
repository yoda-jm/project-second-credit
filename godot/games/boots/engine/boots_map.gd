class_name BootsMap
extends RefCounted
## A Muddy Boots mission map: terrain tiles plus things placed on them, and the mission's goals.
## Our own text format (a campaign file holds several missions):
##
##   [mission]
##   name=Jungle Welcome
##   goals=kill,destroy      kill: every enemy; destroy: every hut; rescue: every hostage
##   grenades=4
##   rockets=0
##   ..TT..~~~..            the grid, one line per row
##
## Terrain: . land   , rough (slows)   ~ water (swim, no shooting)   - shallows (slows)   T tree   # rock
##          q quicksand (slows a lot)   * snow (slows)   x cliff (blocks)
## Things (on land): P the squad's start   E enemy soldier   H hut (2x2, spawns enemies)   h hostage
##                   X rescue tent   G grenade crate   R rocket crate   M mine
## The original game's maps are read by CfImport into the same structure.

enum T { LAND, ROUGH, WATER, SHALLOW, TREE, ROCK, QUICKSAND, SNOW, CLIFF }

const TERRAIN_CHARS := {".": T.LAND, ",": T.ROUGH, "~": T.WATER, "-": T.SHALLOW, "T": T.TREE, "#": T.ROCK,
	"q": T.QUICKSAND, "*": T.SNOW, "x": T.CLIFF}
const THING_CHARS := {"P": "start", "E": "enemy", "H": "hut", "h": "hostage", "X": "tent", "G": "grenades",
	"R": "rockets", "M": "mine"}

var name := ""
var goals: Array[String] = ["kill"]
var grenades := 4
var rockets := 0
var w := 0
var h := 0
var terrain := PackedByteArray()
var things: Array[Dictionary] = []  ## {kind, cell: Vector2i}
var source := "text"  ## "text" or "original"


static func parse_campaign(text: String) -> Array[BootsMap]:
	var out: Array[BootsMap] = []
	var cur := ""
	for raw in text.split("\n"):
		if raw.strip_edges().to_lower() == "[mission]":
			if cur.strip_edges() != "":
				out.append(parse(cur))
			cur = ""
			continue
		cur += raw + "\n"
	if cur.strip_edges() != "":
		out.append(parse(cur))
	return out.filter(func(m): return m.w > 0)


static func parse(text: String) -> BootsMap:
	var m := BootsMap.new()
	var rows := PackedStringArray()
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.is_empty() or line.begins_with(";") or line.begins_with("["):
			continue
		if line.contains("="):
			var kv := line.split("=", true, 1)
			match kv[0].strip_edges().to_lower():
				"name": m.name = kv[1].strip_edges()
				"goals":
					m.goals.clear()
					for g in kv[1].split(",", false):
						m.goals.append(g.strip_edges())
				"grenades": m.grenades = kv[1].to_int()
				"rockets": m.rockets = kv[1].to_int()
			continue
		rows.append(line)
	m.h = rows.size()
	m.w = rows[0].length() if m.h > 0 else 0
	m.terrain.resize(m.w * m.h)
	for y in m.h:
		for x in m.w:
			var c := rows[y][x] if x < rows[y].length() else "."
			m.terrain[y * m.w + x] = TERRAIN_CHARS.get(c, T.LAND)
			if THING_CHARS.has(c):
				m.things.append({"kind": THING_CHARS[c], "cell": Vector2i(x, y)})
	return m


func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < w and c.y < h


func at(c: Vector2i) -> int:
	return terrain[c.y * w + c.x] if inside(c) else T.CLIFF


func blocks(c: Vector2i) -> bool:
	var t := at(c)
	return t == T.TREE or t == T.ROCK or t == T.CLIFF


func count(kind: String) -> int:
	return things.filter(func(t): return t["kind"] == kind).size()
