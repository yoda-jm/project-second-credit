class_name GardenMap
extends RefCounted
## A Fruitburrow garden: a vertical slice of soil with tunnels, fruit, apples, a monster nest and the start.
## Our own text format, in the spirit of BDCFF: a pack file holds several gardens.
##
##   ; comment
##   [pack]
##   name=Second Credit Orchard
##   [garden]
##   name=First Harvest
##   monsters=5        how many monsters come out of the nest in total
##   diggers=1         how many of them can dig through soil from the start
##   ##..c.##A##       the grid, one line per row, all rows the same width
##
## Grid: # soil   . tunnel   X stone (never dug)   A apple (in soil)   N nest (tunnel)   P player start (tunnel)
##       fruit in soil: c cherries, b banana, p pear, g grapes, s strawberry

enum Terrain { SOIL, TUNNEL, STONE }

const FRUIT_CHARS := "cbpgs"
const FRUIT_NAMES := ["cherries", "banana", "pear", "grapes", "strawberry"]

var name := ""
var monsters := 5
var diggers := 0
var w := 0
var h := 0
var terrain := PackedByteArray()
var fruit := {}  ## Vector2i -> fruit index (into FRUIT_NAMES)
var apples: Array[Vector2i] = []
var nest := Vector2i.ZERO
var start := Vector2i.ZERO


## Parses a pack file into its gardens (at least one; a file with no [garden] header is one garden).
static func parse_pack(text: String) -> Array[GardenMap]:
	var out: Array[GardenMap] = []
	var chunks := PackedStringArray()
	var cur := ""
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.to_lower() == "[garden]":
			if cur.strip_edges() != "":
				chunks.append(cur)
			cur = ""
			continue
		if line.to_lower() == "[pack]":
			continue
		cur += raw + "\n"
	if cur.strip_edges() != "":
		chunks.append(cur)
	for c in chunks:
		var g := parse(c)
		if g.w > 0:
			out.append(g)
	return out


static func parse(text: String) -> GardenMap:
	var m := GardenMap.new()
	var rows := PackedStringArray()
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.is_empty() or line.begins_with(";") or line.begins_with("["):
			continue
		if line.contains("="):
			var kv := line.split("=", true, 1)
			match kv[0].strip_edges().to_lower():
				"name": m.name = kv[1].strip_edges()
				"monsters": m.monsters = kv[1].to_int()
				"diggers": m.diggers = kv[1].to_int()
			continue
		rows.append(line)
	m.h = rows.size()
	m.w = rows[0].length() if m.h > 0 else 0
	m.terrain.resize(m.w * m.h)
	for y in m.h:
		for x in m.w:
			var c := rows[y][x] if x < rows[y].length() else "#"
			var t := Terrain.SOIL
			match c:
				".": t = Terrain.TUNNEL
				"X": t = Terrain.STONE
				"N":
					t = Terrain.TUNNEL
					m.nest = Vector2i(x, y)
				"P":
					t = Terrain.TUNNEL
					m.start = Vector2i(x, y)
				"A":
					m.apples.append(Vector2i(x, y))
				_:
					var f := FRUIT_CHARS.find(c)
					if f >= 0:
						m.fruit[Vector2i(x, y)] = f
			m.terrain[y * m.w + x] = t
	return m


static func load_pack(path: String) -> Array[GardenMap]:
	return parse_pack(FileAccess.get_file_as_string(path))


func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < w and c.y < h
