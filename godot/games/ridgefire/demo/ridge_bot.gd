class_name RidgeBot
extends RefCounted
## The CPU gunner. It picks a target (the weakest tank in reach, else the nearest), then searches angles and powers
## by flying test shells through the real wind and ground (the engine's own step) and keeps the one that lands
## nearest; a skill scatters the final aim a little. It chooses a weapon by what it owns and the target (the nuke for a
## cluster, the roller when the target sits in a hollow below, heavy shells otherwise), and buys between rounds.

const R = preload("res://games/ridgefire/engine/ridge_engine.gd")

var angle := 45.0
var power := 60.0
var weapon := "shell"
var skill := 0.35
var plan_from := Vector2.ZERO   ## (angle, power) the tank had when the plan began
var rng := RandomNumberGenerator.new()


func _init(seed_ := 1) -> void:
	rng.seed = seed_


func plan(e: RidgeEngine) -> void:
	var me := e.current()
	var target := _target(e, me)
	if target.is_empty():
		angle = me["angle"]
		power = me["power"]
		return
	var aim := Vector2(target["x"], target["y"] + 0.6)
	var best := INF
	var right: bool = aim.x > me["x"]
	var a_lo := 20.0 if right else 100.0
	var a_hi := 80.0 if right else 160.0
	var a := a_lo
	while a <= a_hi:
		var p := 20.0
		while p <= 100.0:
			var d := _miss(e, me, a, p, aim)
			if d < best:
				best = d
				angle = a
				power = p
			p += 2.5
		a += 4.0
	# refine around the best
	var a0 := angle
	var p0 := power
	for da in [-2.0, -1.0, 0.0, 1.0, 2.0]:
		for dp in [-1.2, -0.6, 0.0, 0.6, 1.2]:
			var d := _miss(e, me, a0 + da, clampf(p0 + dp, 5.0, 100.0), aim)
			if d < best:
				best = d
				angle = a0 + da
				power = clampf(p0 + dp, 5.0, 100.0)
	angle += rng.randfn(0.0, 2.2 * skill)
	power = clampf(power + rng.randfn(0.0, 3.0 * skill), 5.0, 100.0)
	weapon = _weapon(e, me, target)


func _target(e: RidgeEngine, me: Dictionary) -> Dictionary:
	var best := {}
	var bs := INF
	for q in e.players:
		if not q["alive"] or q["i"] == me["i"]:
			continue
		var s: float = absf(q["x"] - me["x"]) * 0.6 + q["hp"]
		if s < bs:
			bs = s
			best = q
	return best


## How far from the aim point a shell with this angle and power lands (or passes nearest, for a hit on the way).
func _miss(e: RidgeEngine, me: Dictionary, a: float, p: float, aim: Vector2) -> float:
	var r := deg_to_rad(a)
	var s := {"pos": RidgeEngine.muzzle_at(me["x"], me["y"], a), "vel": Vector2(cos(r), sin(r)) * p / 100.0 * R.MAX_SPEED,
		"t": 0.0}
	var nearest := INF
	for k in 900:
		var hit := e.step_shot(s, false)
		var d := (s["pos"] as Vector2).distance_to(aim)
		nearest = minf(nearest, d)
		if hit != "":
			if hit == "out":
				return 999.0
			# landing near the shooter itself is a bad idea
			if (s["pos"] as Vector2).distance_to(Vector2(me["x"], me["y"])) < 6.0:
				return 500.0
			return minf(d, nearest + 0.5) if nearest < R.TANK_R else d
	return 999.0


func _weapon(e: RidgeEngine, me: Dictionary, target: Dictionary) -> String:
	var owned := e.owned(me["i"])
	var near := 0
	for q in e.players:
		if q["alive"] and q["i"] != me["i"] and absf(q["x"] - target["x"]) < 12.0:
			near += 1
	if owned.has("nuke") and (near >= 2 or target["hp"] > 70.0) and absf(target["x"] - me["x"]) > 20.0:
		return "nuke"
	if owned.has("mirv") and rng.randf() < 0.5:
		return "mirv"
	if owned.has("heavy"):
		return "heavy"
	if owned.has("roller") and target["y"] < me["y"] - 3.0:
		return "roller"
	return "shell"


## Between rounds: heavy shells first, then a shield, then the big things.
static func shop(e: RidgeEngine, i: int) -> void:
	var p := e.players[i]
	for item in ["heavy", "shield", "mirv", "heavy", "nuke", "roller"]:
		if p["money"] >= 900 or item == "heavy":
			e.buy(i, item)
