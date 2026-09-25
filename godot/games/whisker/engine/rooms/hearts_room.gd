class_name HeartsRoom
extends WhiskerRoom
## The serenade: after every third room the cat climbs a tower of drifting hearts to the lady cat waiting on the
## top one. Cupid's arrows fly across and knock the cat down (no life lost). Reach her before the time runs out.

const TOP_Y := 12.6
const ARROW_SPEED := 6.5
const ARROW_EVERY := Vector2(1.2, 2.2)

var hearts: Array[Dictionary] = []  ## the moving platforms: {rect, vel, kind, x0, amp, phase}
var arrows: Array[Dictionary] = []  ## {pos, dir}
var lady := Vector2(8.0, TOP_Y)
var _arrow_in := 2.0
var _t := 0.0


func setup(e: WhiskerEngine) -> void:
	bounds = Rect2(0, 0, 16, 14)
	super.setup(e)
	time_left = 40.0
	var ys := [1.9, 3.9, 5.9, 7.9, 9.9, 11.9]
	for i in ys.size():
		# neighbours sit about 3 m apart and drift in and out of reach (a 2 m climb carries about 2.4 m)
		var x0: float = [5.0, 7.8, 5.2, 8.2, 5.6, 8.0][i]
		var h := {"rect": Rect2(x0 - 0.9, ys[i] - 0.3, 1.8, 0.3), "vel": Vector2.ZERO, "kind": "heart",
			"x0": x0, "amp": 1.4 + 0.15 * i, "phase": i * 1.3, "speed": 0.8 + 0.08 * e.level}
		hearts.append(h)
		platforms.append(h)
	platforms.append({"rect": Rect2(6.6, TOP_Y - 0.4, 2.8, 0.4), "kind": "top"})
	entry = Vector2(1.5, 0.0)
	goal = 1


func tick(e: WhiskerEngine, dt: float) -> void:
	super.tick(e, dt)
	_t += dt
	for h in hearts:
		var r: Rect2 = h["rect"]
		var nx: float = h["x0"] + sin(_t * h["speed"] + h["phase"]) * h["amp"]
		h["vel"] = Vector2((nx - r.get_center().x) / dt, 0.0)
		r.position.x = nx - r.size.x * 0.5
		h["rect"] = r
	_arrow_in -= dt
	if _arrow_in <= 0.0:
		_arrow_in = e.rng.randf_range(ARROW_EVERY.x, ARROW_EVERY.y) / (1.0 + 0.1 * (e.level - 1))
		var dir := 1 if e.rng.randf() < 0.5 else -1
		var y := clampf(e.cat.pos.y + e.rng.randf_range(-0.5, 1.5), 1.0, TOP_Y - 1.0)
		arrows.append({"pos": Vector2(-1.0 if dir > 0 else bounds.end.x + 1.0, y), "dir": dir})
		e.event.emit("arrow", {"y": y})
	var i := 0
	while i < arrows.size():
		var a := arrows[i]
		a["pos"].x += a["dir"] * ARROW_SPEED * dt
		if e.cat.rect().grow(0.1).has_point(a["pos"]) and e.stunned <= 0.0:
			e.stunned = WhiskerEngine.STUN
			e.cat.vel = Vector2(a["dir"] * 2.5, -1.0)
			e.cat.drop_until = e.time + 0.4
			e.event.emit("shoe_hit", {"pos": a["pos"]})
			arrows.remove_at(i)
			continue
		if a["pos"].x < -2.0 or a["pos"].x > bounds.end.x + 2.0:
			arrows.remove_at(i)
			continue
		i += 1
	if e.cat.rect().grow(0.2).has_point(lady + Vector2(0, 0.3)) and status == 0:
		catch_one(e, "lady", lady, 0)
