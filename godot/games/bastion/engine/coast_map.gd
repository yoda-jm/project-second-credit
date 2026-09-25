class_name CoastMap
extends RefCounted
## A Bastion Coast battlefield: land and water cells, and castle sites (2x2). Our own text format:
##
##   name=First Shore
##   ~~~~....~~~
##   ~~..C...~~~        ~ water   . land   C castle (top-left cell of a 2x2 castle)   # rock (land, unbuildable)
##
## Lines before the grid are key=value. Every grid row has the same width.

enum Terrain { WATER, LAND, ROCK }

var name := ""
var w := 0
var h := 0
var terrain := PackedByteArray()
var castles: Array[Vector2i] = []  ## top-left cells of the castles


static func parse(text: String) -> CoastMap:
	var m := CoastMap.new()
	var rows := PackedStringArray()
	for raw in text.split("\n"):
		var line := raw.strip_edges(false, true)
		if line.is_empty() or line.begins_with(";"):
			continue
		if rows.is_empty() and line.contains("="):
			var kv := line.split("=", true, 1)
			if kv[0].strip_edges() == "name":
				m.name = kv[1].strip_edges()
			continue
		rows.append(line)
	m.h = rows.size()
	m.w = rows[0].length() if m.h > 0 else 0
	m.terrain.resize(m.w * m.h)
	for y in m.h:
		var row := rows[y]
		for x in m.w:
			var c := row[x] if x < row.length() else "~"
			match c:
				"~": m.terrain[y * m.w + x] = Terrain.WATER
				"#": m.terrain[y * m.w + x] = Terrain.ROCK
				_: m.terrain[y * m.w + x] = Terrain.LAND
			if c == "C":
				m.castles.append(Vector2i(x, y))
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
