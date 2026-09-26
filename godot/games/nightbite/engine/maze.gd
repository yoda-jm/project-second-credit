class_name NightMaze
extends RefCounted
## A Nightbite maze in our own text format (a file holds several, each starting with [maze]):
##
##   name=Firefly Row
##   color=violet                        the neon colour of the walls
##   #  wall   .  light pellet   o  power orb   (space) empty path   -  spirit gate
##   P  the hero's start   1  the first spirit (outside the house)   2 3 4  the house   F  where bonus gems appear
##
## An open cell on the left or right edge wraps round to the other side (tunnels).

var name := ""
var color := "violet"
var w := 0
var h := 0
var walls := PackedByteArray()
var gate := {}          ## cell -> true
var pellets := {}       ## cell -> true
var powers := {}        ## cell -> true
var hero := Vector2i.ZERO
var spirits: Array[Vector2i] = []  ## starts: [outside, then the house cells]
var house: Array[Vector2i] = []
var bonus := Vector2i(-1, -1)


static func parse_file(text: String) -> Array[NightMaze]:
	var out: Array[NightMaze] = []
	var cur: Array[String] = []
	var meta := {}
	for raw in (text + "\n[maze]").split("\n"):
		var line := raw.rstrip("\r")
		if line.strip_edges() == "[maze]" or line.strip_edges() == "":
			if cur.size() > 3:
				out.append(parse(cur, meta))
				cur = []
			if line.strip_edges() == "[maze]":
				cur = []
				meta = {}
			continue
		if line.begins_with(";"):
			continue
		if line.contains("=") and not line.contains("#"):
			var kv := line.split("=", true, 1)
			meta[kv[0].strip_edges()] = kv[1].strip_edges()
			continue
		cur.append(line)
	return out


static func parse(rows: Array[String], meta: Dictionary) -> NightMaze:
	var m := NightMaze.new()
	m.name = meta.get("name", "Maze")
	m.color = meta.get("color", "violet")
	m.h = rows.size()
	for r in rows:
		m.w = maxi(m.w, r.length())
	m.walls.resize(m.w * m.h)
	var first := Vector2i(-1, -1)
	for y in m.h:
		for x in m.w:
			var ch := rows[y][x] if x < rows[y].length() else " "
			var c := Vector2i(x, y)
			match ch:
				"#": m.walls[y * m.w + x] = 1
				"-": m.gate[c] = true
				".": m.pellets[c] = true
				"o": m.powers[c] = true
				"P": m.hero = c
				"1": first = c
				"2", "3", "4": m.house.append(c)
				"F": m.bonus = c
	m.spirits = [first]
	for i in 3:
		m.spirits.append(m.house[i % m.house.size()] if not m.house.is_empty() else first)
	return m


func wrap_cell(c: Vector2i) -> Vector2i:
	return Vector2i(posmod(c.x, w), c.y)


func wall(c: Vector2i) -> bool:
	c = wrap_cell(c)
	return c.y < 0 or c.y >= h or walls[c.y * w + c.x] == 1
