class_name BootsBot
extends RefCounted
## Demo autopilot for Muddy Boots: shoots the nearest enemy in sight, brings huts down with grenades or rockets,
## picks up crates when short of grenades, collects hostages and walks them to the tent, and otherwise heads for
## the nearest thing still to do.

const E = preload("res://games/boots/engine/boots_engine.gd")

var _replan := 0.0
var _throw_cd := 0.0


func drive(e: BootsEngine) -> void:
	e.firing = false
	var l := e.leader()
	if l.is_empty() or e.phase != E.Phase.PLAY:
		return
	var lp: Vector2 = l["pos"]
	_replan -= E.TICK
	_throw_cd -= E.TICK
	# 1. shoot what can see us
	var foe := _nearest(lp, e.enemies.filter(func(x): return x["alive"] and e.clear_line(lp, x["pos"])), E.BULLET_RANGE - 0.5)
	if not foe.is_empty():
		e.aim = foe["pos"]
		e.firing = true
	# 2. huts: a grenade or a rocket from a safe distance
	for h in e.huts:
		if not h["alive"]:
			continue
		var hc := Vector2(h["cell"]) + (Vector2(1, 1) if e.map.source == "text" else Vector2(0.5, 0.5))
		var d := lp.distance_to(hc)
		if _throw_cd <= 0.0 and d < E.GRENADE_RANGE - 0.5 and d > 2.8 and e.grenades > 0:
			e.throw_grenade(hc)
			_throw_cd = 1.5
		elif _throw_cd <= 0.0 and d < 9.0 and e.rockets > 0 and e.clear_line(lp, hc):
			e.fire_rocket(hc)
			_throw_cd = 1.5
	if _replan > 0.0 and not e.path.is_empty():
		return
	_replan = 1.0
	e.move_to(_goal(e, lp))


func _nearest(p: Vector2, list: Array, max_d := INF) -> Dictionary:
	var best := {}
	var bd := max_d
	for x in list:
		var d := p.distance_to(x["pos"])
		if d < bd:
			bd = d
			best = x
	return best


func _goal(e: BootsEngine, lp: Vector2) -> Vector2:
	var following := e.hostages.filter(func(h): return h["following"] and not h["rescued"])
	if not following.is_empty() and not e.tents.is_empty():
		return e.tents[0]
	var huts := e.huts.filter(func(h): return h["alive"])
	if not huts.is_empty() and e.grenades == 0 and e.rockets == 0 and not e.crates.is_empty():
		return _nearest(lp, e.crates)["pos"]
	var todo: Array = []
	for h in huts:
		var hc := Vector2(h["cell"]) + Vector2(1, 3.2)  # stand off in front of the door
		todo.append({"pos": hc})
	for x in e.enemies:
		if x["alive"]:
			todo.append({"pos": x["pos"]})
	for x in e.hostages:
		if not x["following"] and not x["rescued"]:
			todo.append({"pos": x["pos"]})
	var t := _nearest(lp, todo)
	if t.is_empty():
		return lp
	var target: Vector2 = t["pos"]
	# walk to a spot a few tiles short of an enemy, not onto it
	var d := lp.distance_to(target)
	if d > 5.0 and not e.hostages.any(func(x): return x["pos"] == target):
		target = lp + (target - lp).normalized() * (d - 4.0)
	var c := e.cell_of(target)
	var tries := 0
	while (e.blocked(c) or not e.map.inside(c)) and tries < 12:
		c += Vector2i(e.rng.randi_range(-1, 1), e.rng.randi_range(-1, 1))
		c = c.clamp(Vector2i.ZERO, Vector2i(e.map.w - 1, e.map.h - 1))
		tries += 1
	return Vector2(c) + Vector2(0.5, 0.5)
