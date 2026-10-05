class_name TunnelGame
extends Node
## Runs Tunnel Pop: level after level (more creatures, more drakes, quicker), the score and lives carried on. 60 Hz
## ticks. Arrows, W A S D, the d-pad or the stick move (the last direction pressed wins, as on a four-way stick);
## space, Z or the pad's A works the pump (tap it, or hold it to keep pumping). "--level=N" starts at a level.

signal level_started(engine: DigEngine)
signal game_over()

const D = preload("res://games/tunnelpop/engine/pop_dig_engine.gd")

var engine: DigEngine
var level := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: DigBot
var _games := 0
var _held: Array[Vector2i] = []      ## directions held, the latest last
var _pump_t := 0.0


func start(at := 0) -> void:
	_games += 1
	level = maxi(0, at)
	over = false
	_load(0, 3)


func _load(score: int, lives: int) -> void:
	engine = DigEngine.new(level, score, lives, _games * 13 + 1)
	_bot = DigBot.new()
	level_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == D.Phase.OVER and engine.phase_t <= 0.0:
		over = true
		high = maxi(high, engine.score)
		game_over.emit()
		if demo:
			get_tree().create_timer(5.0).timeout.connect(func(): start(0))
		return
	if engine.phase == D.Phase.CLEARED and engine.phase_t <= 0.0:
		level += 1
		_load(engine.score, engine.lives)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= D.TICK:
		_acc -= D.TICK
		if demo:
			_bot.drive(engine)
		else:
			_steer()
		engine.tick()


func _steer() -> void:
	var keys := {Vector2i(1, 0): [KEY_RIGHT, KEY_D], Vector2i(-1, 0): [KEY_LEFT, KEY_A], Vector2i(0, -1): [KEY_UP, KEY_W], Vector2i(0, 1): [KEY_DOWN, KEY_S]}
	var pads := {Vector2i(1, 0): JOY_BUTTON_DPAD_RIGHT, Vector2i(-1, 0): JOY_BUTTON_DPAD_LEFT, Vector2i(0, -1): JOY_BUTTON_DPAD_UP, Vector2i(0, 1): JOY_BUTTON_DPAD_DOWN}
	var ax := Vector2(Input.get_joy_axis(0, JOY_AXIS_LEFT_X), Input.get_joy_axis(0, JOY_AXIS_LEFT_Y))
	for d in keys:
		var on := false
		for k in keys[d]:
			on = on or Input.is_physical_key_pressed(k)
		on = on or Input.is_joy_button_pressed(0, pads[d])
		if ax.length() > 0.5 and Vector2i(roundi(ax.normalized().x), roundi(ax.normalized().y)) == d:
			on = true
		if on and not _held.has(d):
			_held.append(d)
		elif not on and _held.has(d):
			_held.erase(d)
	engine.want = _held.back() if not _held.is_empty() else Vector2i.ZERO
	var pump := Input.is_physical_key_pressed(KEY_SPACE) or Input.is_physical_key_pressed(KEY_Z) or Input.is_joy_button_pressed(0, JOY_BUTTON_A)
	if pump:
		_pump_t -= D.TICK
		if _pump_t <= 0.0:
			engine.pump_pressed = true
			_pump_t = 0.22
	else:
		_pump_t = 0.0
	engine.pump_held = pump


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
