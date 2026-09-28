class_name PopStage
extends RefCounted
## A Pop Voyage stage, in a text file of [stage] sections:
##   name=...        theme=0-7 (the scene behind: lighthouse, windmills, desert arch, bamboo temple, glacier, volcano,
##   harbour city at night, aurora)        time=seconds
##   ball=size,x,y,dir      size 0-3 (smallest to biggest), x and y its centre, dir -1 or 1
##   block=x,y,w,h[,cracked]   a block in the air (x, y its lower-left corner); "cracked" breaks under the wire

var name := ""
var theme := 0
var time := 90.0
var balls: Array[Dictionary] = []
var blocks: Array[Dictionary] = []


static func parse_file(text: String) -> Array[PopStage]:
	var out: Array[PopStage] = []
	var cur: PopStage = null
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line == "[stage]":
			cur = PopStage.new()
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
			"time": cur.time = float(val)
			"ball": cur.balls.append({"size": int(p[0]), "pos": Vector2(float(p[1]), float(p[2])), "dir": signf(float(p[3]))})
			"block": cur.blocks.append({"rect": Rect2(float(p[0]), float(p[1]), float(p[2]), float(p[3])),
				"breakable": p.size() > 4 and p[4].strip_edges() == "cracked"})
	return out
