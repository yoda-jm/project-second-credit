class_name BloomLevel
extends RefCounted
## A Bloomwand level: a 20 x 15 grid ('#' block, 'H' ladder, '*' flower, 'P' 'Q' starts, 'g' 'b' 's' 'c' creatures),
## read from `levels/*.bloom` ([level] name= theme= map: then 15 rows). Rows count down from the top.

const W := 20
const H := 15

var name := ""
var theme := 0
var rows: Array[String] = []


static func parse_file(text: String) -> Array[BloomLevel]:
	var out: Array[BloomLevel] = []
	var cur: BloomLevel = null
	var in_map := false
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.begins_with(";") or line.is_empty():
			continue
		if line == "[level]":
			cur = BloomLevel.new()
			out.append(cur)
			in_map = false
			continue
		if cur == null:
			continue
		if in_map:
			if cur.rows.size() < H:
				cur.rows.append(line.rpad(W, "."))
			continue
		if line == "map:":
			in_map = true
		elif line.begins_with("name="):
			cur.name = line.substr(5)
		elif line.begins_with("theme="):
			cur.theme = int(line.substr(6))
	return out


func at(x: int, row: int) -> String:
	if x < 0 or x >= W or row < 0 or row >= H:
		return "#"
	return rows[row][x]
