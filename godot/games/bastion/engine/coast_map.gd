class_name CoastMap
extends RefCounted
## A Bastion Coast battlefield: land and water cells, and castle sites (2x2). Our own text format:
##
##   name=First Shore
##   rounds=4           (optional) hold the island this many rounds to win it; 0 or absent: play until it falls
##                      (versus: the match ends after this many rounds, the best score wins)
##   players=2          (optional) a versus map for up to this many players
##   ~~~~....~~~
##   ~~..C...~~~        ~ water   . land   C castle (top-left cell of a 2x2 castle)   # rock (land, unbuildable)
##
## Lines before the grid are key=value. Every grid row has the same width.
## Versus maps write castles as 1, 2 or 3 instead of C: the castle, and the whole land mass it stands on (land and
## rock connected to it, not across water), belong to that player's region. A player builds only in their region.

enum Terrain { WATER, LAND, ROCK }

var name := ""
var rounds := 0  ## rounds to hold the island (0: endless)
var w := 0
var h := 0
var terrain := PackedByteArray()
var castles: Array[Vector2i] = []  ## top-left cells of the castles
var players := 1  ## versus maps: how many players the coast has room for
var region := PackedByteArray()  ## versus maps: per cell, 0 (nobody's) or the owning player + 1


static func parse(text: String) -> CoastMap:
	var m := CoastMap.new()
	var rows := PackedStringArray()
	for raw in text.split("\n"):
		var line := raw.strip_edges(false, true)
		if line.is_empty() or line.begins_with(";"):
			continue
		if rows.is_empty() and line.contains("="):
			var kv := line.split("=", true, 1)
			match kv[0].strip_edges():
				"name": m.name = kv[1].strip_edges()
				"rounds": m.rounds = maxi(0, kv[1].to_int())
				"players": m.players = clampi(kv[1].to_int(), 1, 3)
			continue
		rows.append(line)
	m.h = rows.size()
	m.w = rows[0].length() if m.h > 0 else 0
	m.terrain.resize(m.w * m.h)
	m.region.resize(m.w * m.h)
	var seeds := {}  # castle cell index -> player
	for y in m.h:
		var row := rows[y]
		for x in m.w:
			var c := row[x] if x < row.length() else "~"
			match c:
				"~": m.terrain[y * m.w + x] = Terrain.WATER
				"#": m.terrain[y * m.w + x] = Terrain.ROCK
				_: m.terrain[y * m.w + x] = Terrain.LAND
			if c == "C" or c in ["1", "2", "3"]:
				m.castles.append(Vector2i(x, y))
				if c != "C":
					seeds[y * m.w + x] = c.to_int()
	# regions: flood each player's castles over connected land and rock
	for start in seeds:
		var stack: Array[int] = [start]
		m.region[start] = seeds[start]
		while not stack.is_empty():
			var i: int = stack.pop_back()
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var nx: int = i % m.w + d.x
				var ny: int = i / m.w + d.y
				var j := ny * m.w + nx
				if m.inside(nx, ny) and m.region[j] == 0 and m.terrain[j] != Terrain.WATER:
					m.region[j] = seeds[start]
					stack.append(j)
	return m


static func load_file(path: String) -> CoastMap:
	return parse(FileAccess.get_file_as_string(path))


func inside(x: int, y: int) -> bool:
	return x >= 0 and y >= 0 and x < w and y < h


func at(x: int, y: int) -> int:
	return terrain[y * w + x] if inside(x, y) else Terrain.WATER


func is_land(x: int, y: int) -> bool:
	return at(x, y) == Terrain.LAND


func castle_at(x: int, y: int) -> int:
	## Index of the castle covering (x, y), or -1.
	for i in castles.size():
		var c := castles[i]
		if x >= c.x and x <= c.x + 1 and y >= c.y and y <= c.y + 1:
			return i
	return -1


## The player (0-based) whose region holds (x, y), or -1 (water, or a map without regions).
func region_of(x: int, y: int) -> int:
	return region[y * w + x] - 1 if inside(x, y) else -1


## The castles standing in player `p`'s region.
func castles_of(p: int) -> Array[int]:
	var out: Array[int] = []
	for i in castles.size():
		if region_of(castles[i].x, castles[i].y) == p:
			out.append(i)
	return out
