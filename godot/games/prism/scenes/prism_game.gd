class_name PrismGame
extends Node
## Runs Prism Breaker: the walls in turn, three lives, fixed 120 Hz sub-steps. The mouse, the arrows, A and D or a
## gamepad move the paddle; space, a click or the pad's A button launches the ball and fires the laser. The demo
## lets the autopilot play. "--walls=<file>" (user argument) plays a wall file of the player's own instead of ours:
## our format or an LBreakout2 level set, read locally.

signal stage_started(engine: PrismEngine)
signal game_over()

const E = preload("res://games/prism/engine/prism_engine.gd")
const FILE := "res://games/prism/levels/spectrum.wall"

var engine: PrismEngine
var levels: Array[PrismLevel] = []
var stage := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var wait := 0.0             ## seconds before a lost ball comes back or the next wall starts
var pick_x: Callable        ## screen position -> field x (set by the view)
var _acc := 0.0
var _bot: PrismBot
var _seed := 1
var _mouse := false


func start(seed := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	levels = PrismLevel.parse_file(FileAccess.get_file_as_string(_wall_file()))
	if levels.is_empty():
		levels = PrismLevel.parse_file(FileAccess.get_file_as_string(FILE))
	stage = 0
	over = false
	_new_stage(3, 0)


func _wall_file() -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--walls=") and FileAccess.file_exists(a.substr(8)):
			return a.substr(8)
	return FILE


func _new_stage(lives: int, score: int) -> void:
	engine = PrismEngine.new(levels[stage % levels.size()], stage, _seed + stage * 17, lives, score)
	_bot = PrismBot.new(_seed + stage)
	wait = 0.0
	stage_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	match engine.phase:
		E.Phase.LOST:
			wait += delta
			if wait > 1.6:
				wait = 0.0
				engine.respawn()
		E.Phase.CLEARED:
			wait += delta
			if wait > 3.0:
				stage += 1
				_new_stage(engine.lives, engine.score)
			return
		E.Phase.OVER:
			over = true
			high = maxi(high, engine.score)
			game_over.emit()
			if demo:
				get_tree().create_timer(5.0).timeout.connect(func(): start(_seed + 1))
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
	var d := 0.0
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A): d -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D): d += 1.0
	if absf(ax) > 0.2: d = ax
	if d != 0.0:
		_mouse = false
		# past the right edge counts too: that is how the paddle leaves through an open break door
		engine.target_x = clampf(engine.paddle_x + d * 14.0 * E.TICK, 0.0, E.W + 1.0)
	elif not _mouse:
		engine.target_x = engine.paddle_x
	if Input.is_physical_key_pressed(KEY_SPACE) or Input.is_joy_button_pressed(0, JOY_BUTTON_A):
		engine.fire()


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
	if over:
		if event.is_action_pressed("ui_accept"):
			start()
		return
	if event is InputEventMouseMotion and pick_x.is_valid():
		_mouse = true
		engine.target_x = pick_x.call(event.position)
	var go: bool = (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_SPACE) \
		or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT) \
		or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_A)
	if go:
		engine.launch()
		engine.fire()
