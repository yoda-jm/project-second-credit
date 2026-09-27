class_name HenLevel
extends RefCounted
## A Henhouse Heist level: 32 x 26 characters after [level] (a file holds several):
##   #  brick platform (stood on from above; jumped through from below)   H  ladder   .  air
##   o  an egg   g  grain   h  a hen (starting there)   P  the farmhand   L  a lift shaft (two columns wide, from
##   top to bottom: the lifts rise through it)   G  the goose's cage (top left, 2 x 2)
## Header lines before the grid: name=..., hens=N (how many hens roam, the first N of the h marks), goose=1 (the goose
## breaks out), time=seconds.

const W := 32
const H := 26

var name := ""
var solid := PackedByteArray()
var ladder := PackedByteArray()
var eggs: Array[Vector2i] = []
var grain: Array[Vector2i] = []
var hens: Array[Vector2i] = []
var start := Vector2i(2, 24)
var lift_col := -1
var cage := Vector2i(-1, -1)
var hen_count := 3
var goose := false
var time_limit := 90.0


static func parse_file(text: String) -> Array[HenLevel]:
	var out: Array[HenLevel] = []
	var cur: HenLevel = null
	var rows: Array[String] = []
	for raw in text.split("\n"):
		var line := raw.rstrip("\r")
		if line.strip_edges() == "[level]":
			if cur:
				cur._grid(rows)
				out.append(cur)
			cur = HenLevel.new()
			rows = []
			continue
		if cur == null or line.begins_with(";"):
			continue
		if line.begins_with("name="): cur.name = line.substr(5).strip_edges()
		elif line.begins_with("hens="): cur.hen_count = int(line.substr(5))
		elif line.begins_with("goose="): cur.goose = line.substr(6).strip_edges() == "1"
		elif line.begins_with("time="): cur.time_limit = float(line.substr(5))
		elif line.length() >= W:
			rows.append(line)
	if cur:
		cur._grid(rows)
		out.append(cur)
	return out


func _grid(rows: Array[String]) -> void:
	solid.resize(W * H)
	solid.fill(0)
	ladder.resize(W * H)
	ladder.fill(0)
	for y in mini(rows.size(), H):
		for x in W:
			var ch := rows[y][x]
			var c := Vector2i(x, y)
			match ch:
				"#": solid[y * W + x] = 1
				"H": ladder[y * W + x] = 1
				"o": eggs.append(c)
				"g": grain.append(c)
				"h": hens.append(c)
				"P": start = c
				"L":
					if lift_col < 0 or x < lift_col:
						lift_col = x
				"G":
					if cage.x < 0:
						cage = c
