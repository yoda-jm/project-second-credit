class_name FlowGame
extends Node
## Runs Brassflow: level after level (longer pipes, quicker glow, more blocked cells); a level that spills short costs
## one of three chances and is tried again on a new board. 60 Hz ticks. Arrows, W A S D or the stick move the cursor
## (held, it repeats); space, enter or the pad's A places the dispenser's front piece; F or the pad's Y sends the glow
## on quickly once you are done. The mouse works too: point at a cell, click to place. "--level=N" starts at a level.

signal level_started(engine: FlowEngine)
signal game_over()

const F = preload("res://games/brassflow/engine/flow_engine.gd")

var engine: FlowEngine
var level := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: FlowBot
var _tries := 0
var _repeat := 0.0
var _held := Vector2i.ZERO


func start(at := 0) -> void:
	level = maxi(0, at)
	over = false
	_tries = 0
	_load(0, 3)


func _load(score: int, chances: int) -> void:
	_tries += 1
	engine = FlowEngine.new(level, score, chances, _tries)
	_bot = FlowBot.new()
	level_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == F.Phase.OVER and engine.phase_t <= 0.0:
		over = true
		high = maxi(high, engine.score)
		game_over.emit()
		if demo:
			get_tree().create_timer(5.0).timeout.connect(func(): start(0))
		return
	if engine.phase == F.Phase.DONE and engine.phase_t <= 0.0:
		if engine.passed():
			level += 1
		_load(engine.score, engine.chances)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= F.TICK:
		_acc -= F.TICK
		if demo:
			_bot.drive(engine)
		else:
			_steer()
		engine.tick()


## The cursor moves a cell per press, and repeats while a direction is held.
func _steer() -> void:
	var d := Vector2i.ZERO
	var ax := Vector2(Input.get_joy_axis(0, JOY_AXIS_LEFT_X), Input.get_joy_axis(0, JOY_AXIS_LEFT_Y))
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A) or ax.x < -0.5: d.x = -1
	elif Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D) or ax.x > 0.5: d.x = 1
	elif Input.is_action_pressed("ui_up") or Input.is_physical_key_pressed(KEY_W) or ax.y < -0.5: d.y = -1
	elif Input.is_action_pressed("ui_down") or Input.is_physical_key_pressed(KEY_S) or ax.y > 0.5: d.y = 1
	if d != _held:
		_held = d
		_repeat = 0.3
		_nudge(d)
	elif d != Vector2i.ZERO:
		_repeat -= F.TICK
		if _repeat <= 0.0:
			_repeat = 0.09
			_nudge(d)


func _nudge(d: Vector2i) -> void:
	if d == Vector2i.ZERO:
		return
	var c := engine.cursor + d
	if FlowEngine.inside(c):
		engine.cursor = c


func _unhandled_input(event: InputEvent) -> void:
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start(0)
			get_viewport().set_input_as_handled()
		return
	if over and event.is_action_pressed("ui_accept"):
		start(0)
		return
	var place: bool = (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_SPACE, KEY_ENTER, KEY_KP_ENTER]) \
		or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_A)
	if place:
		engine.place_pressed = true
	var fast: bool = (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F) \
		or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_Y)
	if fast:
		engine.fast_pressed = true
	# the mouse: point at a cell, click to place
	var cam := get_viewport().get_camera_3d()
	if cam and (event is InputEventMouseMotion or (event is InputEventMouseButton and event.pressed)):
		var from := cam.project_ray_origin(event.position)
		var dir := cam.project_ray_normal(event.position)
		if absf(dir.y) > 0.001:
			var t := -from.y / dir.y
			var hit := from + dir * t
			var c := Vector2i(int(floor(hit.x)), int(floor(hit.z)))
			if FlowEngine.inside(c):
				engine.cursor = c
				if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
					engine.place_pressed = true
