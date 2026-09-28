class_name TumbleBot
extends RefCounted
## The Tumbletop autopilot (the demo): between hops it marks the cells the dangerous enemies hold or may hop to next,
## then takes the first hop of the cheapest safe path to a cube that still needs painting (a finished cube costs more
## when stepping on it would undo it). With the serpent close and a disc one hop away, it rides the disc.

const T = preload("res://games/tumbletop/engine/tumble_engine.gd")


func drive(e: TumbleEngine) -> void:
	e.want = ""
	if e.phase != T.Phase.PLAY:
		return
	var h := e.hero
	if h["state"] != "stand" or h["t"] < 1.0:
		return
	var at: Vector2i = h["to"]
	var danger := _danger(e)
	# the serpent close: a disc one hop away lures him off
	for en in e.enemies:
		if en["kind"] == "serpent" and T.cube3(en["to"]).distance_to(T.cube3(at)) < 2.6:
			for k in T.DIRS:
				if e.disc_at(at + T.DIRS[k]) >= 0:
					e.want = k
					return
	var best := _plan(e, at, danger)
	if best != "":
		e.want = best
		return
	# nowhere good: step to any safe neighbour if this cell is threatened
	if danger.has(at):
		for k in T.DIRS:
			var c: Vector2i = at + T.DIRS[k]
			if T.on_pyramid(c) and not danger.has(c):
				e.want = k
				return
		for k in T.DIRS:
			if e.disc_at(at + T.DIRS[k]) >= 0:
				e.want = k
				return


func _danger(e: TumbleEngine) -> Dictionary:
	var out := {}
	if e.frozen > 0.6:
		return out
	for en in e.enemies:
		if en["kind"] in ["green", "imp"] or en.has("fall_t"):
			continue
		out[en["to"]] = true
		if en.has("from_cell") and en["t"] < 1.0:
			out[en["from_cell"]] = true
		if en["kind"] == "serpent":
			for k in T.DIRS:
				out[en["to"] + T.DIRS[k]] = true
		elif en.get("wait", 0.0) < T.HOP + 0.25 or en.get("drop", 0.0) > 0.0:
			out[en["to"] + T.DIRS["dl"]] = true
			out[en["to"] + T.DIRS["dr"]] = true
	return out


## Dijkstra over the pyramid: the first hop towards the nearest unfinished cube (or "").
func _plan(e: TumbleEngine, at: Vector2i, danger: Dictionary) -> String:
	var dist := {at: 0.0}
	var first := {at: ""}
	var open: Array[Vector2i] = [at]
	var best_c := Vector2i(-1, -1)
	var best_d := INF
	while not open.is_empty():
		open.sort_custom(func(a, b): return dist[a] < dist[b])
		var c: Vector2i = open.pop_front()
		if c != at and not e.done(c) and dist[c] < best_d:
			best_d = dist[c]
			best_c = c
			break
		for k in T.DIRS:
			var n: Vector2i = c + T.DIRS[k]
			if not T.on_pyramid(n):
				continue
			# the next hop must be safe right now; further ones are only discouraged
			if c == at and danger.has(n):
				continue
			var cost := 1.0 + (3.0 if danger.has(n) else 0.0)
			if e.done(n) and e.rule["undo"]:
				cost += 4.0
			var nd: float = dist[c] + cost
			if nd < dist.get(n, INF):
				dist[n] = nd
				first[n] = k if c == at else first[c]
				if not open.has(n):
					open.append(n)
	return first.get(best_c, "")
