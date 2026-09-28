class_name TumbleGame
extends Node
## Runs Tumbletop: four rounds a level, the levels cycling through the four painting rules, faster each time.
## Three lives. Hops: Q / E / Z / C (up-left, up-right, down-left, down-right), or the arrows turned a quarter
## (up = up-right, right = down-right, down = down-left, left = up-left), or the numpad's 7 9 1 3, or the pad's stick
## diagonals. Holding a key keeps hopping. "--level=N" (user argument) starts at a level.

signal level_started(engine: TumbleEngine)
signal game_over()

const T = preload("res://games/tumbletop/engine/tumble_engine.gd")

var engine: TumbleEngine
var level := 0
var round := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: TumbleBot


func start(at := 0) -> void:
	level = maxi(0, at)
	round = 0
	over = false
	_load(3, 0)


func _load(lives: int, score: int) -> void:
	engine = TumbleEngine.new(level, round, lives, score)
	_bot = TumbleBot.new()
	level_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == T.Phase.OVER and engine.phase_t <= 0.0:
		over = true
		high = maxi(high, engine.score)
		game_over.emit()
		if demo:
			get_tree().create_timer(5.0).timeout.connect(func(): start(0))
		return
	if engine.phase == T.Phase.CLEARED and engine.phase_t <= 0.0:
		round += 1
		if round >= T.ROUNDS:
			round = 0
			level += 1
		_load(engine.lives, engine.score)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= T.TICK:
		_acc -= T.TICK
		if demo:
			_bot.drive(engine)
		else:
			engine.want = _held()
		engine.tick()


func _held() -> String:
	var k := func(keys: Array) -> bool:
		for kc in keys:
			if Input.is_physical_key_pressed(kc):
				return true
		return false
	if k.call([KEY_Q, KEY_KP_7, KEY_LEFT]): return "ul"
	if k.call([KEY_E, KEY_KP_9, KEY_UP]): return "ur"
	if k.call([KEY_Z, KEY_Y, KEY_KP_1, KEY_DOWN]): return "dl"
	if k.call([KEY_C, KEY_KP_3, KEY_RIGHT]): return "dr"
	var ax := Vector2(Input.get_joy_axis(0, JOY_AXIS_LEFT_X), Input.get_joy_axis(0, JOY_AXIS_LEFT_Y))
	if Input.is_joy_button_pressed(0, JOY_BUTTON_DPAD_LEFT): ax += Vector2(-1, -1)
	if Input.is_joy_button_pressed(0, JOY_BUTTON_DPAD_UP): ax += Vector2(1, -1)
	if Input.is_joy_button_pressed(0, JOY_BUTTON_DPAD_DOWN): ax += Vector2(-1, 1)
	if Input.is_joy_button_pressed(0, JOY_BUTTON_DPAD_RIGHT): ax += Vector2(1, 1)
	if ax.length() > 0.5:
		if ax.x < 0.0:
			return "ul" if ax.y < 0.0 else "dl"
		return "ur" if ax.y < 0.0 else "dr"
	return ""


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
