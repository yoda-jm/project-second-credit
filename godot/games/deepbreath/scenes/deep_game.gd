class_name DeepGame
extends Node
## Runs Deep Breath: cavern after cavern, three lives, 60 Hz ticks. Arrows (or A and D, or a gamepad) walk; space,
## Z, up or the pad's A jumps. The demo plays each cavern's route. "--level=N" (user argument) starts at a cavern.

signal level_started(engine: DeepEngine)
signal game_over()

const E = preload("res://games/deepbreath/engine/deep_engine.gd")
const FILE := "res://games/deepbreath/levels/caverns.deep"

var engine: DeepEngine
var levels: Array[DeepLevel] = []
var index := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: DeepBot


func start(at := 0) -> void:
	levels = DeepLevel.parse_file(FileAccess.get_file_as_string(FILE))
	index = clampi(at, 0, levels.size() - 1)
	over = false
	_load(3, 0)


func _load(lives: int, score: int) -> void:
	var lv: DeepLevel = DeepLevel.parse_file(FileAccess.get_file_as_string(FILE))[index % levels.size()]
	engine = DeepEngine.new(lv, lives, score)
	_bot = DeepBot.new()
	level_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == E.Phase.OVER and engine.phase_t <= 0.0:
		over = true
		high = maxi(high, engine.score)
		game_over.emit()
		if demo:
			get_tree().create_timer(5.0).timeout.connect(func(): start(0))
		return
	if engine.phase == E.Phase.CLEARED and engine.phase_t <= 0.0:
		index += 1
		_load(engine.lives, engine.score)
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
	var x := 0.0
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A) or ax < -0.4: x -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D) or ax > 0.4: x += 1.0
	engine.move_x = x


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
	if over:
		if event.is_action_pressed("ui_accept"):
			start(0)
		return
	if not event.is_pressed() or event.is_echo():
		return
	if (event is InputEventKey and event.physical_keycode in [KEY_SPACE, KEY_Z, KEY_UP, KEY_W]) \
			or (event is InputEventJoypadButton and event.button_index == JOY_BUTTON_A):
		engine.jump_pressed = true
