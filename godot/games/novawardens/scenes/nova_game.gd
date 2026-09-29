class_name NovaGame
extends Node
## Runs Nova Wardens: wave after wave (the engine carries on by itself), three lives, 60 Hz ticks. Arrows (or A and
## D, or a gamepad) move the cannon; space, Z, up or the pad's A fires (held, it fires again as soon as the shot is
## free). "--level=N" (user argument) starts at a wave.

signal game_started(engine: NovaEngine)
signal game_over()

const N = preload("res://games/novawardens/engine/nova_engine.gd")

var engine: NovaEngine
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: NovaBot
var _games := 0


func start(at := 0) -> void:
	over = false
	_games += 1
	engine = NovaEngine.new(maxi(0, at), 3, 0, _games)
	_bot = NovaBot.new()
	game_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == N.Phase.OVER and engine.phase_t <= 0.0:
		over = true
		high = maxi(high, engine.score)
		game_over.emit()
		if demo:
			get_tree().create_timer(5.0).timeout.connect(func(): start(0))
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= N.TICK:
		_acc -= N.TICK
		if demo:
			_bot.drive(engine)
		else:
			_steer()
		engine.tick()


func _steer() -> void:
	var ax := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
	var x := 0.0
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A) or ax < -0.4: x -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D) or ax > 0.4: x += 1.0
	engine.move_x = x
	engine.fire_pressed = Input.is_physical_key_pressed(KEY_SPACE) or Input.is_physical_key_pressed(KEY_Z) \
		or Input.is_physical_key_pressed(KEY_UP) or Input.is_physical_key_pressed(KEY_W) or Input.is_joy_button_pressed(0, JOY_BUTTON_A)


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
