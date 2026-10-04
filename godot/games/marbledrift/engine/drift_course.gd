class_name DriftCourse
extends RefCounted
## A Marble Drift course, in a text file of [course] sections (a file holds several; tools/marble_courses.py writes
## ours). The floor is a height field on a grid of cells (1 unit each, x across, z down the course): heights are given
## per vertex, (W + 1) x (H + 1) numbers, so slopes come from neighbouring vertices; each cell has a kind.
##   name=...   time=seconds   theme=0-5   start=x,z   route=x,z[,speed] ... (the demo's waypoints, with a speed to
##   hold towards that point when it matters: a jump needs a run-up)
##   enemy=kind,x,z[,x2,z2]   (steelie: a black marble that hunts you; hopper: patrols from x,z to x2,z2)
##   size=W,H   then "heights:" and H + 1 rows of W + 1 numbers (tenths of a unit), then "cells:" and H rows of W chars:
##   . floor   # wall (solid, rises above the floor)   _ void (nothing: a fall to oblivion)   ~ acid   G goal
##   = fast floor (glass: less grip)   ^ bumpy floor (rough: more grip)

const KINDS := ".#_~G=^"

var name := ""
var time := 60.0
var theme := 0
var w := 0
var h := 0
var heights := PackedFloat32Array()   ## (w + 1) * (h + 1) vertex heights
var cells := PackedByteArray()        ## w * h kind characters
var start := Vector2(1.5, 1.5)
var route: Array[Vector2] = []
var route_speed: Array[float] = []   ## per route point: the demo's speed towards it (0: its own choice)
var enemies: Array[Dictionary] = []


static func parse_file(text: String) -> Array[DriftCourse]:
	var out: Array[DriftCourse] = []
	var cur: DriftCourse = null
	var mode := ""
	var rows: Array[String] = []
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line == "[course]":
			if cur:
				cur._finish(rows)
			cur = DriftCourse.new()
			out.append(cur)
			mode = ""
			rows = []
			continue
		if cur == null or line.begins_with(";") or line == "":
			continue
		if line == "heights:":
			mode = "heights"
			continue
		if line == "cells:":
			mode = "cells"
			continue
		if mode == "heights":
			for v in line.split(" ", false):
				cur.heights.append(float(v) * 0.1)
			continue
		if mode == "cells":
			rows.append(line)
			continue
		var key := line.get_slice("=", 0)
		var val := line.substr(key.length() + 1)
		match key:
			"name": cur.name = val
			"time": cur.time = float(val)
			"theme": cur.theme = int(val)
			"size":
				cur.w = int(val.get_slice(",", 0))
				cur.h = int(val.get_slice(",", 1))
			"start": cur.start = Vector2(float(val.get_slice(",", 0)), float(val.get_slice(",", 1)))
			"route":
				for p in val.split(" ", false):
					var q := p.split(",")
					cur.route.append(Vector2(float(q[0]), float(q[1])))
					cur.route_speed.append(float(q[2]) if q.size() > 2 else 0.0)
			"enemy":
				var p := val.split(",")
				var e := {"kind": p[0], "pos": Vector2(float(p[1]), float(p[2]))}
				if p.size() >= 5:
					e["to"] = Vector2(float(p[3]), float(p[4]))
				cur.enemies.append(e)
	if cur:
		cur._finish(rows)
	return out


func _finish(rows: Array[String]) -> void:
	cells.resize(w * h)
	cells.fill(".".unicode_at(0))
	for z in mini(rows.size(), h):
		for x in mini(rows[z].length(), w):
			cells[z * w + x] = rows[z].unicode_at(x)


## The checkpoints shown on the course: route points (not the goal, not run-up points with a speed) about GATE_GAP
## apart along the route. A broken marble comes back at the last one passed.
const GATE_GAP := 9.0


func gates() -> Array[int]:
	var out: Array[int] = []
	var prev := start
	var run := 0.0
	for i in route.size() - 1:
		run += prev.distance_to(route[i])
		prev = route[i]
		if i < route_speed.size() and route_speed[i] > 0.0:
			continue
		if run >= GATE_GAP:
			out.append(i)
			run = 0.0
	return out


func kind(x: int, z: int) -> String:
	if x < 0 or z < 0 or x >= w or z >= h:
		return "_"
	return char(cells[z * w + x])


func vertex(x: int, z: int) -> float:
	return heights[clampi(z, 0, h) * (w + 1) + clampi(x, 0, w)]


## The floor's height at a point (bilinear in its cell), or -INF over the void.
func height_at(p: Vector2) -> float:
	var cx := int(floor(p.x))
	var cz := int(floor(p.y))
	var k := kind(cx, cz)
	if k == "_":
		return -INF
	var fx := p.x - cx
	var fz := p.y - cz
	var a := lerpf(vertex(cx, cz), vertex(cx + 1, cz), fx)
	var b := lerpf(vertex(cx, cz + 1), vertex(cx + 1, cz + 1), fx)
	var y := lerpf(a, b, fz)
	if k == "#":
		y += 1.5  # walls stand above the floor
	return y


## The slope at a point: how much the floor rises per unit of x and of z.
func gradient(p: Vector2) -> Vector2:
	var cx := int(floor(p.x))
	var cz := int(floor(p.y))
	var fx := p.x - cx
	var fz := p.y - cz
	var dx := lerpf(vertex(cx + 1, cz) - vertex(cx, cz), vertex(cx + 1, cz + 1) - vertex(cx, cz + 1), fz)
	var dz := lerpf(vertex(cx, cz + 1) - vertex(cx, cz), vertex(cx + 1, cz + 1) - vertex(cx + 1, cz), fx)
	return Vector2(dx, dz)
