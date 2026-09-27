class_name RelicGame
extends Node
## Runs Relic Run: level after level, six lives, 60 Hz ticks. Arrows walk and climb (Down crawls), Up or Z jumps,
## Space or X fires, C or Ctrl plants dynamite; on a gamepad, A jumps, X fires, B plants. The demo plays each
## level's route. "--level=N" (user argument) starts at a level.

signal level_started(engine: RelicEngine)
signal game_over()

const E = preload("res://games/relic/engine/relic_engine.gd")
const FILE := "res://games/relic/levels/temple.relic"

var engine: RelicEngine
var levels: Array[RelicLevel] = []
var index := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: RelicBot


func start(at := 0) -> void:
	levels = RelicLevel.parse_file(FileAccess.get_file_as_string(FILE))
	index = clampi(at, 0, levels.size() - 1)
	over = false
	_load(6, 0)


func _load(lives: int, score: int) -> void:
	var lv: RelicLevel = RelicLevel.parse_file(FileAccess.get_file_as_string(FILE))[index % levels.size()]
	engine = RelicEngine.new(lv, 1 + index, lives, score)
	_bot = RelicBot.new()
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
	var ay := Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
	var x := 0.0
	if Input.is_action_pressed("ui_left") or ax < -0.4: x -= 1.0
	if Input.is_action_pressed("ui_right") or ax > 0.4: x += 1.0
	engine.move_x = x
	engine.up = Input.is_action_pressed("ui_up") or ay < -0.5
	engine.down = Input.is_action_pressed("ui_down") or ay > 0.5


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
	if event is InputEventKey:
		match event.physical_keycode:
			KEY_Z: engine.jump_pressed = true
			KEY_UP:
				if not engine._on_ladder(engine.hero["pos"]):
					engine.jump_pressed = true
			KEY_SPACE, KEY_X: engine.fire_pressed = true
			KEY_C, KEY_CTRL: engine.plant_pressed = true
	elif event is InputEventJoypadButton:
		match event.button_index:
			JOY_BUTTON_A: engine.jump_pressed = true
			JOY_BUTTON_X: engine.fire_pressed = true
			JOY_BUTTON_B: engine.plant_pressed = true
