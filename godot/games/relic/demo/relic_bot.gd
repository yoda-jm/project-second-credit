class_name RelicBot
extends RefCounted
## The Relic Run autopilot (the demo) plays a level's route, a list of steps written with the level:
##   go:X  walk to x = X        crawl:X  crawl to x = X        up:Y / down:Y  climb a ladder to feet at y = Y
##   jump  jump (keeping the walk going)     shoot  fire once     plant  plant dynamite     wait:S  stand still
##   clear  wait until no dart is flying
## It also fires at any enemy ahead on its own level. After dying it starts the route again from the step that brought it into the screen it respawned in.

var _step := 0
var _t := 0.0
var _last_x := 0.0
var _screen_step := {}   ## screen -> the first step taken in it
var _jump_dir := 0.0
var _cool := 0.0


func drive(e: RelicEngine) -> void:
	e.move_x = 0.0
	e.up = false
	e.down = false
	if e.phase == RelicEngine.Phase.DYING:
		_step = _screen_step.get(e._screen_of(e.respawn), _step)
		_t = 0.0
		return
	if e.phase != RelicEngine.Phase.PLAY:
		return
	var route: Array[String] = e.level.route
	if _step >= route.size():
		return
	var s := e.screen
	if not _screen_step.has(s):
		_screen_step[s] = _step
	# a reflex: an enemy ahead on this level gets a bullet
	_cool -= RelicEngine.TICK
	if _cool <= 0.0 and e.bullets > 0 and e.hero["state"] in ["ground", "crawl"]:
		for en in e.enemies:
			var d: Vector2 = en["pos"] - e.hero["pos"]
			if en["alive"] and absf(d.y) < 0.8 and d.x * e.hero["facing"] > 0.0 and absf(d.x) < 8.0:
				e.fire_pressed = true
				_cool = 0.35
				break
	var cmd := route[_step]
	var op := cmd.get_slice(":", 0)
	var arg := float(cmd.get_slice(":", 1)) if cmd.contains(":") else 0.0
	var h := e.hero
	var p: Vector2 = h["pos"]
	match op:
		"go", "crawl":
			var dx := arg - p.x
			if absf(dx) < 0.12 and h["state"] != "air":
				_step += 1
				return
			e.move_x = signf(dx) * (1.0 if absf(dx) > 0.3 else 0.5)
			e.down = op == "crawl"
			if h["state"] == "air" and _jump_dir != 0.0:
				e.move_x = _jump_dir
		"jump":
			e.jump_pressed = true
			_jump_dir = float(h["facing"])
			_step += 1
		"shoot":
			e.fire_pressed = true
			_step += 1
		"plant":
			e.plant_pressed = true
			_step += 1
		"clear":
			# wait until no dart is in the air
			if e.darts.is_empty():
				_step += 1
		"wait":
			_t += RelicEngine.TICK
			if _t >= arg:
				_t = 0.0
				_step += 1
		"up", "down":
			var dy := arg - p.y
			if absf(dy) < 0.08 or (op == "up" and h["state"] == "ground" and p.y <= arg + 0.1 and _t > 0.2):
				_step += 1
				_t = 0.0
				return
			_t += RelicEngine.TICK
			e.up = op == "up"
			e.down = op == "down"
	if h["state"] != "air":
		_jump_dir = 0.0
