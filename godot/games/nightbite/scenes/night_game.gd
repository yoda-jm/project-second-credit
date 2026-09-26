class_name NightGame
extends Node
## Runs Nightbite: the mazes in turn, stage after stage faster, three lives (one more at 10,000), fixed 60 Hz ticks.
## Arrows, W A S D or a gamepad steer (a turn pressed early is kept until it opens). The demo lets the autopilot play.

signal stage_started(engine: NightEngine)
signal game_over()

const E = preload("res://games/nightbite/engine/night_engine.gd")
const FILE := "res://games/nightbite/mazes/night.maze"

var engine: NightEngine
var mazes: Array[NightMaze] = []
var stage := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: NightBot
var _seed := 1


func start(seed := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	mazes = NightMaze.parse_file(FileAccess.get_file_as_string(FILE))
	stage = 0
	over = false
	_new_stage(3, 0)


func _new_stage(lives: int, score: int) -> void:
	var m: NightMaze = NightMaze.parse_file(FileAccess.get_file_as_string(FILE))[stage % mazes.size()]
	engine = NightEngine.new(m, stage, _seed + stage * 17, lives, score)
	_bot = NightBot.new(_seed + stage)
	stage_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == E.Phase.DYING and engine.phase_t <= 0.0:
		if engine.lives <= 0:
			over = true
			high = maxi(high, engine.score)
			game_over.emit()
			if demo:
				get_tree().create_timer(5.0).timeout.connect(func(): start(_seed + 1))
			return
		engine.respawn()
	elif engine.phase == E.Phase.CLEARED and engine.phase_t <= 0.0:
		stage += 1
		_new_stage(engine.lives, engine.score)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= E.TICK:
		_acc -= E.TICK
		if demo:
			_bot.drive(engine)
		else:
			var d := _held()
			if d != Vector2i.ZERO:
				engine.want = d
		engine.tick()


func _held() -> Vector2i:
	var ax := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
	var ay := Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
	if Input.is_action_pressed("ui_up") or Input.is_physical_key_pressed(KEY_W) or ay < -0.5: return Vector2i(0, -1)
	if Input.is_action_pressed("ui_down") or Input.is_physical_key_pressed(KEY_S) or ay > 0.5: return Vector2i(0, 1)
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A) or ax < -0.5: return Vector2i(-1, 0)
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D) or ax > 0.5: return Vector2i(1, 0)
	return Vector2i.ZERO


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
