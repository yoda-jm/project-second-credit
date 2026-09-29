class_name LinksGame
extends Node
## Runs Lantern Links: the seat setup (one to four players, each a person or the CPU), the round, and the controls.
## Aim: move the mouse, or left and right (shift: fine), or the left stick. Shoot: press the mouse, pull back and
## release (pull back to nothing to cancel); or hold space (or the pad's A) while the meter swings and release. Tab
## (or the pad's Y) holds the overview; the wheel zooms. Enter skips a fly-over or a scorecard. CPU players plan on a
## worker thread with the game's own physics. "--demo": the CPU plays (the captures); "--hole=N" starts at a hole;
## "--players=N" seats N people.

signal game_started(engine: LinksEngine)
signal setup_changed()

const E = preload("res://games/lanternlinks/engine/links_engine.gd")
const COURSE := "res://games/lanternlinks/courses/lantern_garden.links"
const TICK := 1.0 / 60.0
const LEAD := 2.2            ## a CPU strikes this long after it starts planning (so the plan is exact for gadgets)
const METER_T := 2.2         ## the swinging meter's period (s)
const PULL_PX := 260.0       ## a full-power pull with the mouse

var engine: LinksEngine
var holes: Array[LinksHole] = []
var seats: Array[Dictionary] = [{"name": "PLAYER 1", "cpu": false}, {"name": "CPU", "cpu": true}]
var setup := true
var demo := false
var demo_locked := false
var first_hole := 0
var aim_angle := 0.0
var aim_power := 0.0         ## the power being charged (0 when not charging)
var charging := false
var charge_by_mouse := false
var overview := false
var zoom := 1.0
var cpu_thinking := false
var best_total := 0
var _meter_t := 0.0
var _pull := 0.0
var _acc := 0.0
var _bot: LinksBot
var _task := -1
var _cpu_at := 0.0           ## the hole clock the CPU strikes at
var _cpu_ready := false
var _games := 0
var _cpu_turn := false
var _line := 0.0              ## the default aim of this turn (the CPU looks along it while it thinks)


func _ready() -> void:
	var text := FileAccess.get_file_as_string(COURSE)
	holes = LinksHole.parse_course(text)


func begin() -> void:
	setup = false
	_games += 1
	var who: Array[Dictionary] = []
	for s in seats:
		who.append(s.duplicate())
	engine = LinksEngine.new(holes, who, first_hole, 1000 + _games)
	engine.event.connect(_on_event)
	game_started.emit(engine)
	_on_event("hole", {"index": engine.hole_i})


func demo_seats() -> void:
	seats = [{"name": "ROSE", "cpu": true}, {"name": "BASIL", "cpu": true}]


func _on_event(kind: String, _d: Dictionary) -> void:
	match kind:
		"hole":
			_wait_task()
			_bot = LinksBot.new(engine.hole, 97 + engine.hole_i * 13 + _games)
		"aim":
			charging = false
			aim_power = 0.0
			_line = default_aim()
			aim_angle = _line
			_cpu_turn = demo or bool(engine.player()["cpu"])
			if _cpu_turn:
				_plan()
		"tee":
			aim_angle = default_aim()
		"final":
			var t := engine.total(0)
			if not engine.players[0]["cpu"] and (best_total == 0 or t < best_total):
				best_total = t
			if demo:
				get_tree().create_timer(9.0).timeout.connect(func():
					if demo:
						begin())


## Where a player starts aiming: towards the furthest point along the walking route to the cup that the ball can
## see in a straight line (the cup itself when in sight).
func default_aim() -> float:
	if engine == null or _bot == null:
		return 0.0
	var h := engine.hole
	var from := engine.ball.pos
	if _clear(h, from, h.cup):
		return (h.cup - from).angle()
	var best := INF
	var best_a := 0.0
	for k in 72:
		var a := TAU * k / 72.0
		var d := Vector2.from_angle(a)
		var p := from
		for s in 40:
			var q := p + d * 0.1
			if h.solid_at(q) or h.kind_at(q) in [LinksHole.WATER, LinksHole.CHASM]:
				break
			p = q
		var f := _bot.field(p)
		if f < best:
			best = f
			best_a = a
	return best_a


static func _clear(h: LinksHole, a: Vector2, b: Vector2) -> bool:
	var n := int(a.distance_to(b) / 0.08) + 1
	for s in n + 1:
		var p := a.lerp(b, float(s) / n)
		if h.solid_at(p) or h.kind_at(p) in [LinksHole.WATER, LinksHole.CHASM]:
			return false
	for g in h.gadgets:
		if g["type"] in ["bumper", "windmill", "spinner", "mover"]:
			var c: Vector2 = g.get("pos", g.get("hub", g.get("p0", Vector2.ZERO)))
			if Geometry2D.get_closest_point_to_segment(c, a, b).distance_to(c) < 0.3:
				return false
	return true


# --- the CPU ---

func _plan() -> void:
	_wait_task()
	_bot.skill = 0.45 if demo else 0.7
	_cpu_at = engine.clock + LEAD
	_cpu_ready = false
	cpu_thinking = true
	_bot.plan(engine.ball, _cpu_at)
	_task = WorkerThreadPool.add_task(_bot.think)


func _wait_task() -> void:
	if _task >= 0:
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -1


func _drive_cpu(delta: float) -> void:
	if not _cpu_ready:
		if _task >= 0 and WorkerThreadPool.is_task_completed(_task):
			_wait_task()
			_cpu_ready = true
			cpu_thinking = false
			if engine.clock > _cpu_at + TICK and engine.hole.moving():
				_plan()   # too late for the plan's moment: the gadgets have moved on
				return
		else:
			# lining up: look along the green while thinking
			aim_angle = lerp_angle(aim_angle, _line + sin(engine.clock * 1.3) * 0.15, 1.0 - exp(-delta * 1.5))
			return
	# turn to the planned line, charge, and strike on the planned tick
	aim_angle = lerp_angle(aim_angle, _bot.angle, 1.0 - exp(-delta * 7.0))
	var left := _cpu_at - engine.clock
	charging = left < 0.9
	aim_power = _bot.power * clampf(1.0 - left / 0.9, 0.0, 1.0) if charging else 0.0
	if engine.clock >= _cpu_at - TICK * 0.5:
		charging = false
		aim_power = 0.0
		engine.shoot(_bot.angle, _bot.power)


# --- the loop ---

func _process(delta: float) -> void:
	if engine == null or setup:
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= TICK:
		_acc -= TICK
		if engine.phase == LinksEngine.Phase.AIM:
			if _cpu_turn:
				_drive_cpu(TICK)
			else:
				_steer(TICK)
		engine.tick()


func _steer(delta: float) -> void:
	var turn := 0.0
	var fine := Input.is_physical_key_pressed(KEY_SHIFT)
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A):
		turn -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D):
		turn += 1.0
	var ax := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
	if absf(ax) > 0.15:
		turn += ax
	aim_angle += turn * delta * (0.22 if fine else 1.3)
	overview = Input.is_physical_key_pressed(KEY_TAB) or Input.is_joy_button_pressed(0, JOY_BUTTON_Y)
	var held := Input.is_physical_key_pressed(KEY_SPACE) or Input.is_joy_button_pressed(0, JOY_BUTTON_A)
	if charge_by_mouse:
		return
	if held:
		if not charging:
			charging = true
			_meter_t = 0.0
		_meter_t += delta
		aim_power = 0.5 - 0.5 * cos(TAU * _meter_t / METER_T)
	elif charging:
		_release()


func _release() -> void:
	var p := aim_power
	charging = false
	charge_by_mouse = false
	aim_power = 0.0
	if p > 0.03:
		engine.shoot(aim_angle, p)


func _unhandled_input(event: InputEvent) -> void:
	if setup:
		_setup_input(event)
		return
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() \
				and (event is InputEventKey or event is InputEventJoypadButton or event is InputEventMouseButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			_wait_task()
			seats = [{"name": "PLAYER 1", "cpu": false}, {"name": "CPU", "cpu": true}]
			setup = true
			setup_changed.emit()
			get_viewport().set_input_as_handled()
		return
	if engine.phase in [LinksEngine.Phase.INTRO, LinksEngine.Phase.CARD]:
		if event.is_action_pressed("ui_accept") or (event is InputEventMouseButton and event.pressed) \
				or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_A):
			engine.skip()
		return
	if engine.phase == LinksEngine.Phase.FINAL:
		if event.is_action_pressed("ui_accept"):
			setup = true
			setup_changed.emit()
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			zoom = clampf(zoom * 0.9, 0.55, 2.2)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			zoom = clampf(zoom * 1.1, 0.55, 2.2)
		elif mb.button_index == MOUSE_BUTTON_LEFT and engine.can_shoot() and not _cpu_turn:
			if mb.pressed:
				charging = true
				charge_by_mouse = true
				_pull = 0.0
				aim_power = 0.0
			elif charge_by_mouse:
				_release()
	elif event is InputEventMouseMotion and engine.can_shoot() and not _cpu_turn:
		var mm := event as InputEventMouseMotion
		if charge_by_mouse:
			_pull = maxf(0.0, _pull + mm.relative.y)
			aim_power = clampf(_pull / PULL_PX, 0.0, 1.0)
			aim_angle += mm.relative.x * 0.0012
		else:
			aim_angle += mm.relative.x * 0.004


# --- the seats ---

func _setup_input(event: InputEvent) -> void:
	var changed := false
	if event.is_action_pressed("ui_right") and seats.size() < 4:
		seats.append({"name": "PLAYER %d" % (seats.size() + 1), "cpu": false})
		changed = true
	elif event.is_action_pressed("ui_left") and seats.size() > 1:
		seats.pop_back()
		changed = true
	elif event is InputEventKey and event.pressed and not event.echo:
		var k := (event as InputEventKey).physical_keycode
		if k >= KEY_1 and k <= KEY_4 and k - KEY_1 < seats.size():
			var s: Dictionary = seats[k - KEY_1]
			s["cpu"] = not s["cpu"]
			s["name"] = "CPU" if s["cpu"] else "PLAYER %d" % (k - KEY_1 + 1)
			changed = true
	if event.is_action_pressed("ui_accept") or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_START):
		get_viewport().set_input_as_handled()
		begin()
		setup_changed.emit()
		return
	if changed:
		_name_cpus()
		setup_changed.emit()
		get_viewport().set_input_as_handled()


func _name_cpus() -> void:
	var names := ["ROSE", "BASIL", "IVY", "SAGE"]
	var k := 0
	for s in seats:
		if s["cpu"]:
			s["name"] = names[k % names.size()]
			k += 1


func _exit_tree() -> void:
	_wait_task()
