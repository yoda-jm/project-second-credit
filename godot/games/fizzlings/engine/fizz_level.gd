class_name FizzLevel
extends RefCounted
## A Fizzlings level: 32 x 26 characters after [level] (a file holds several):
##   #  platform (the two outer columns on each side are the walls)     .  open water
##   A B  where hero 1 and 2 start (standing in that cell)                b s f  a beetle, a spring, a flyer
## Header lines before the grid: name=..., colour=r,g,b (the platform tint), hurry=seconds (extra time before the
## toys turn angry).

const W := 32
const H := 26

var name := ""
var colour := Color(0.95, 0.55, 0.7)
var hurry_extra := 0.0
var solid := PackedByteArray()
var starts: Array[Vector2] = []
var toys: Array[Dictionary] = []


static func parse_file(text: String) -> Array[FizzLevel]:
	var out: Array[FizzLevel] = []
	var cur: FizzLevel = null
	var rows: Array[String] = []
	for raw in text.split("\n"):
		var line := raw.rstrip("\r")
		if line.strip_edges() == "[level]":
			if cur:
				cur._grid(rows)
				out.append(cur)
			cur = FizzLevel.new()
			rows = []
			continue
		if cur == null or line.begins_with(";"):
			continue
		if line.begins_with("name="):
			cur.name = line.substr(5).strip_edges()
		elif line.begins_with("colour="):
			var p := line.substr(7).split(",")
			cur.colour = Color(float(p[0]), float(p[1]), float(p[2]))
		elif line.begins_with("hurry="):
			cur.hurry_extra = float(line.substr(6))
		elif line.length() >= W:
			rows.append(line)
	if cur:
		cur._grid(rows)
		out.append(cur)
	return out


func _grid(rows: Array[String]) -> void:
	solid.resize(W * H)
	solid.fill(0)
	var sa := Vector2.ZERO
	var sb := Vector2.ZERO
	for y in mini(rows.size(), H):
		for x in W:
			var ch := rows[y][x]
			var feet := Vector2(x + 0.5, y + 1.0)
			match ch:
				"#": solid[y * W + x] = 1
				"A": sa = feet
				"B": sb = feet
				"b": toys.append({"kind": "beetle", "pos": feet})
				"s": toys.append({"kind": "spring", "pos": feet})
				"f": toys.append({"kind": "flyer", "pos": feet + Vector2(0, -0.5)})
	starts = [sa, sb if sb != Vector2.ZERO else sa + Vector2(3, 0)]
