class_name FuseStage
extends RefCounted
## A Fuseflight stage, in a text file of [stage] sections: the arena is 16 x 12 units, y up, the floor at 0.
##   name=...   theme=0-4 (the festival scene behind)   speed=1.. (how keen the enemies are)   enemies=N (at most at once)
##   start=x,y   platform=x,y,w,h (lower-left corner, size)   bomb=x,y (one per firework, in the stage's order: the
##   lit fuse goes from each to the next)

var name := ""
var theme := 0
var speed := 1.0
var max_enemies := 3
var start := Vector2(8, 0)
var platforms: Array[Rect2] = []
var bombs: Array[Vector2] = []


static func parse_file(text: String) -> Array[FuseStage]:
	var out: Array[FuseStage] = []
	var cur: FuseStage = null
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line == "[stage]":
			cur = FuseStage.new()
			out.append(cur)
			continue
		if cur == null or line.begins_with(";") or not line.contains("="):
			continue
		var key := line.get_slice("=", 0)
		var val := line.substr(key.length() + 1)
		var p := val.split(",")
		match key:
			"name": cur.name = val
			"theme": cur.theme = int(val)
			"speed": cur.speed = float(val)
			"enemies": cur.max_enemies = int(val)
			"start": cur.start = Vector2(float(p[0]), float(p[1]))
			"platform": cur.platforms.append(Rect2(float(p[0]), float(p[1]), float(p[2]), float(p[3])))
			"bomb": cur.bombs.append(Vector2(float(p[0]), float(p[1])))
	return out
