class_name InkGame
extends Node
## Runs Inkstorm: stage after stage (a new land each time, the storm faster, two storms from stage 3), three lives,
## fixed 60 Hz ticks. Arrows, W A S D or a gamepad move; hold space (or the pad's A) to draw fast, shift (or X) to
## draw slow for double points. The demo lets the autopilot play.

signal stage_started(engine: InkEngine)
signal game_over()

const E = preload("res://games/inkstorm/engine/ink_engine.gd")

var engine: InkEngine
var stage := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: InkBot
var _seed := 1


func start(seed := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	stage = 0
	over = false
	_new_stage(3, 0)


func _new_stage(lives: int, score: int) -> void:
	engine = InkEngine.new(stage, _seed + stage * 31, lives, score)
	_bot = InkBot.new(_seed + stage)
	stage_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == E.Phase.OVER:
		over = true
		high = maxi(high, engine.score)
		game_over.emit()
		if demo:
			get_tree().create_timer(5.0).timeout.connect(func(): start(_seed + 1))
		return
	if engine.phase == E.Phase.CLEARED and engine.phase_t <= 0.0:
		stage += 1
		_new_stage(engine.lives, engine.score)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= E.TICK:
		_acc -= E.TICK
		if demo:
			_bot.drive(engine)
		else:
			_steer()
		engine.tick()


func _steer() -> void:
	var ax := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
	var ay := Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
	var d := Vector2i.ZERO
	if Input.is_action_pressed("ui_up") or Input.is_physical_key_pressed(KEY_W) or ay < -0.5: d = Vector2i(0, -1)
	elif Input.is_action_pressed("ui_down") or Input.is_physical_key_pressed(KEY_S) or ay > 0.5: d = Vector2i(0, 1)
	elif Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A) or ax < -0.5: d = Vector2i(-1, 0)
	elif Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D) or ax > 0.5: d = Vector2i(1, 0)
	engine.want = d
	engine.draw_fast = Input.is_physical_key_pressed(KEY_SPACE) or Input.is_joy_button_pressed(0, JOY_BUTTON_A)
	engine.draw_slow = Input.is_physical_key_pressed(KEY_SHIFT) or Input.is_joy_button_pressed(0, JOY_BUTTON_X)


func _unhandled_input(event: InputEvent) -> void:
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start()
			get_viewport().set_input_as_handled()
		return
	if over and event.is_action_pressed("ui_accept"):
		start()
