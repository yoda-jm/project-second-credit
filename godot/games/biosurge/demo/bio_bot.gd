class_name BioBot
extends RefCounted
## The Biosurge autopilot (the demo). It fires all the time and, each moment, tries nine ways to steer (the eight
## directions and staying put), predicting over half a second where the enemy shots, creatures and walls will be; it
## takes the safest way that also brings it under the next enemy ahead (or a credit close by), keeping low on the screen.

const B = preload("res://games/biosurge/engine/bio_engine.gd")
const LOOK := 0.5

var _t := 0


func drive(e: BioEngine) -> void:
	e.firing = e.phase in [B.Phase.PLAY, B.Phase.BOSS]
	if not e.firing:
		e.input = Vector2.ZERO
		return
	_t -= 1
	if _t > 0:
		return
	_t = 3
	var p: Vector2 = e.ship["pos"]
	var goal := _goal(e, p)
	var best := Vector2.ZERO
	var bs := -INF
	for k in 9:
		var dir := Vector2.ZERO if k == 8 else Vector2.from_angle(k * TAU / 8.0)
		var s := _score(e, p, dir, goal)
		if s > bs:
			bs = s
			best = dir
	e.input = best


func _goal(e: BioEngine, p: Vector2) -> Vector2:
	var low := e.scroll + 3.0
	var tx := p.x
	var bd := INF
	for f in e.foes:
		if f["dead"]:
			continue
		var fp: Vector2 = f["pos"]
		if fp.y > p.y + 1.0 and fp.y < e.scroll + B.SCREEN:
			var d := absf(fp.x - p.x) + (fp.y - p.y) * 0.3
			if d < bd:
				bd = d
				tx = fp.x
	if not e.boss.is_empty():
		tx = e.boss["core"].x
	for dr in e.drops:
		if (dr["pos"] as Vector2).distance_to(p) < 4.0:
			return dr["pos"]
	return Vector2(tx, low)


func _score(e: BioEngine, p: Vector2, dir: Vector2, goal: Vector2) -> float:
	var sp: float = B.SPEED * (1.0 + 0.12 * e.loadout["speed"])
	var danger := 0.0
	for step in 5:
		var t := LOOK * (step + 1) / 5.0
		var q := p + dir * sp * t
		q.y = clampf(q.y, e.scroll + t * B.SCROLL + 0.8, e.scroll + B.SCREEN - 2.0)
		q.x = clampf(q.x, 0.6, B.W - 0.6)
		if e.wall_hit(q, B.R + 0.35):
			danger += 6.0
		for b in e.bullets:
			var bp: Vector2 = b["pos"] + b["vel"] * t
			var d := bp.distance_to(q)
			if d < 1.4:
				danger += (1.4 - d) * 5.0
		for f in e.foes:
			if f["dead"]:
				continue
			var fp: Vector2 = f["pos"] + (f["vel"] as Vector2) * t
			var d := fp.distance_to(q)
			var rr: float = B.RADIUS[f["kind"]] + 1.0
			if d < rr:
				danger += (rr - d) * 4.0
	var end := p + dir * sp * LOOK
	return -danger * 3.0 - end.distance_to(goal) * 0.6
