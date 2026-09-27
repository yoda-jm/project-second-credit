class_name RelicLevel
extends RefCounted
## A Relic Run level: a block of screens, each 20 x 12 tiles, written as one map (a file holds several, each after
## [level]). Header lines: name=..., screens=CxR (columns x rows of screens), theme=0|1, route=... (what the demo
## does, see RelicBot). Map characters:
##   #  stone   B  cracked stone (dynamite breaks it)   =  wooden plank (solid)   H  ladder   .  air
##   S  spike trap (springs up when the hero comes near)   D d  a dart hole in the stone, shooting right / left
##      (darts fly high in their row: a crawling hero passes under them)
##   O  the boulder (once the hero passes the column marked o, it rolls that way)
##   C  a crusher (drops on the hero passing under it)   ~  water / a pit of doom (deadly)
##   e  automaton   k  skeleton   b  bat   $  treasure   a  bullets   x  dynamite   E  the exit   P  the start

const SW := 20
const SH := 12

var name := ""
var cols := 1
var rows := 1
var theme := 0
var w := SW
var h := SH
var tiles := PackedByteArray()   ## per tile: the character code of the terrain (# B = H ~ or .)
var things: Array[Dictionary] = []   ## {kind, cell}
var start := Vector2i(1, 1)
var exit := Vector2i(2, 1)
var boulder := Vector2i(-1, -1)
var trigger_col := -1
var route: Array[String] = []


static func parse_file(text: String) -> Array[RelicLevel]:
	var out: Array[RelicLevel] = []
	var cur: RelicLevel = null
	var rows_txt: Array[String] = []
	for raw in text.split("\n"):
		var line := raw.rstrip("\r")
		if line.strip_edges() == "[level]":
			if cur:
				cur._map(rows_txt)
				out.append(cur)
			cur = RelicLevel.new()
			rows_txt = []
			continue
		if cur == null or line.begins_with(";"):
			continue
		if line.begins_with("name="): cur.name = line.substr(5).strip_edges()
		elif line.begins_with("screens="):
			cur.cols = int(line.substr(8).get_slice("x", 0))
			cur.rows = int(line.substr(8).get_slice("x", 1))
		elif line.begins_with("theme="): cur.theme = int(line.substr(6))
		elif line.begins_with("route="): cur.route.assign(line.substr(6).strip_edges().split(" ", false))
		elif line.length() > 0 and not _header(line):
			rows_txt.append(line)
	if cur:
		cur._map(rows_txt)
		out.append(cur)
	return out


## A header line is a lowercase word and "=" (map rows may hold "=" too: the planks).
static func _header(line: String) -> bool:
	var i := line.find("=")
	return i > 0 and line.substr(0, i).is_valid_identifier() and line.substr(0, i) == line.substr(0, i).to_lower()


func _map(lines: Array[String]) -> void:
	w = cols * SW
	h = rows * SH
	tiles.resize(w * h)
	tiles.fill(".".unicode_at(0))
	for y in mini(lines.size(), h):
		for x in mini(lines[y].length(), w):
			var ch := lines[y][x]
			var c := Vector2i(x, y)
			match ch:
				"#", "B", "=", "H", "~":
					tiles[y * w + x] = ch.unicode_at(0)
				"P": start = c
				"E": exit = c
				"O": boulder = c
				"o": trigger_col = x
				"S", "D", "d", "C", "e", "k", "b", "$", "a", "x":
					things.append({"kind": ch, "cell": c})
					if ch == "D" or ch == "d":
						tiles[y * w + x] = "#".unicode_at(0)  # the hole is carved in solid stone


func at(x: int, y: int) -> String:
	if x < 0 or y < 0 or x >= w or y >= h:
		return "#"
	return char(tiles[y * w + x])
