class_name DeepBot
extends RefCounted
## The Deep Breath autopilot (the demo) plays a cavern's route, steps written with the cavern:
##   go:X  walk to x = X       jump  jump straight up      jumpl / jumpr  jump left / right (the arc is fixed)
##   offl / offr  walk off the edge of the floor, left / right   wait:S  stand still
##   clear  wait until no guardian on this floor is near or coming
##   hop  wait for the guardian on this floor to come close, then jump over it (the way it comes from)
##   gleft:X / gright:X  wait until a patrolling guardian (on any floor) is left of X heading left / right of X heading right
## After dying it starts the cavern's route again.

var _step := 0
var _t := 0.0
var _jump_dir := 0.0


func drive(e: DeepEngine) -> void:
	e.move_x = 0.0
	if e.phase == DeepEngine.Phase.DYING or e.phase == DeepEngine.Phase.READY:
		if e.phase == DeepEngine.Phase.DYING:
			_step = 0
			_t = 0.0
		return
	if e.phase != DeepEngine.Phase.PLAY:
		return
	var h := e.hero
	var p: Vector2 = h["pos"]
	if h["state"] == "air":
		e.move_x = _jump_dir
		var r: Array[String] = e.level.route
		if _step < r.size() and r[_step] in ["offl", "offr"]:
			_step += 1  # off the edge: that step is done
		return
	_jump_dir = 0.0
	var route: Array[String] = e.level.route
	if _step >= route.size():
		return
	var cmd := route[_step]
	var op := cmd.get_slice(":", 0)
	var arg := float(cmd.get_slice(":", 1)) if cmd.contains(":") else 0.0
	match op:
		"go":
			var dx := arg - p.x
			if absf(dx) < 0.1:
				_step += 1
				return
			e.move_x = signf(dx)
		"jump", "jumpl", "jumpr":
			_jump_dir = {"jump": 0.0, "jumpl": -1.0, "jumpr": 1.0}[op]
			e.move_x = _jump_dir
			e.jump_pressed = true
			_step += 1
		"offl", "offr":
			# walk off the edge of this floor (the step ends once he is falling)
			e.move_x = -1.0 if op == "offl" else 1.0
			if _standing(e, p) == false:
				_step += 1
		"wait":
			_t += DeepEngine.TICK
			if _t >= arg:
				_t = 0.0
				_step += 1
		"clear":
			if _near_guard(e, p) == null:
				_step += 1
		"gleft", "gright":
			for g in e.guards:
				var gx: float = g["pos"].x
				if g["axis"] == "h" and ((op == "gleft" and gx < arg and g["dir"] < 0) or (op == "gright" and gx > arg and g["dir"] > 0)):
					_step += 1
					break
		"hop":
			var g = _near_guard(e, p, 2.4)
			if g != null:
				_jump_dir = signf(g["pos"].x - p.x)
				e.move_x = _jump_dir
				e.jump_pressed = true
				_step += 1


func _standing(e: DeepEngine, p: Vector2) -> bool:
	return e._standing_cell(p).x >= 0


## The guardian on this floor that is near, or coming this way (null if none).
func _near_guard(e: DeepEngine, p: Vector2, reach := 5.0):
	for g in e.guards:
		var gp: Vector2 = g["pos"]
		if g["axis"] == "v":
			# a guardian going up and down may be anywhere in the air a jump from here goes through:
			# clear only once its whole body is below his feet and it is still heading down
			if absf(gp.x - p.x) < 2.6 and not (gp.y - 1.6 > p.y + 0.2 and g["dir"] > 0):
				return g
			continue
		if absf(gp.y - p.y) > 1.6:
			continue
		var d := gp.x - p.x
		var coming: bool = g["axis"] == "h" and signf(d) != float(g["dir"]) and d != 0.0
		if absf(d) < reach and (coming or absf(d) < 2.2):
			return g
	return null
