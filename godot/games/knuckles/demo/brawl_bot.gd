class_name BrawlBot
extends RefCounted
## Demo autopilot for Neon Knuckles: walks right when the street is clear, lines up with the nearest enemy in
## depth, throws combos and jump kicks, grabs staggered enemies and knees them, picks weapons up on the way.

const B = preload("res://games/knuckles/engine/brawl_engine.gd")

var _cool := 0
var _rng := RandomNumberGenerator.new()


func _init(seed := 3) -> void:
	_rng.seed = seed


func drive(e: BrawlEngine, player: int) -> void:
	var ps := e.players()
	if player >= ps.size():
		return
	var p: Dictionary = ps[player]
	_cool -= 1
	var dir := Vector2.ZERO
	var attack := false
	var jump := false
	var pick := false
	if not p["alive"]:
		e.set_input(player, dir, false, false)
		return
	var target := {}
	var best := INF
	for en in e.enemies():
		var d: float = Vector2(en["pos"].x, en["pos"].z).distance_to(Vector2(p["pos"].x, p["pos"].z))
		if d < best and en["state"] != B.S.DOWN:
			best = d
			target = en
	if p["state"] == B.S.GRABBING:
		attack = _cool <= 0
		if attack:
			_cool = 18
	elif target.is_empty():
		dir = Vector2(1, -p["pos"].z * 0.5)  # nobody around: move on
		var it := e._item_near(p)
		if it >= 0 and p["weapon"] == "":
			pick = true
	else:
		var dx: float = target["pos"].x - p["pos"].x
		var dz: float = target["pos"].z - p["pos"].z
		var side := signf(dx) if dx != 0.0 else 1.0
		if absf(dz) > 0.25:
			dir.y = signf(dz)
		if absf(dx) > 1.0:
			dir.x = side
		elif absf(dx) < 0.5:
			dir.x = -side * 0.5  # a step back to make room
		if absf(dz) < 0.35 and absf(dx) < 1.2 and _cool <= 0:
			if target["state"] == B.S.HITSTUN and p["weapon"] == "":
				dir.x = side  # walk in and grab
			attack = true
			_cool = 14 + _rng.randi_range(0, 6)
		elif absf(dz) < 0.3 and absf(dx) < 2.6 and absf(dx) > 1.6 and _cool <= 0 and _rng.randf() < 0.05:
			jump = true
			dir.x = side
			_cool = 30
		elif p["state"] == B.S.JUMP and absf(dx) < 1.8:
			attack = true
	e.set_input(player, dir, attack, jump, pick)
