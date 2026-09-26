class_name IngotGame
extends Node
## Runs Ingot Run: a set of levels in order, five lives, the score across levels, fixed 60 Hz ticks. Keys: arrows
## (or W A S D by position) to run, climb and hang; Z / Q or ctrl-left to dig left, X / E or ctrl-right to dig right
## (gamepad: d-pad or stick, X and B). The demo lets the autopilot play; a key takes over.

signal level_started(engine: IngotEngine)
signal game_over(won: bool)

const E = preload("res://games/ingot/engine/ingot_engine.gd")
const SET := "res://games/ingot/levels/deep-seam.lvl"
const LIVES := 5

var engine: IngotEngine
var levels: Array[IngotLevel] = []
var level := 0
var lives := LIVES
var score := 0
var demo := false
var demo_locked := false
var end_t := -1.0
var over := false
var _acc := 0.0
var _bot: IngotBot
var _seed := 1


func start(seed := -1, first := 0) -> void:
	_seed = seed if seed >= 0 else randi()
	levels = IngotLevel.parse_file(FileAccess.get_file_as_string(SET))
	level = clampi(first, 0, levels.size() - 1)
	lives = LIVES
	score = 0
	over = false
	_start_level()


func _start_level() -> void:
	var lv: IngotLevel = IngotLevel.parse_file(FileAccess.get_file_as_string(SET))[level]
	engine = IngotEngine.new(lv, _seed + level * 31 + lives)
	engine.score = score
	_bot = IngotBot.new(_seed + level)
	end_t = -1.0
	level_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase != E.Phase.PLAY:
		if end_t < 0.0:
			end_t = 0.0
		end_t += delta
		if end_t > 3.0:
			score = engine.score
			if engine.phase == E.Phase.CLEARED:
				level += 1
				if level >= levels.size():
					over = true
					game_over.emit(true)
					if demo:
						get_tree().create_timer(6.0).timeout.connect(func(): start(_seed + 1))
					return
			else:
				lives -= 1
				if lives <= 0:
					over = true
					game_over.emit(false)
					if demo:
						get_tree().create_timer(6.0).timeout.connect(func(): start(_seed + 1))
					return
			_start_level()
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= E.TICK:
		_acc -= E.TICK
		if demo:
			_bot.drive(engine)
		else:
			_read_input()
		engine.tick()


func _read_input() -> void:
	var ax := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
	var ay := Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
	var up := Input.is_action_pressed("ui_up") or Input.is_physical_key_pressed(KEY_W) or ay < -0.5
	var down := Input.is_action_pressed("ui_down") or Input.is_physical_key_pressed(KEY_S) or ay > 0.5
	var left := Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A) or ax < -0.5
	var right := Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D) or ax > 0.5
	var d := Vector2i.ZERO
	if left != right:
		d.x = -1 if left else 1
	elif up != down:
		d.y = -1 if up else 1
	engine.input = d


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
		return
	if not event.is_pressed() or event.is_echo():
		return
	var left := false
	var right := false
	if event is InputEventKey:
		match event.physical_keycode:
			KEY_Z, KEY_Q, KEY_COMMA: left = true
			KEY_X, KEY_E, KEY_PERIOD: right = true
	elif event is InputEventJoypadButton:
		left = event.button_index == JOY_BUTTON_X or event.button_index == JOY_BUTTON_LEFT_SHOULDER
		right = event.button_index == JOY_BUTTON_B or event.button_index == JOY_BUTTON_RIGHT_SHOULDER
	if left:
		engine.dig_left = true
	elif right:
		engine.dig_right = true
