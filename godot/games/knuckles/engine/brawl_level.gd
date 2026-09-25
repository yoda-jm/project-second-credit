class_name BrawlLevel
extends RefCounted
## A Neon Knuckles stage: its length, the weapons lying in the street and the waves of enemies. Our text format
## (a file holds several stages):
##
##   [stage]
##   name=Neon Row
##   theme=street            street, docks, rooftops (the look)
##   length=90               metres of street
##   item=bat, 18, 0.5       a weapon: kind, x, depth
##   wave=14: thug, thug, knifer:left      when the lead player nears x = 14; enemies (":left" enters from the left)

var name := ""
var theme := "street"
var length := 80.0
var items: Array[Dictionary] = []  ## {kind, x, z}
var waves: Array[Dictionary] = []  ## {at, enemies: [{kind, side}]}


static func parse_file(text: String) -> Array[BrawlLevel]:
	var out: Array[BrawlLevel] = []
	var cur: BrawlLevel = null
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.is_empty() or line.begins_with(";"):
			continue
		if line.to_lower() == "[stage]":
			cur = BrawlLevel.new()
			out.append(cur)
			continue
		if cur == null or not line.contains("="):
			continue
		var kv := line.split("=", true, 1)
		var v := kv[1].strip_edges()
		match kv[0].strip_edges().to_lower():
			"name": cur.name = v
			"theme": cur.theme = v
			"length": cur.length = v.to_float()
			"item":
				var p := v.split(",")
				cur.items.append({"kind": p[0].strip_edges(), "x": p[1].to_float(), "z": p[2].to_float() if p.size() > 2 else 0.0})
			"wave":
				var head := v.split(":", true, 1)
				var w := {"at": head[0].to_float(), "enemies": []}
				for e in head[1].split(",", false):
					var ek := e.strip_edges().split(":")
					w["enemies"].append({"kind": ek[0], "side": ek[1] if ek.size() > 1 else "right"})
				cur.waves.append(w)
	return out
