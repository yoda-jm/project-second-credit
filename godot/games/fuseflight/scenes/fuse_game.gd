class_name FuseGame
extends Node
## Runs Fuseflight: stage after stage (back to the first after the last, faster), three lives, 60 Hz ticks.
## Arrows (or A and D, or a gamepad) run; space, Z, up, W or the pad's A leaps (hold it to leap higher; hold it while
## falling to glide). "--level=N" (user argument) starts at a stage.

signal stage_started(engine: FuseEngine)
signal game_over()

const F = preload("res://games/fuseflight/engine/fuse_engine.gd")
const FILE := "res://games/fuseflight/stages/festival.fuse"

var engine: FuseEngine
var stages: Array[FuseStage] = []
var index := 0
var round := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: FuseBot
var _was_jump := false


func start(at := 0) -> void:
	stages = FuseStage.parse_file(FileAccess.get_file_as_string(FILE))
	index = clampi(at, 0, stages.size() - 1)
	round = 0
	over = false
	_load(3, 0)


func _load(lives: int, score: int) -> void:
	var st: FuseStage = FuseStage.parse_file(FileAccess.get_file_as_string(FILE))[index]
	st.speed += round * 0.5
	engine = FuseEngine.new(st, lives, score, 1 + index + round * 7)
	_bot = FuseBot.new()
	stage_started.emit(engine)


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
	if engine.phase == F.Phase.CLEARED and engine.phase_t <= 0.0:
		index += 1
		if index >= stages.size():
			index = 0
			round += 1
		_load(engine.lives, engine.score)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= F.TICK:
		_acc -= F.TICK
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
	var j := Input.is_physical_key_pressed(KEY_SPACE) or Input.is_physical_key_pressed(KEY_Z) or Input.is_physical_key_pressed(KEY_UP) \
		or Input.is_physical_key_pressed(KEY_W) or Input.is_joy_button_pressed(0, JOY_BUTTON_A)
	engine.jump_held = j
	engine.jump_pressed = j and not _was_jump
	_was_jump = j


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
