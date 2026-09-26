class_name IngotLevel
extends RefCounted
## An Ingot Run level: a 28x16 grid (other sizes work) in the plain-text tile format used by the free Lode Runner
## remakes, so community level sets read as they are:
##
##   (space) empty   #  brick (diggable)   @  solid stone   H  ladder   -  bar (hand over hand)
##   X  trap brick (looks solid, you fall through)   S  ladder that appears when all the gold is taken
##   $  gold   0  guard   &  the runner
##
## A file holds several levels: each starts with a line "[level]" (our packs; optional "name=..." after it), or the
## levels follow one another as blocks of equal-width rows separated by blank lines (plain sets).

enum T { EMPTY, BRICK, SOLID, LADDER, BAR, TRAP, HIDDEN_LADDER }
const CHARS := {" ": T.EMPTY, ".": T.EMPTY, "#": T.BRICK, "@": T.SOLID, "H": T.LADDER, "-": T.BAR, "X": T.TRAP, "S": T.HIDDEN_LADDER}

var name := ""
var w := 0
var h := 0
var tiles := PackedByteArray()
var gold: Array[Vector2i] = []
var guards: Array[Vector2i] = []
var runner := Vector2i(-1, -1)


static func parse_file(text: String) -> Array[IngotLevel]:
	var out: Array[IngotLevel] = []
	var blocks: Array = []
	var cur: Array[String] = []
	var cur_name := ""
	var bracketed := text.contains("[level]")
	for raw in text.split("\n"):
		var line := raw.rstrip("\r")
		if line.begins_with(";"):
			continue
		if bracketed:
			if line.strip_edges() == "[level]":
				if not cur.is_empty():
					blocks.append([cur_name, cur])
				cur = []
				cur_name = ""
				continue
			if line.begins_with("name="):
				cur_name = line.substr(5).strip_edges()
				continue
			if line.strip_edges() == "" and cur.is_empty():
				continue
			cur.append(line)
		else:
			if line.strip_edges() == "":
				if not cur.is_empty():
					blocks.append([cur_name, cur])
				cur = []
				continue
			cur.append(line)
	if not cur.is_empty():
		blocks.append([cur_name, cur])
	for b in blocks:
		var rows: Array = b[1]
		while not rows.is_empty() and rows.back().strip_edges() == "":
			rows.pop_back()
		var lv := parse_rows(rows)
		if lv.w > 0 and lv.runner.x >= 0:
			lv.name = b[0] if b[0] != "" else "Level %d" % (out.size() + 1)
			out.append(lv)
	return out


static func parse_rows(rows: Array) -> IngotLevel:
	var lv := IngotLevel.new()
	lv.h = rows.size()
	for r in rows:
		lv.w = maxi(lv.w, r.length())
	lv.tiles.resize(lv.w * lv.h)
	for y in lv.h:
		for x in lv.w:
			var c: String = rows[y][x] if x < rows[y].length() else " "
			lv.tiles[y * lv.w + x] = CHARS.get(c, T.EMPTY)
			match c:
				"$": lv.gold.append(Vector2i(x, y))
				"0": lv.guards.append(Vector2i(x, y))
				"&": lv.runner = Vector2i(x, y)
	return lv


func at(c: Vector2i) -> int:
	if c.x < 0 or c.x >= w or c.y >= h:
		return T.SOLID
	if c.y < 0:
		return T.EMPTY
	return tiles[c.y * w + c.x]
