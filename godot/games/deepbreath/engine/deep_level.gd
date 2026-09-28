class_name DeepLevel
extends RefCounted
## A Deep Breath cavern: 32 x 16 characters after [cavern] (a file holds several). Map characters:
##   .  air          =  floor (stood on from above, jumped through from below)      #  rock wall (solid)
##   ~  crumbling floor (gives way under the miner)    <  >  conveyor floor moving left / right
##   x  something deadly (spikes, a poisonous plant, a steam vent)   k  a key   P  the exit lift (2 x 2, its top-left)
##   M  the miner's start (standing in that cell)
## Header lines: name=..., theme=0-5, air=seconds, route=... (what the demo does, see DeepBot), and any number of
## guard=kind,x,y,axis,min,max,speed  (axis h: x goes from min to max; axis v: y does; kind names the model).

const W := 32
const H := 16

var name := ""
var theme := 0
var air := 60.0
var tiles := PackedByteArray()
var keys: Array[Vector2i] = []
var hazards: Array[Vector2i] = []
var guards: Array[Dictionary] = []
var portal := Vector2i(29, 13)
var start := Vector2i(1, 14)
var route: Array[String] = []


static func parse_file(text: String) -> Array[DeepLevel]:
	var out: Array[DeepLevel] = []
	var cur: DeepLevel = null
	var rows: Array[String] = []
	for raw in text.split("\n"):
		var line := raw.rstrip("\r")
		if line.strip_edges() == "[cavern]":
			if cur:
				cur._grid(rows)
				out.append(cur)
			cur = DeepLevel.new()
			rows = []
			continue
		if cur == null or line.begins_with(";"):
			continue
		if line.begins_with("name="): cur.name = line.substr(5).strip_edges()
		elif line.begins_with("theme="): cur.theme = int(line.substr(6))
		elif line.begins_with("air="): cur.air = float(line.substr(4))
		elif line.begins_with("route="): cur.route.assign(line.substr(6).strip_edges().split(" ", false))
		elif line.begins_with("guard="):
			var p := line.substr(6).split(",")
			# positions are feet (x centre of the cell, y the bottom of the cell); min and max are cells on the axis
			var off := 0.5 if p[3] == "h" else 1.0
			cur.guards.append({"kind": p[0], "pos": Vector2(float(p[1]) + 0.5, float(p[2]) + 1.0), "axis": p[3],
				"min": float(p[4]) + off, "max": float(p[5]) + off, "speed": float(p[6])})
		elif line.length() >= W:
			rows.append(line)
	if cur:
		cur._grid(rows)
		out.append(cur)
	return out


func _grid(rows: Array[String]) -> void:
	tiles.resize(W * H)
	tiles.fill(".".unicode_at(0))
	var portal_set := false
	for y in mini(rows.size(), H):
		for x in W:
			var ch := rows[y][x]
			var c := Vector2i(x, y)
			match ch:
				"#", "=", "~", "<", ">":
					tiles[y * W + x] = ch.unicode_at(0)
				"x": hazards.append(c)
				"k": keys.append(c)
				"M": start = c
				"P":
					if not portal_set:
						portal = c
						portal_set = true


func at(x: int, y: int) -> String:
	if x < 0 or x >= W:
		return "#"
	if y < 0 or y >= H:
		return "."
	return char(tiles[y * W + x])
