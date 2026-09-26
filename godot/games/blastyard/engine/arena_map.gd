class_name ArenaMap
extends RefCounted
## A Blastyard arena or solo stage, in our own text format (a file holds several, each starting with [arena]):
##
##   [arena]
##   name=Garden Party
##   theme=garden            garden, factory or ice
##   crates=0.75             how many '.' cells get a crate (seeded, so a match replays the same)
##   time=150                seconds before sudden death (arenas) or the stage clock (solo)
##   ###############
##   #1 .........  #         # wall (border) or pillar   + always a crate   . a crate or not (crates=)
##   # #.#.#.#.#.# #           (space) always empty      1-4 player starts
##   ...                      solo: b blob  v bat  g ghost  s stomper (enemies)   X the exit, hidden under a crate
##
## Every row has the same width.

enum T { FLOOR, PILLAR, CRATE }

const ENEMY_CHARS := {"b": "blob", "v": "bat", "g": "ghost", "s": "stomper"}

var name := ""
var theme := "garden"
var crate_density := 0.75
var time := 150.0
var w := 0
var h := 0
var tiles := PackedByteArray()      ## T per cell, crates already rolled
var starts: Array[Vector2i] = []    ## player starts, in slot order
var enemies: Array[Dictionary] = [] ## {kind, cell}
var exit_cell := Vector2i(-1, -1)
var solo := false


static func parse_file(text: String, seed := 1) -> Array[ArenaMap]:
	var out: Array[ArenaMap] = []
	var cur := ""
	for raw in text.split("\n"):
		if raw.strip_edges().to_lower() == "[arena]":
			if cur.strip_edges() != "":
				out.append(parse(cur, seed + out.size()))
			cur = ""
			continue
		cur += raw + "\n"
	if cur.strip_edges() != "":
		out.append(parse(cur, seed + out.size()))
	return out.filter(func(m): return m.w > 0)


static func parse(text: String, seed := 1) -> ArenaMap:
	var m := ArenaMap.new()
	var rows := PackedStringArray()
	for raw in text.split("\n"):
		var line := raw.rstrip(" \t\r")
		if line.strip_edges().is_empty() or line.begins_with(";"):
			continue
		if not line.begins_with("#") and line.contains("="):
			var kv := line.split("=", true, 1)
			match kv[0].strip_edges():
				"name": m.name = kv[1].strip_edges()
				"theme": m.theme = kv[1].strip_edges()
				"crates": m.crate_density = kv[1].to_float()
				"time": m.time = kv[1].to_float()
			continue
		rows.append(line)
	m.h = rows.size()
	for r in rows:
		m.w = maxi(m.w, r.length())
	m.tiles.resize(m.w * m.h)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var starts := {}
	for y in m.h:
		for x in m.w:
			var c := rows[y][x] if x < rows[y].length() else " "
			var t := T.FLOOR
			match c:
				"#": t = T.PILLAR
				"+": t = T.CRATE
				".": t = T.CRATE if rng.randf() < m.crate_density else T.FLOOR
				"X":
					t = T.CRATE
					m.exit_cell = Vector2i(x, y)
					m.solo = true
				"1", "2", "3", "4": starts[c.to_int()] = Vector2i(x, y)
				_:
					if ENEMY_CHARS.has(c):
						m.enemies.append({"kind": ENEMY_CHARS[c], "cell": Vector2i(x, y)})
						m.solo = true
			m.tiles[y * m.w + x] = t
	var keys := starts.keys()
	keys.sort()
	for k in keys:
		m.starts.append(starts[k])
	return m


func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < w and c.y < h


func at(c: Vector2i) -> int:
	return tiles[c.y * w + c.x] if inside(c) else T.PILLAR


func set_at(c: Vector2i, t: int) -> void:
	if inside(c):
		tiles[c.y * w + c.x] = t
