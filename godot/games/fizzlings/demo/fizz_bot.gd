class_name FizzBot
extends RefCounted
## The Fizzlings autopilot (the demo, one per hero). It blows at any toy in front of it on its own level, turns to
## face a toy closing in, goes for trapped bubbles to pop them (jumping up into high ones), picks up treats, and
## otherwise heads for the nearest toy, jumping up through the platforms when the toy is above.

var p := 0
var _rng := RandomNumberGenerator.new()
var _jump_t := 0.0
var _wander := 0.0
var _dir := 1.0


func _init(player := 0, seed_ := 1) -> void:
	p = player
	_rng.seed = seed_ + player * 101


func drive(e: FizzEngine) -> void:
	var h: Dictionary = e.heroes[p]
	h["want_x"] = 0.0
	h["jump"] = false
	h["blow"] = false
	if e.phase != FizzEngine.Phase.PLAY and e.phase != FizzEngine.Phase.CLEARED or not h["alive"]:
		return
	var hp: Vector2 = h["pos"]
	_jump_t -= FizzEngine.TICK
	# a toy in front on this level: blow
	for t in e.toys:
		var d: Vector2 = t["pos"] - hp
		if absf(d.y) < 1.4 and absf(d.x) < 8.0:
			if signf(d.x) == h["facing"] or absf(d.x) < 3.0:
				if signf(d.x) != h["facing"]:
					h["want_x"] = signf(d.x) * 0.1  # turn round
				h["blow"] = true
				if absf(d.x) < 2.2:
					h["want_x"] = -signf(d.x)  # too close: back off after blowing
				return
	# what to go for
	var goal := Vector2(-1, -1)
	var bd := INF
	for b in e.bubbles:
		if not b["trapped"].is_empty() and b["age"] > b["fly"]:
			var dd := (b["pos"] as Vector2).distance_to(hp) * 0.8
			if dd < bd:
				bd = dd
				goal = b["pos"] + Vector2(0, 0.9)
	for tr in e.treats:
		var dd := (tr["pos"] as Vector2).distance_to(hp) * 1.2
		if dd < bd:
			bd = dd
			goal = tr["pos"]
	if goal.x < 0.0:
		for t in e.toys:
			var dd := (t["pos"] as Vector2).distance_to(hp)
			if dd < bd:
				bd = dd
				goal = t["pos"]
	if goal.x < 0.0:
		_wander -= FizzEngine.TICK
		if _wander <= 0.0:
			_wander = _rng.randf_range(1.0, 2.5)
			_dir = [-1.0, 1.0][_rng.randi_range(0, 1)]
		h["want_x"] = _dir
		return
	var dx := goal.x - hp.x
	var dy := goal.y - hp.y
	h["want_x"] = signf(dx) if absf(dx) > 0.4 else 0.0
	# up: jump (the platforms let it through from below)
	if dy < -1.5 and h["ground"] and _jump_t <= 0.0 and absf(dx) < 6.0:
		h["jump"] = true
		_jump_t = 0.5
	# a trapped bubble just above: jump into it
	if dy < -0.5 and dy > -4.0 and absf(dx) < 1.2 and h["ground"]:
		h["jump"] = true
	# down: walk off the edge towards it (nothing to do: gravity)
	# stuck against a wall under the goal: try the other way now and then
	if absf(h["vel"].x) < 0.1 and h["want_x"] != 0.0 and h["ground"] and _rng.randf() < 0.02:
		h["jump"] = true
