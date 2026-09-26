class_name MossDemo
extends RefCounted
## Plays a level's recorded solution (the demo): "120:3:dig" gives creature 3 a dig at frame 120 (or as soon as it
## can take it after); "@246:0:build" when creature 0 walks onto x = 246; "*" stands for every creature.

var _done := {}


func drive(e: MossEngine) -> void:
	var sol: Array = e.level.solution
	for i in sol.size():
		var when: String = sol[i][0]
		var who: String = sol[i][1]
		var skill: String = sol[i][2]
		for c in e.folk:
			if who != "*" and int(who) != c["id"]:
				continue
			var key := Vector2i(i, c["id"])
			if _done.has(key):
				continue
			var due := false
			if when.begins_with("@"):
				due = c["x"] == int(when.substr(1)) and c["state"] in ["walk", "fall"]
			else:
				due = e.frame >= int(when)
			if due and e.assign(c["id"], skill):
				_done[key] = true
